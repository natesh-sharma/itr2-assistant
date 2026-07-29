import re
from typing import Any, Dict, Optional

import pdfplumber


def parse_form16(pdf: pdfplumber.PDF) -> Dict[str, Any]:
    text = _extract_full_text(pdf)

    result: Dict[str, Any] = {
        "salary_17_1": _extract_amount(text, [
            r"17\s*\(\s*1\s*\).*?(\d[\d,]*\.?\d*)",
            r"[Ss]alary\s+as\s+per.*?(\d[\d,]*\.?\d*)",
            r"[Ss]alary\s+under\s+section\s+17\(1\).*?(\d[\d,]*\.?\d*)",
        ]),
        "perquisites_17_2": _extract_amount(text, [
            r"17\s*\(\s*2\s*\).*?(\d[\d,]*\.?\d*)",
            r"[Pp]erquisites.*?(\d[\d,]*\.?\d*)",
            r"[Vv]alue\s+of\s+perquisites.*?(\d[\d,]*\.?\d*)",
        ]),
        "profits_17_3": _extract_amount(text, [
            r"17\s*\(\s*3\s*\).*?(\d[\d,]*\.?\d*)",
            r"[Pp]rofits\s+in\s+lieu.*?(\d[\d,]*\.?\d*)",
        ]),
        "gross_salary": _extract_amount(text, [
            r"[Gg]ross\s+[Ss]alary.*?(\d[\d,]*\.?\d*)",
            r"[Gg]ross\s+total.*?salary.*?(\d[\d,]*\.?\d*)",
        ]),
        "tds_total": _extract_amount(text, [
            r"[Tt]otal\s+[Tt]ax\s+[Dd]educted.*?(\d[\d,]*\.?\d*)",
            r"[Tt]ax\s+[Dd]educted\s+at\s+[Ss]ource.*?(\d[\d,]*\.?\d*)",
            r"TDS.*?[Tt]otal.*?(\d[\d,]*\.?\d*)",
        ]),
        "employer_name": _extract_text_field(text, [
            r"[Nn]ame\s+(?:and\s+address\s+)?of\s+the\s+[Ee]mployer[:\s]*(.+?)(?:\n|$)",
            r"[Ee]mployer\s*[:\-]\s*(.+?)(?:\n|$)",
            r"[Nn]ame\s+of\s+[Dd]eductor[:\s]*(.+?)(?:\n|$)",
        ]),
        "employer_tan": _extract_text_field(text, [
            r"TAN\s+(?:of\s+the\s+)?[Dd]eductor[:\s]*([A-Z]{4}\d{5}[A-Z])",
            r"TAN[:\s]*([A-Z]{4}\d{5}[A-Z])",
            r"([A-Z]{4}\d{5}[A-Z])",
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
                raw = match.group(1).replace(",", "").strip()
                value = float(raw)
                if value > 0:
                    return value
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
