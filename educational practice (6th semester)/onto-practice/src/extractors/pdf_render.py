"""Render PDF pages to PNG via PyMuPDF (no system poppler required)."""

from __future__ import annotations

from pathlib import Path

import fitz


def render_pages(pdf_path: Path, dest_dir: Path, dpi: int = 180) -> list[Path]:
    """Render every page of `pdf_path` to PNG. Return list of PNG paths."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    out: list[Path] = []
    doc = fitz.open(str(pdf_path))
    try:
        for i, page in enumerate(doc, start=1):
            pix = page.get_pixmap(dpi=dpi)
            target = dest_dir / f"page_{i:02d}.png"
            pix.save(str(target))
            out.append(target)
    finally:
        doc.close()
    return out
