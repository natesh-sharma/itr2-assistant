from datetime import datetime
from typing import Any, BinaryIO, Dict, List, Optional, Union

import pandas as pd


def parse_zerodha_pnl(file: Union[str, BinaryIO]) -> Dict[str, Any]:
    try:
        xl = pd.ExcelFile(file)
    except Exception as e:
        raise ValueError(f"Failed to read Excel file: {e}") from e

    equity_stcg: List[Dict] = []
    equity_ltcg: List[Dict] = []
    mf_ltcg_equity: List[Dict] = []
    mf_ltcg_debt: List[Dict] = []
    dividends: List[Dict] = []

    for sheet_name in xl.sheet_names:
        df = xl.parse(sheet_name, header=None)
        lower_name = sheet_name.lower()

        if "equity" in lower_name and ("delivery" in lower_name or "stock" in lower_name):
            stcg, ltcg = _parse_equity_delivery(df)
            equity_stcg.extend(stcg)
            equity_ltcg.extend(ltcg)
        elif "mutual" in lower_name or "mf" in lower_name:
            eq_mf, debt_mf = _parse_mutual_fund(df)
            mf_ltcg_equity.extend(eq_mf)
            mf_ltcg_debt.extend(debt_mf)
        elif "dividend" in lower_name:
            dividends.extend(_parse_dividends(df))
        else:
            stcg, ltcg = _parse_equity_delivery(df)
            if stcg or ltcg:
                equity_stcg.extend(stcg)
                equity_ltcg.extend(ltcg)

    stcg_total = sum(t["profit"] for t in equity_stcg)
    ltcg_equity_total = sum(t["profit"] for t in equity_ltcg) + sum(
        t["profit"] for t in mf_ltcg_equity
    )
    ltcg_debt_total = sum(t["profit"] for t in mf_ltcg_debt)
    dividend_total = sum(d["amount"] for d in dividends)

    return {
        "equity_stcg": equity_stcg,
        "equity_ltcg": equity_ltcg,
        "mf_ltcg_equity": mf_ltcg_equity,
        "mf_ltcg_debt": mf_ltcg_debt,
        "dividends": dividends,
        "summary": {
            "stcg_total": round(stcg_total, 2),
            "ltcg_equity_total": round(ltcg_equity_total, 2),
            "ltcg_debt_total": round(ltcg_debt_total, 2),
            "dividend_total": round(dividend_total, 2),
        },
    }


def _find_header_row(df: pd.DataFrame) -> Optional[int]:
    target_cols = {"symbol", "isin", "trade", "quantity", "buy", "sell"}
    for idx, row in df.iterrows():
        row_vals = {str(v).strip().lower() for v in row.values if pd.notna(v)}
        matches = sum(1 for t in target_cols if any(t in v for v in row_vals))
        if matches >= 3:
            return idx
    return None


def _parse_equity_delivery(df: pd.DataFrame) -> tuple:
    stcg: List[Dict] = []
    ltcg: List[Dict] = []

    header_idx = _find_header_row(df)
    if header_idx is None:
        return stcg, ltcg

    headers = [str(v).strip().lower() for v in df.iloc[header_idx]]
    df_data = df.iloc[header_idx + 1:].copy()
    df_data.columns = headers

    col_map = _map_columns(headers)

    for _, row in df_data.iterrows():
        try:
            trade = _build_trade(row, col_map)
            if trade is None:
                continue

            if trade["holding_days"] > 365:
                ltcg.append(trade)
            else:
                stcg.append(trade)
        except Exception:
            continue

    return stcg, ltcg


def _parse_mutual_fund(df: pd.DataFrame) -> tuple:
    equity_mf: List[Dict] = []
    debt_mf: List[Dict] = []

    header_idx = _find_header_row(df)
    if header_idx is None:
        return equity_mf, debt_mf

    headers = [str(v).strip().lower() for v in df.iloc[header_idx]]
    df_data = df.iloc[header_idx + 1:].copy()
    df_data.columns = headers

    col_map = _map_columns(headers)

    for _, row in df_data.iterrows():
        try:
            trade = _build_trade(row, col_map)
            if trade is None:
                continue

            scheme_name = str(row.get(col_map.get("symbol", ""), "")).lower()
            is_debt = any(
                kw in scheme_name
                for kw in ["debt", "liquid", "money market", "gilt", "bond", "fixed"]
            )

            if is_debt:
                debt_mf.append(trade)
            else:
                equity_mf.append(trade)
        except Exception:
            continue

    return equity_mf, debt_mf


