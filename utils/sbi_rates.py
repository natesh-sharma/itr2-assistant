import io
from datetime import date, timedelta
from typing import Optional, Union

import pandas as pd
import requests

SBI_CSV_URL = (
    "https://raw.githubusercontent.com/sahilgupta/sbi-fx-ratekeeper"
    "/main/csv_files/SBI_REFERENCE_RATES_USD.csv"
)


def fetch_sbi_rates() -> pd.DataFrame:
    response = requests.get(SBI_CSV_URL, timeout=30)
    response.raise_for_status()
    df = pd.read_csv(io.StringIO(response.text))
    df.columns = df.columns.str.strip()
    date_col = "DATE" if "DATE" in df.columns else "Date"
    tt_col = "TT BUY" if "TT BUY" in df.columns else "TT_BUY"
    df["Date"] = pd.to_datetime(df[date_col], format="mixed", dayfirst=False)
    df["TT_BUY"] = pd.to_numeric(df[tt_col], errors="coerce")
    df = df[["Date", "TT_BUY"]].dropna(subset=["TT_BUY"])
    df = df[df["TT_BUY"] > 0]
    df = df.sort_values("Date").reset_index(drop=True)
    return df


def get_tt_buying_rate(
    target_date: Union[date, str], rates_df: pd.DataFrame
) -> Optional[float]:
    if isinstance(target_date, str):
        target_date = pd.to_datetime(target_date).date()

    target_ts = pd.Timestamp(target_date)

    exact = rates_df.loc[rates_df["Date"] == target_ts, "TT_BUY"]
    if not exact.empty:
        return float(exact.iloc[0])

    preceding = rates_df[rates_df["Date"] < target_ts]
    if preceding.empty:
        return None
    return float(preceding.iloc[-1]["TT_BUY"])


def convert_usd_to_inr(
    amount_usd: float,
    target_date: Union[date, str],
    rates_df: pd.DataFrame,
) -> Optional[float]:
    rate = get_tt_buying_rate(target_date, rates_df)
    if rate is None:
        return None
    return round(amount_usd * rate, 2)
