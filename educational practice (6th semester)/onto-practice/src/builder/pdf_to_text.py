"""Extract plain text from a regulation PDF (text-based PDF — not OCR)."""

from __future__ import annotations

import re
from pathlib import Path

import pdfplumber

_HEADER_PATTERNS = [
    re.compile(r"^Федеральное государственное автономное.*$", re.MULTILINE),
    re.compile(r"^образовательное учреждение.*$", re.MULTILINE),
    re.compile(r"^«Новосибирский национальный.*$", re.MULTILINE),
    re.compile(r"^государственный университет».*$", re.MULTILINE),
    re.compile(r"^Факультет информационных технологий стр\..*$", re.MULTILINE),
    re.compile(r"^Методические рекомендации по организации.*$", re.MULTILINE),
    re.compile(r"^проведению практики обучающихся ФИТ\s*$", re.MULTILINE),
]


def extract_text(pdf_path: Path) -> str:
    """Return the regulation as a single string with running headers stripped."""
    pages: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            pages.append(t)
    text = "\n".join(pages)
    for pat in _HEADER_PATTERNS:
        text = pat.sub("", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
