import re
from typing import Any, Dict, Optional

import pdfplumber


def parse_form16(pdf: pdfplumber.PDF) -> Dict[str, Any]:
    text = _extract_full_text(pdf)
    lines = text.split("\n")

    result: Dict[str, Any] = {
        "salary_17_1": _find_labeled_amount(lines, r"section\s+17\s*\(\s*1\s*\)"),
        "perquisites_17_2": _find_labeled_amount(lines, r"section\s+17\s*\(\s*2\s*\)"),
        "profits_17_3": _find_labeled_amount(lines, r"section\s+17\s*\(\s*3\s*\)", allow_zero=True),
        "gross_salary": _find_labeled_amount(lines, r"\(d\)\s*Total"),
        "tds_total": _find_labeled_amount(lines, r"Net\s+tax\s+payable"),
        "employer_name": _extract_text_field(text, [
            r"[Nn]ame\s+(?:and\s+address\s+)?of\s+the\s+[Ee]mployer[:\s]*(.+?)(?:\n|$)",
        ]),
        "employer_tan": _extract_text_field(text, [
            r"TAN\s+of\s+Employer[:\s]*([A-Z]{4}\d{5}[A-Z])",
            r"TAN[:\s]*([A-Z]{4}\d{5}[A-Z])",
        ]),
    }

    if not result["tds_total"]:
        result["tds_total"] = _find_labeled_amount(lines, r"Tax\s+payable\s*\(13")

    if not result["gross_salary"]:
        result["gross_salary"] = _find_labeled_amount(lines, r"Gross\s+Salary")

    return result


def _find_labeled_amount(lines: list, label_pattern: str, allow_zero: bool = False) -> Optional[float]:
    for i, line in enumerate(lines):
        if re.search(label_pattern, line, re.IGNORECASE):
            amount = _extract_trailing_amount(line)
            if amount is not None and (amount > 1 or (allow_zero and amount == 0)):
                return amount
            for j in range(1, 3):
                if i + j < len(lines):
                    amount = _extract_trailing_amount(lines[i + j])
                    if amount is not None and (amount > 1 or (allow_zero and amount == 0)):
                        return amount
    return None


def _extract_trailing_amount(line: str) -> Optional[float]:
    matches = re.findall(r"(\d[\d,]*\.\d{2})\b", line)
    if matches:
        try:
            return float(matches[-1].replace(",", ""))
        except ValueError:
            return None
    return None


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


def _extract_text_field(text: str, patterns: list) -> Optional[str]:
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            if value:
                return value
    return None
