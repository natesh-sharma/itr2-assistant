from typing import Any, Dict, List, Optional


DTAA_COUNTRIES = {
    "USA": {"name": "United States of America", "code": "US", "section": "90", "dividend_article": "10", "dividend_rate": 25, "capital_gains_article": "13", "interest_article": "11", "has_dtaa": True},
    "UK": {"name": "United Kingdom", "code": "GB", "section": "90", "dividend_article": "10", "dividend_rate": 15, "capital_gains_article": "13", "interest_article": "11", "has_dtaa": True},
    "Germany": {"name": "Germany", "code": "DE", "section": "90", "dividend_article": "10", "dividend_rate": 10, "capital_gains_article": "13", "interest_article": "11", "has_dtaa": True},
    "Singapore": {"name": "Republic of Singapore", "code": "SG", "section": "90", "dividend_article": "10", "dividend_rate": 15, "capital_gains_article": "13", "interest_article": "11", "has_dtaa": True},
    "Japan": {"name": "Japan", "code": "JP", "section": "90", "dividend_article": "10", "dividend_rate": 10, "capital_gains_article": "13", "interest_article": "11", "has_dtaa": True},
    "Canada": {"name": "Canada", "code": "CA", "section": "90", "dividend_article": "10", "dividend_rate": 15, "capital_gains_article": "13", "interest_article": "11", "has_dtaa": True},
    "Australia": {"name": "Australia", "code": "AU", "section": "90", "dividend_article": "10", "dividend_rate": 15, "capital_gains_article": "13", "interest_article": "11", "has_dtaa": True},
    "France": {"name": "France", "code": "FR", "section": "90", "dividend_article": "10", "dividend_rate": 10, "capital_gains_article": "13", "interest_article": "11", "has_dtaa": True},
    "Netherlands": {"name": "Netherlands", "code": "NL", "section": "90", "dividend_article": "10", "dividend_rate": 10, "capital_gains_article": "13", "interest_article": "11", "has_dtaa": True},
    "Switzerland": {"name": "Switzerland", "code": "CH", "section": "90", "dividend_article": "10", "dividend_rate": 10, "capital_gains_article": "13", "interest_article": "11", "has_dtaa": True},
    "UAE": {"name": "United Arab Emirates", "code": "AE", "section": "90", "dividend_article": "10", "dividend_rate": 0, "capital_gains_article": "13", "interest_article": "11", "has_dtaa": True},
    "China": {"name": "People's Republic of China", "code": "CN", "section": "90", "dividend_article": "10", "dividend_rate": 10, "capital_gains_article": "13", "interest_article": "11", "has_dtaa": True},
    "South Korea": {"name": "Republic of Korea", "code": "KR", "section": "90", "dividend_article": "10", "dividend_rate": 15, "capital_gains_article": "13", "interest_article": "11", "has_dtaa": True},
    "Ireland": {"name": "Ireland", "code": "IE", "section": "90", "dividend_article": "10", "dividend_rate": 10, "capital_gains_article": "13", "interest_article": "11", "has_dtaa": True},
    "Sweden": {"name": "Sweden", "code": "SE", "section": "90", "dividend_article": "10", "dividend_rate": 10, "capital_gains_article": "13", "interest_article": "11", "has_dtaa": True},
    "Israel": {"name": "Israel", "code": "IL", "section": "90", "dividend_article": "10", "dividend_rate": 10, "capital_gains_article": "13", "interest_article": "11", "has_dtaa": True},
    "Hong Kong": {"name": "Hong Kong", "code": "HK", "section": "90", "dividend_article": "10", "dividend_rate": 5, "capital_gains_article": "13", "interest_article": "11", "has_dtaa": True},
    "Mauritius": {"name": "Mauritius", "code": "MU", "section": "90", "dividend_article": "10", "dividend_rate": 15, "capital_gains_article": "13", "interest_article": "11", "has_dtaa": True},
}

