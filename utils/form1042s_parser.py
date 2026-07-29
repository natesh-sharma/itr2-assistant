import re
from typing import Any, Dict, Optional

import pdfplumber


def parse_1042s(pdf: pdfplumber.PDF) -> Dict[str, Any]:
    text = _extract_full_text(pdf)

    result: Dict[str, Any] = {
        "income_code": _extract_text_field(text, [
            r"[Ii]ncome\s+[Cc]ode[:\s]*(\d{2})",
            r"Box\s*1[:\s]*(\d{2})",
        ]),
        "gross_income_usd": _extract_amount(text, [
            r"[Gg]ross\s+[Ii]ncome.*?\$?\s*(\d[\d,]*\.?\d*)",
            r"Box\s*2[:\s]*\$?\s*(\d[\d,]*\.?\d*)",
        ]),
        "tax_rate": _extract_percentage(text, [
            r"[Tt]ax\s+[Rr]ate[:\s]*(\d+\.?\d*)\s*%",
            r"[Rr]ate\s+of\s+[Ww]ithholding[:\s]*(\d+\.?\d*)",
            r"Box\s*3[a-b]?[:\s]*(\d+\.?\d*)\s*%?",
        ]),
        "federal_tax_withheld_usd": _extract_amount(text, [
            r"[Ff]ederal\s+[Tt]ax\s+[Ww]ithheld.*?\$?\s*(\d[\d,]*\.?\d*)",
            r"Box\s*7[:\s]*\$?\s*(\d[\d,]*\.?\d*)",
            r"[Tt]ax\s+[Ww]ithheld.*?\$?\s*(\d[\d,]*\.?\d*)",
        ]),
        "recipient_name": _extract_text_field(text, [
            r"[Rr]ecipient'?s?\s+[Nn]ame[:\s]*(.+?)(?:\n|$)",
            r"Box\s*13[a-z]?[:\s]*(.+?)(?:\n|$)",
        ]),
        "recipient_country": _extract_text_field(text, [
            r"[Cc]ountry\s+[Cc]ode[:\s]*([A-Z]{2})",
            r"[Rr]ecipient.*?[Cc]ountry[:\s]*(.+?)(?:\n|$)",
            r"Box\s*12[a-z]?[:\s]*([A-Z]{2})",
        ]),
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


def _extract_amount(text: str, patterns: list) -> Optional[float]:
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            try:
                raw = match.group(1).replace(",", "").replace("$", "").strip()
                value = float(raw)
                if value >= 0:
                    return value
            except (ValueError, IndexError):
                continue
    return None


def _extract_percentage(text: str, patterns: list) -> Optional[float]:
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except (ValueError, IndexError):
                continue
    return None


def _extract_text_field(text: str, patterns: list) -> Optional[str]:
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            if value:
                return value
    return None