def _parse_dividends(df: pd.DataFrame) -> List[Dict]:
    divs: List[Dict] = []

    header_idx = None
    for idx, row in df.iterrows():
        row_vals = {str(v).strip().lower() for v in row.values if pd.notna(v)}
        if any("symbol" in v or "scrip" in v for v in row_vals) and any(
            "amount" in v or "dividend" in v for v in row_vals
        ):
            header_idx = idx
            break

    if header_idx is None:
        return divs

    headers = [str(v).strip().lower() for v in df.iloc[header_idx]]
    df_data = df.iloc[header_idx + 1:].copy()
    df_data.columns = headers

    symbol_col = _find_col(headers, ["symbol", "scrip", "name"])
    amount_col = _find_col(headers, ["amount", "dividend", "value"])
    date_col = _find_col(headers, ["date", "ex-date", "ex date", "record"])

    for _, row in df_data.iterrows():
        try:
            amount = _to_float(row.get(amount_col))
            if amount is None or amount == 0:
                continue

            divs.append({
                "symbol": str(row.get(symbol_col, "")).strip(),
                "amount": round(amount, 2),
                "ex_date": _parse_date(row.get(date_col)),
            })
        except Exception:
            continue

    return divs


def _map_columns(headers: List[str]) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    mapping["symbol"] = _find_col(headers, ["symbol", "scrip", "name", "stock"])
    mapping["isin"] = _find_col(headers, ["isin"])
    mapping["buy_date"] = _find_col(headers, ["buy date", "purchase date", "buy_date", "acquisition"])
    mapping["sell_date"] = _find_col(headers, ["sell date", "sale date", "sell_date", "redemption"])
    mapping["qty"] = _find_col(headers, ["quantity", "qty", "units"])
    mapping["buy_value"] = _find_col(headers, ["buy value", "buy_value", "purchase value", "cost", "buy amount"])
    mapping["sell_value"] = _find_col(headers, ["sell value", "sell_value", "sale value", "sale amount"])
    mapping["profit"] = _find_col(headers, ["p&l", "pnl", "profit", "gain", "realized"])
    mapping["fmv"] = _find_col(headers, ["fmv", "fair market", "nav"])
    return mapping


def _find_col(headers: List[str], candidates: List[str]) -> str:
    for candidate in candidates:
        for h in headers:
            if candidate in h:
                return h
    return ""


def _build_trade(row: pd.Series, col_map: Dict[str, str]) -> Optional[Dict]:
    qty = _to_float(row.get(col_map["qty"]))
    if qty is None or qty == 0:
        return None

    buy_value = _to_float(row.get(col_map["buy_value"])) or 0
    sell_value = _to_float(row.get(col_map["sell_value"])) or 0
    profit_direct = _to_float(row.get(col_map["profit"]))
    profit = profit_direct if profit_direct is not None else (sell_value - buy_value)

    buy_date = _parse_date(row.get(col_map["buy_date"]))
    sell_date = _parse_date(row.get(col_map["sell_date"]))

    holding_days = 0
    if buy_date and sell_date:
        try:
            bd = datetime.strptime(buy_date, "%Y-%m-%d")
            sd = datetime.strptime(sell_date, "%Y-%m-%d")
            holding_days = (sd - bd).days
        except (ValueError, TypeError):
            pass

    trade: Dict[str, Any] = {
        "symbol": str(row.get(col_map["symbol"], "")).strip(),
        "isin": str(row.get(col_map["isin"], "")).strip(),
        "buy_date": buy_date,
        "sell_date": sell_date,
        "qty": int(qty),
        "buy_value": round(buy_value, 2),
        "sell_value": round(sell_value, 2),
        "profit": round(profit, 2),
        "holding_days": holding_days,
    }

    fmv = _to_float(row.get(col_map.get("fmv", "")))
    if fmv is not None:
        trade["fmv"] = round(fmv, 2)

    return trade


def _to_float(val: Any) -> Optional[float]:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        cleaned = str(val).replace(",", "").replace("₹", "").strip()
        if cleaned in ("", "-", "nan", "None"):
            return None
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def _parse_date(val: Any) -> Optional[str]:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d")
    if isinstance(val, pd.Timestamp):
        return val.strftime("%Y-%m-%d")
    try:
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y", "%d-%b-%Y"):
            try:
                return datetime.strptime(str(val).strip(), fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
    except Exception:
        pass
    return str(val).strip() if val else None
