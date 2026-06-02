"""Parse a practice order (PDF / DOCX / TXT) into OrderFacts via LLM.

PDF goes through OCR first (Qianfan), DOCX/TXT skip OCR — Word's built-in OCR
or a typed document already gives clean text. After loading, every input
becomes a list of page/chunk strings that get structured into JSON page by page
by a free-tier text LLM with strict 'do not normalise / do not invent' prompt.

Repeat uploads of the same file (by SHA256) are served from cache.
"""

from __future__ import annotations

import hashlib
import logging
import os
from datetime import date, datetime
from pathlib import Path

from src.extractors.llm import (
    QuotaExhaustedError,
    get_pool,
    is_connection_error,
    is_quota_exhausted_error,
    is_upstream_rate_limited,
    make_client,
    parse_json_response,
)
from src.extractors.models import (
    OrderFacts,
    PracticeLocation,
    StudentAssignment,
    Supervisor,
)
from src.extractors.text_loader import load_pages

log = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).resolve().parents[2] / "var" / "cache" / "facts"


def parse_order(file_path: Path) -> OrderFacts:
    """Parse a PDF/DOCX/TXT order, with SHA256-keyed cache."""
    digest = _sha256(file_path)

    cached = _load_cached(digest)
    if cached is not None:
        log.info("file cache hit (sha256=%s)", digest[:12])
        return cached

    if not _llm_available():
        raise RuntimeError(
            "OPENROUTER_API_KEYS is not set — cannot parse file. "
            "Set keys in .env and restart the server."
        )

    facts = _llm_parse_pages(file_path)
    _save_cached(digest, facts)
    return facts


