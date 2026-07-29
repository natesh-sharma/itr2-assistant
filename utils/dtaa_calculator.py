from typing import Any, Dict, List


def compute_dtaa_relief(
    foreign_income_inr: float,
    tax_paid_abroad_inr: float,
    indian_tax_rate: float,
    country: str = "USA",
) -> Dict[str, Any]:
    indian_tax_on_foreign = round(foreign_income_inr * indian_tax_rate, 2)
    relief = round(min(tax_paid_abroad_inr, indian_tax_on_foreign), 2)

    return {
        "relief_amount": relief,
        "section": "90",
        "article": "10",
        "country": country,
        "foreign_income_inr": foreign_income_inr,
        "tax_paid_abroad_inr": tax_paid_abroad_inr,
        "indian_tax_on_foreign_income": indian_tax_on_foreign,
        "method": "tax_credit",
    }


def prepare_form67_data(
    dividends_list: List[Dict[str, Any]],
) -> Dict[str, Any]:
    entries: List[Dict[str, Any]] = []
    total_income_usd = 0.0
    total_tax_usd = 0.0
    total_income_inr = 0.0
    total_tax_inr = 0.0

    for div in dividends_list:
        amount_usd = div["amount_usd"]
        tax_usd = div["tax_usd"]
        sbi_rate = div["sbi_rate"]

        amount_inr = round(amount_usd * sbi_rate, 2)
        tax_inr = round(tax_usd * sbi_rate, 2)

        entry = {
            "date": div["date"],
            "amount_usd": amount_usd,
            "tax_withheld_usd": tax_usd,
            "sbi_tt_buying_rate": sbi_rate,
            "amount_inr": amount_inr,
            "tax_withheld_inr": tax_inr,
            "country_code": "US",
            "taxpayer_id_in_country": div.get("taxpayer_id", ""),
            "income_code": "06",
        }
        entries.append(entry)

        total_income_usd += amount_usd
        total_tax_usd += tax_usd
        total_income_inr += amount_inr
        total_tax_inr += tax_inr

    return {
        "entries": entries,
        "summary": {
            "total_income_usd": round(total_income_usd, 2),
            "total_tax_usd": round(total_tax_usd, 2),
            "total_income_inr": round(total_income_inr, 2),
            "total_tax_inr": round(total_tax_inr, 2),
            "country": "United States of America",
            "country_code": "US",
            "dtaa_article": "Article 10",
            "section": "90",
        },
    }
