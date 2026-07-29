import re
from typing import Any, Dict, List, Optional

import pdfplumber


def parse_morgan_stanley(pdf: pdfplumber.PDF) -> Dict[str, Any]:
    text = _extract_full_text(pdf)
    tables = _extract_all_tables(pdf)

    result: Dict[str, Any] = {
        "account_number": _extract_account_number(text),
        "rsu_outstanding": _extract_rsu_outstanding(text, tables),
        "rsu_vested_during_year": _extract_rsu_vested(text, tables),
        "long_share_holdings": _extract_share_holdings(text, tables),
        "dividends": _extract_dividends(text, tables),
        "closing_value": _extract_closing_value(text, tables),
        "exchange_rate": _extract_exchange_rate(text),
    }

    return result


def _extract_full_text(pdf: pdfplumber.PDF) -> str:
    parts = []
    for page in pdf.pages:
        try:
            text = page.extract_text()
            if text:
                parts.append(text)
        except Exception:
            continue
    return "\n".join(parts)


def _extract_all_tables(pdf: pdfplumber.PDF) -> list:
    all_tables = []
    for page in pdf.pages:
        try:
            page_tables = page.extract_tables()
            if page_tables:
                all_tables.extend(page_tables)
        except Exception:
            continue
    return all_tables


def _extract_account_number(text: str) -> Optional[str]:
    patterns = [
        r"[Aa]ccount\s*(?:[Nn]o\.?|[Nn]umber)[:\s]*([A-Z0-9\-]+)",
        r"[Aa]cct\.?\s*#?\s*[:\s]*([A-Z0-9\-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return None


def _extract_rsu_outstanding(text: str, tables: list) -> Optional[int]:
    amount = _extract_integer(text, [
        r"[Oo]utstanding\s+(?:RSU|[Rr]estricted).*?(\d[\d,]*)",
        r"[Uu]nvested.*?(\d[\d,]*)\s+(?:shares|units)",
        r"[Rr]emaining\s+(?:RSU|[Uu]nits).*?(\d[\d,]*)",
    ])
    if amount is not None:
        return amount

    return _search_tables_for_integer(tables, ["outstanding", "unvested", "remaining"])


def _extract_rsu_vested(text: str, tables: list) -> Optional[int]:
    amount = _extract_integer(text, [
        r"[Vv]ested\s+(?:during|in).*?(\d[\d,]*)\s+(?:shares|units)",
        r"RSU[s]?\s+[Vv]ested.*?(\d[\d,]*)",
        r"[Ss]hares?\s+[Vv]ested.*?(\d[\d,]*)",
        r"[Vv]esting.*?(\d[\d,]*)\s+(?:shares|units)",
    ])
    if amount is not None:
        return amount

    return _search_tables_for_integer(tables, ["vested", "vesting", "released"])


def _extract_share_holdings(text: str, tables: list) -> List[Dict[str, Any]]:
    holdings: List[Dict[str, Any]] = []

    for table in tables:
        if not table or len(table) < 2:
            continue

        header = [str(c).lower() if c else "" for c in table[0]]
        header_text = " ".join(header)
        is_holdings = any(
            kw in header_text
            for kw in ["acquisition", "vest", "date", "shares", "cost basis", "lot"]
        )
        if not is_holdings:
            continue

        date_col = _find_col_idx(header, ["acquisition", "vest", "grant", "date"])
        qty_col = _find_col_idx(header, ["shares", "quantity", "qty", "units"])
        cost_col = _find_col_idx(header, ["cost", "basis", "price", "acquisition cost"])
        value_col = _find_col_idx(header, ["value", "market", "current", "closing"])

        for row in table[1:]:
            try:
                if not row or all(c is None or str(c).strip() == "" for c in row):
                    continue

                lot: Dict[str, Any] = {
                    "acquisition_date": _safe_get(row, date_col),
                    "qty": _parse_int(_safe_get(row, qty_col)),
                    "cost_basis": _parse_float(_safe_get(row, cost_col)),
                    "current_value": _parse_float(_safe_get(row, value_col)),
                }

                if lot["qty"] and lot["qty"] > 0:
                    holdings.append(lot)
            except Exception:
                continue

    return holdings


def _extract_dividends(text: str, tables: list) -> List[Dict[str, Any]]:
    divs: List[Dict[str, Any]] = []

    for table in tables:
        if not table or len(table) < 2:
            continue

        header = [str(c).lower() if c else "" for c in table[0]]
        header_text = " ".join(header)
        is_dividend = any(
            kw in header_text for kw in ["dividend", "distribution", "income"]
        )
        if not is_dividend:
            continue

        date_col = _find_col_idx(header, ["date", "pay", "record", "ex-date"])
        amount_col = _find_col_idx(header, ["amount", "dividend", "gross", "value"])

        for row in table[1:]:
            try:
                if not row or all(c is None or str(c).strip() == "" for c in row):
                    continue

                amount = _parse_float(_safe_get(row, amount_col))
                if amount and amount > 0:
                    divs.append({
                        "date": _safe_get(row, date_col),
                        "amount": amount,
                    })
            except Exception:
                continue

    if not divs:
        div_pattern = re.findall(
            r"[Dd]ividend.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}).*?\$?\s*(\d[\d,]*\.?\d*)",
            text,
        )
        for date_str, amount_str in div_pattern:
            try:
                amount = float(amount_str.replace(",", ""))
                if amount > 0:
                    divs.append({"date": date_str, "amount": amount})
            except ValueError:
                continue

    return divs


def _extract_closing_value(text: str, tables: list) -> Optional[float]:
    patterns = [
        r"[Cc]losing\s+[Vv]alue.*?\$?\s*(\d[\d,]*\.?\d*)",
        r"[Tt]otal\s+[Vv]alue.*?\$?\s*(\d[\d,]*\.?\d*)",
        r"[Mm]arket\s+[Vv]alue.*?\$?\s*(\d[\d,]*\.?\d*)",
        r"[Ee]nd(?:ing)?\s+[Bb]alance.*?\$?\s*(\d[\d,]*\.?\d*)",
        r"[Aa]ccount\s+[Vv]alue.*?\$?\s*(\d[\d,]*\.?\d*)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1).replace(",", ""))
            except ValueError:
                continue

    return _search_tables_for_float(
        tables, ["closing", "total value", "market value", "ending"]
    )


def _extract_exchange_rate(text: str) -> Optional[float]:
    patterns = [
        r"[Ee]xchange\s+[Rr]ate[:\s]*(\d+\.?\d*)",
        r"USD[/\s]*INR[:\s]*(\d+\.?\d*)",
        r"1\s*USD\s*=\s*(?:INR|Rs\.?)\s*(\d+\.?\d*)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                continue
    return None


def _find_col_idx(header: List[str], candidates: List[str]) -> Optional[int]:
    for candidate in candidates:
        for idx, h in enumerate(header):
            if candidate in h:
                return idx
    return None


def _safe_get(row: list, idx: Optional[int]) -> Optional[str]:
    if idx is None or idx >= len(row):
        return None
    val = row[idx]
    if val is None:
        return None
    return str(val).strip()


def _parse_float(val: Optional[str]) -> Optional[float]:
    if not val:
        return None
    try:
        cleaned = val.replace(",", "").replace("$", "").replace("₹", "").strip()
        if cleaned in ("", "-", "N/A", "n/a"):
            return None
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def _parse_int(val: Optional[str]) -> Optional[int]:
    f = _parse_float(val)
    if f is None:
        return None
    return int(f)


def _extract_integer(text: str, patterns: list) -> Optional[int]:
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1).replace(",", ""))
            except (ValueError, IndexError):
                continue
    return None


def _search_tables_for_integer(tables: list, keywords: list) -> Optional[int]:
    for table in tables:
        for row in table:
            if not row:
                continue
            row_text = " ".join(str(c).lower() for c in row if c)
            if any(kw in row_text for kw in keywords):
                for cell in reversed(row):
                    val = _parse_int(str(cell) if cell else None)
                    if val is not None and val > 0:
                        return val
    return None


def _search_tables_for_float(tables: list, keywords: list) -> Optional[float]:
    for table in tables:
        for row in table:
            if not row:
                continue
            row_text = " ".join(str(c).lower() for c in row if c)
            if any(kw in row_text for kw in keywords):
                for cell in reversed(row):
                    val = _parse_float(str(cell) if cell else None)
                    if val is not None and val > 0:
                        return val
    return None