INCOME_TYPES = {
    "dividend": {"article_key": "dividend_article", "description": "Dividends"},
    "interest": {"article_key": "interest_article", "description": "Interest"},
    "capital_gains": {"article_key": "capital_gains_article", "description": "Capital Gains"},
    "salary": {"article_key": None, "description": "Salary/Employment"},
    "other": {"article_key": None, "description": "Other Income"},
}


def get_supported_countries() -> List[str]:
    return sorted(DTAA_COUNTRIES.keys())


def get_country_info(country: str) -> Optional[Dict[str, Any]]:
    return DTAA_COUNTRIES.get(country)


def compute_dtaa_relief(
    foreign_income_inr: float,
    tax_paid_abroad_inr: float,
    indian_tax_rate: float,
    country: str = "USA",
    income_type: str = "dividend",
) -> Dict[str, Any]:
    country_info = DTAA_COUNTRIES.get(country)

    if country_info and country_info["has_dtaa"]:
        section = country_info["section"]
        income_config = INCOME_TYPES.get(income_type, {})
        article_key = income_config.get("article_key")
        article = country_info.get(article_key, "10") if article_key else "NA"
        country_name = country_info["name"]
        country_code = country_info["code"]
    else:
        section = "91"
        article = "NA"
        country_name = country
        country_code = country[:2].upper()

    indian_tax_on_foreign = round(foreign_income_inr * indian_tax_rate / 100, 2)
    relief = round(min(tax_paid_abroad_inr, indian_tax_on_foreign), 2)

    return {
        "relief_amount": relief,
        "section": section,
        "article": article,
        "country": country_name,
        "country_code": country_code,
        "income_type": income_type,
        "foreign_income_inr": foreign_income_inr,
        "tax_paid_abroad_inr": tax_paid_abroad_inr,
        "indian_tax_on_foreign_income": indian_tax_on_foreign,
        "method": "tax_credit",
        "has_dtaa": bool(country_info and country_info["has_dtaa"]),
    }


def prepare_form67_data(
    income_entries: List[Dict[str, Any]],
    country: str = "USA",
) -> Dict[str, Any]:
    country_info = DTAA_COUNTRIES.get(country, {})
    country_name = country_info.get("name", country)
    country_code = country_info.get("code", country[:2].upper())
    section = country_info.get("section", "91")
    article = country_info.get("dividend_article", "NA")

    entries: List[Dict[str, Any]] = []
    total_income_foreign = 0.0
    total_tax_foreign = 0.0
    total_income_inr = 0.0
    total_tax_inr = 0.0

    for item in income_entries:
        amount_foreign = item["amount_usd"]
        tax_foreign = item["tax_usd"]
        sbi_rate = item["sbi_rate"]
        currency = item.get("currency", "USD")

        amount_inr = round(amount_foreign * sbi_rate, 2)
        tax_inr = round(tax_foreign * sbi_rate, 2)

        entry = {
            "date": item["date"],
            "amount_foreign": amount_foreign,
            "tax_withheld_foreign": tax_foreign,
            "currency": currency,
            "sbi_tt_buying_rate": sbi_rate,
            "amount_inr": amount_inr,
            "tax_withheld_inr": tax_inr,
            "country_code": country_code,
            "taxpayer_id_in_country": item.get("taxpayer_id", "NA"),
            "income_type": item.get("income_type", "dividend"),
        }
        entries.append(entry)

        total_income_foreign += amount_foreign
        total_tax_foreign += tax_foreign
        total_income_inr += amount_inr
        total_tax_inr += tax_inr

    return {
        "entries": entries,
        "summary": {
            "total_income_foreign": round(total_income_foreign, 2),
            "total_tax_foreign": round(total_tax_foreign, 2),
            "total_income_inr": round(total_income_inr, 2),
            "total_tax_inr": round(total_tax_inr, 2),
            "currency": income_entries[0].get("currency", "USD") if income_entries else "USD",
            "country": country_name,
            "country_code": country_code,
            "dtaa_article": f"Article {article}",
            "section": section,
        },
    }
