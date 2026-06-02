"""Remote OCR via OpenRouter — Qianfan OCR Fast specialised on plain-text reads.

Splits the OCR step from the structuring step:
- this module turns PNG pages into raw text (no JSON, no structure);
- order_parser then sends the concatenated text to a text-LLM that extracts
  the OrderFacts schema with a strict 'do not normalise / do not invent' prompt.

The split lowers hallucination dramatically because the model that reads the
image isn't asked to also reason about schema, and the model that fills the
schema doesn't see the image — so it can only work with what was actually
recognised.
"""

from __future__ import annotations

import base64
import logging
import os
from pathlib import Path

from src.extractors.llm import (
    QuotaExhaustedError,
    get_pool,
    is_connection_error,
    is_quota_exhausted_error,
    is_upstream_rate_limited,
    make_client,
)

log = logging.getLogger(__name__)

OCR_MODEL_PRIMARY = "baidu/qianfan-ocr-fast:free"
OCR_MODEL_FALLBACK = "google/gemma-3-12b-it:free"  # general vision as fallback

_OCR_PROMPT = (
    "Распознай весь текст с этой страницы документа дословно. "
    "Иди слева-направо, сверху-вниз. Между ячейками таблицы вставляй переводы "
    "строк. Не интерпретируй, не нормализуй имена и числа — переноси буква-в-букву "
    "то, что видишь. Если фрагмент нечитаем — пиши <?>. Только текст, без "
    "комментариев."
)


def ocr_pages(png_paths: list[Path]) -> list[str]:
    """Run remote OCR on every page. Returns list of raw text per page."""
    out: list[str] = []
    for i, p in enumerate(png_paths, start=1):
        text = _ocr_one_page(p, page_no=i)
        out.append(text or "")
    return out


def _ocr_one_page(png_path: Path, page_no: int) -> str | None:
    """OCR a single page, with key rotation on per-day quota and one fallback model."""
    with png_path.open("rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()

    pool = get_pool()
    for model in (OCR_MODEL_PRIMARY, OCR_MODEL_FALLBACK):
        connection_attempts = 0
        upstream_attempts = 0
        while True:
            try:
                client = make_client(timeout=60.0)
                resp = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": _OCR_PROMPT},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{img_b64}"
                                    },
                                },
                            ],
                        }
                    ],
                    max_tokens=4000,
                    temperature=0,
                )
                text = (resp.choices[0].message.content or "") if resp.choices else ""
                if not text.strip():
                    log.warning("page %d: %s returned empty text", page_no, model)
                    break
                log.info("page %d: ocr ok via %s (%d chars)", page_no, model, len(text))
                return text
            except QuotaExhaustedError:
                raise
            except Exception as e:  # noqa: BLE001
                if is_quota_exhausted_error(e):
                    pool.mark_exhausted(client.api_key)
                    log.info("page %d: rotating key for OCR via %s", page_no, model)
                    continue
                if is_upstream_rate_limited(e) and upstream_attempts < 1:
                    upstream_attempts += 1
                    log.warning(
                        "page %d: %s upstream rate-limited — backoff 20s, retry",
                        page_no, model,
                    )
                    import time as _t
                    _t.sleep(20)
                    continue
                if is_connection_error(e) and connection_attempts < 2:
                    connection_attempts += 1
                    log.warning(
                        "page %d: %s connection error (attempt %d) — retrying",
                        page_no, model, connection_attempts,
                    )
                    continue
                log.warning(
                    "page %d: OCR via %s failed (%s: %.120s)",
                    page_no, model, type(e).__name__, str(e),
                )
                break
    log.warning("page %d: OCR gave nothing — page text will be empty", page_no)
    return None


def env_dpi() -> int:
    try:
        return int(os.getenv("OCR_DPI", "300"))
    except ValueError:
        return 300
