import re
from typing import Any, Dict, Optional

import pdfplumber


def parse_1042s(pdf: pdfplumber.PDF) -> Dict[str, Any]:
    text = _extract_full_text(pdf)

    income_code = None
    gross_income = None
    tax_rate = None
    tax_withheld = None
    recipient_name = None
    recipient_country = None

    # 1042-S has a dense line like "06 360.00 25.00 00.00" for income code, gross, rate
    # Must match on a single line; line may have trailing data like "16"
    dense_match = re.search(r"^(\d{2})\s+(\d+\.\d{2})\s+(\d+\.\d{2})\s+(\d+\.\d{2})", text, re.MULTILINE)
    if dense_match:
        income_code = dense_match.group(1)
        gross_income = float(dense_match.group(2))
        tax_rate = float(dense_match.group(3))

    # Federal tax withheld appears as a standalone amount (e.g., "90.00") after the dense line
    # Look for "Federal tax withheld" label or the value after the dense line
    fed_match = re.search(r"[Ff]ederal\s+tax\s+withheld.*?(\d+\.?\d*)", text, re.DOTALL)
    if fed_match:
        tax_withheld = float(fed_match.group(1))
    else:
        amounts = re.findall(r"^(\d+\.\d{2})$", text, re.MULTILINE)
        for amt in amounts:
            val = float(amt)
            if gross_income and 0 < val < gross_income:
                tax_withheld = val
                break

    # Recipient name — look for line before country code "IN"
    name_match = re.search(r"([A-Z][A-Z ]+)\s+IN\b", text)
    if name_match:
        recipient_name = name_match.group(1).strip()

    # Recipient country
    country_match = re.search(r"13b\)?\s*.*?([A-Z]{2})\b", text)
    if not country_match:
        country_match = re.search(r"\b(IN)\b.*?(?:India|INDIA)", text)
    if country_match:
        recipient_country = country_match.group(1)
    else:
        if "India" in text or "INDIA" in text:
            recipient_country = "IN"

    return {
        "income_code": income_code,
        "gross_income_usd": gross_income,
        "tax_rate": tax_rate,
        "federal_tax_withheld_usd": tax_withheld,
        "recipient_name": recipient_name,
        "recipient_country": recipient_country,
    }


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