def _load_cached(digest: str) -> OrderFacts | None:
    f = CACHE_DIR / f"{digest}.json"
    if not f.exists():
        return None
    try:
        return OrderFacts.model_validate_json(f.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def _save_cached(digest: str, facts: OrderFacts) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (CACHE_DIR / f"{digest}.json").write_text(facts.model_dump_json(indent=2), encoding="utf-8")


def _llm_available() -> bool:
    return bool(os.getenv("OPENROUTER_API_KEYS") or os.getenv("OPENROUTER_API_KEY"))


def _llm_parse_pages(file_path: Path) -> OrderFacts:
    """Load text (OCR for PDF, direct for DOCX/TXT), then structure page-by-page.

    Per-page structuring (not the whole document at once) keeps each LLM
    request small (~2-3 KB) which dramatically lowers the chance of the
    free-tier model timing out on long context or returning non-JSON. Header
    fields (order number, dates, program) appear only on the first page;
    students rows are appended from every page that has them.
    """
    page_texts = load_pages(file_path)
    non_empty = [(i + 1, t) for i, t in enumerate(page_texts) if t and t.strip()]
    if not non_empty:
        raise RuntimeError("Loader returned empty text for all pages")

    merged: dict = {"students": []}
    for pno, text in non_empty:
        log.info("structuring page %d (%d chars)", pno, len(text))
        page_data = _structure_one_page(text, pno)
        if not page_data:
            continue
        for key in (
            "order_number", "issue_date", "practice_start", "practice_end",
            "program_code", "program_name", "practice_type", "faculty",
            "dean", "approved_at",
        ):
            if not merged.get(key) and page_data.get(key):
                merged[key] = page_data[key]
        merged["students"].extend(page_data.get("students") or [])

    return _build_order_facts(merged, fallback_number=file_path.stem[:24])


_STRUCTURE_PROMPT = """Перед тобой OCR-распознавание ОДНОЙ страницы приказа российского
вуза о направлении студентов на практику. OCR может содержать ошибки.

Извлеки данные строго в JSON по схеме:
{
  "order_number": "номер приказа (как в OCR) или null",
  "issue_date": "дата приказа в YYYY-MM-DD или null",
  "practice_start": "YYYY-MM-DD или null",
  "practice_end":   "YYYY-MM-DD или null",
  "program_code":   "например 09.03.01, или null",
  "program_name":   "название направления или null",
  "practice_type":  "тип практики или null",
  "faculty":        "название факультета или null",
  "dean":           "ФИО декана или null",
  "approved_at":    "YYYY-MM-DD или null",
  "students": [
    {
      "full_name": "...", "group": "...", "record_book_number": "...",
      "course": число или null,
      "location_organization": "...", "location_address": "...",
      "supervisor_name": "...", "supervisor_position": "...",
      "supervisor_department": "..."
    }
  ]
}

ОБЯЗАТЕЛЬНЫЕ ПРАВИЛА:
1. Извлекай ТОЛЬКО то, что явно есть в OCR-тексте.
2. Имена/фамилии воспроизводи буква-в-букву как в OCR. НЕ исправляй "странные"
   фамилии на похожие — даже если OCR явно ошибся, оставь как есть.
3. НЕ добавляй студентов которых нет в OCR-выводе.
4. Если поле в OCR нечитаемо или содержит "<?>" — поставь null.
5. Если число (группа, зач.№) выглядит подозрительно (например, "20Q5" вместо
   "2025") — оставь как есть.
6. НЕ выводи markdown, только JSON. Никаких комментариев перед/после.
"""


_TEXT_MODEL_FALLBACKS = [
    # diverse providers so a Google-AI-Studio block doesn't take everything
    "qwen/qwen3-next-80b-a3b-instruct:free",
    "nvidia/nemotron-3-nano-30b-a3b:free",
    "minimax/minimax-m2.5:free",
    "google/gemma-4-26b-a4b-it:free",
]


def _structure_one_page(ocr_text: str, page_no: int) -> dict | None:
    """Structure a single OCR page into an OrderFacts-shaped dict.

    Returns None if every model in the chain refused — caller skips the page.
    """
    import time

    primary = os.environ.get("LLM_MODEL_TEXT", "inclusionai/ling-2.6-1t:free")
    models = [primary, *[m for m in _TEXT_MODEL_FALLBACKS if m != primary]]

    pool = get_pool()
    for model in models:
        connection_attempts = 0
        upstream_attempts = 0
        while True:
            try:
                client = make_client(timeout=60.0)
                resp = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": _STRUCTURE_PROMPT},
                        {"role": "user", "content": ocr_text},
                    ],
                    max_tokens=4000,
                    temperature=0,
                )
                content = (resp.choices[0].message.content or "") if resp.choices else ""
                data = parse_json_response(content)
                if data is None:
                    log.warning("page %d: %s gave no JSON; next model", page_no, model)
                    break
                log.info(
                    "page %d: structure ok via %s (students: %d)",
                    page_no, model, len(data.get("students") or []),
                )
                return data
            except QuotaExhaustedError:
                raise
            except Exception as e:  # noqa: BLE001
                if is_quota_exhausted_error(e):
                    pool.mark_exhausted(client.api_key)
                    log.info("page %d: rotating key for %s", page_no, model)
                    continue
                if is_upstream_rate_limited(e) and upstream_attempts < 1:
                    upstream_attempts += 1
                    log.warning(
                        "page %d: %s upstream rate-limited — backoff 20s, retry",
                        page_no, model,
                    )
                    time.sleep(20)
                    continue
                if is_connection_error(e) and connection_attempts < 1:
                    connection_attempts += 1
                    log.warning(
                        "page %d: %s connection error — retrying",
                        page_no, model,
                    )
                    continue
                log.warning(
                    "page %d: %s failed (%s: %.120s); next model",
                    page_no, model, type(e).__name__, str(e),
                )
                break
    log.warning("page %d: all structure models exhausted, page skipped", page_no)
    return None


def _parse_iso_date(s):
    if not s or not isinstance(s, str):
        return None
    try:
        return date.fromisoformat(s[:10])
    except ValueError:
        try:
            return datetime.strptime(s, "%d.%m.%Y").date()
        except ValueError:
            return None


def _build_order_facts(merged: dict, fallback_number: str) -> OrderFacts:
    students_raw = merged.get("students") or []
    students = [
        StudentAssignment(
            full_name=str(s.get("full_name") or ""),
            group=s.get("group"),
            record_book_number=s.get("record_book_number"),
            course=s.get("course") if isinstance(s.get("course"), int) else None,
            location=PracticeLocation(
                organization=s.get("location_organization"),
                address=s.get("location_address"),
            ),
            supervisor=Supervisor(
                full_name=s.get("supervisor_name"),
                position=s.get("supervisor_position"),
                department=s.get("supervisor_department"),
            ),
        )
        for s in students_raw
        if s.get("full_name")
    ]

    return OrderFacts(
        number=str(merged.get("order_number") or fallback_number),
        issue_date=_parse_iso_date(merged.get("issue_date")),
        practice_start=_parse_iso_date(merged.get("practice_start")),
        practice_end=_parse_iso_date(merged.get("practice_end")),
        program_code=merged.get("program_code") or None,
        program_name=merged.get("program_name") or None,
        practice_type=merged.get("practice_type") or None,
        faculty=merged.get("faculty") or None,
        dean=merged.get("dean") or None,
        approved_at=_parse_iso_date(merged.get("approved_at")),
        students=students,
    )


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()
