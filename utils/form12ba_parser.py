import re
from typing import Any, Dict, Optional

import pdfplumber


def parse_form12ba(pdf: pdfplumber.PDF) -> Dict[str, Any]:
    text = _extract_full_text(pdf)
    tables = _extract_all_tables(pdf)

    result: Dict[str, Any] = {
        "total_perquisites": _extract_perquisites_total(text, tables),
        "stock_option_value": _extract_stock_option(text, tables),
        "other_benefits": _extract_other_benefits(text, tables),
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


def _extract_perquisites_total(text: str, tables: list) -> Optional[float]:
    amount = _extract_amount(text, [
        r"[Tt]otal\s+(?:value\s+of\s+)?[Pp]erquisites.*?(\d[\d,]*\.?\d*)",
        r"[Gg]rand\s+[Tt]otal.*?[Pp]erquisites.*?(\d[\d,]*\.?\d*)",
        r"[Tt]otal\s+\(.*?\).*?(\d[\d,]*\.?\d*)",
    ])
    if amount is not None:
        return amount

    return _search_tables_for_amount(tables, ["total", "perquisite", "grand"])


def _extract_stock_option(text: str, tables: list) -> Optional[float]:
    amount = _extract_amount(text, [
        r"[Ss]tock\s+[Oo]ption.*?[Ss]weat\s+[Ee]quity.*?(\d[\d,]*\.?\d*)",
        r"ESOP.*?(\d[\d,]*\.?\d*)",
        r"[Ss]hares?\s+allot.*?(\d[\d,]*\.?\d*)",
        r"[Ss]tock\s+[Oo]ption.*?(\d[\d,]*\.?\d*)",
        r"[Ss]weat\s+[Ee]quity.*?(\d[\d,]*\.?\d*)",
    ])
    if amount is not None:
        return amount

    return _search_tables_for_amount(tables, ["stock", "option", "esop", "sweat"])


def _extract_other_benefits(text: str, tables: list) -> Optional[float]:
    amount = _extract_amount(text, [
        r"[Oo]ther\s+[Bb]enefit.*?(\d[\d,]*\.?\d*)",
        r"[Aa]menity.*?(\d[\d,]*\.?\d*)",
        r"[Oo]ther\s+[Ff]ringe.*?(\d[\d,]*\.?\d*)",
    ])
    if amount is not None:
        return amount

    return _search_tables_for_amount(tables, ["other", "benefit", "amenity", "fringe"])


def _extract_amount(text: str, patterns: list) -> Optional[float]:
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            try:
                raw = match.group(1).replace(",", "").strip()
                value = float(raw)
                if value > 0:
                    return value
            except (ValueError, IndexError):
                continue
    return None


def _search_tables_for_amount(
    tables: list, keywords: list
) -> Optional[float]:
    for table in tables:
        for row in table:
            if not row:
                continue
            row_text = " ".join(str(cell).lower() for cell in row if cell)
            if any(kw in row_text for kw in keywords):
                for cell in reversed(row):
                    val = _parse_numeric(cell)
                    if val is not None and val > 0:
                        return val
    return None


def _parse_numeric(val: Any) -> Optional[float]:
    if val is None:
        return None
    try:
        cleaned = str(val).replace(",", "").replace("₹", "").strip()
        if cleaned in ("", "-", "nil", "Nil", "NIL"):
            return None
        return float(cleaned)
    except (ValueError, TypeError):
        return None
