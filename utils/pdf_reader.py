import io
import tempfile
from pathlib import Path
from typing import Any, BinaryIO, List, Optional, Union

import pdfplumber
import pikepdf


def read_pdf(
    file: Union[str, Path, BinaryIO], password: Optional[str] = None
) -> pdfplumber.PDF:
    if password:
        file_bytes = _read_file_bytes(file)
        decrypted_bytes = _decrypt_pdf(file_bytes, password)
        return pdfplumber.open(io.BytesIO(decrypted_bytes))

    if isinstance(file, (str, Path)):
        return pdfplumber.open(file)
    return pdfplumber.open(file)


def extract_tables(pdf: pdfplumber.PDF) -> List[List[List[Optional[str]]]]:
    tables: List[List[List[Optional[str]]]] = []
    for page in pdf.pages:
        try:
            page_tables = page.extract_tables()
            if page_tables:
                tables.extend(page_tables)
        except Exception:
            continue
    return tables


def extract_text(pdf: pdfplumber.PDF) -> str:
    parts: List[str] = []
    for page in pdf.pages:
        try:
            text = page.extract_text()
            if text:
                parts.append(text)
        except Exception:
            continue
    return "\n".join(parts)


def _read_file_bytes(file: Union[str, Path, BinaryIO]) -> bytes:
    if isinstance(file, (str, Path)):
        return Path(file).read_bytes()
    return file.read()


def _decrypt_pdf(file_bytes: bytes, password: str) -> bytes:
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        with pikepdf.open(io.BytesIO(file_bytes), password=password) as pdf:
            pdf.save(str(tmp_path))
        return tmp_path.read_bytes()
    finally:
        tmp_path.unlink(missing_ok=True)
