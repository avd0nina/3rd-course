"""HTTP routes: upload form, check action, report page (with background pipeline)."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.core.checker import check
from src.core.report import CheckReport, OrderMeta, load_report, save_report
from src.extractors.order_parser import parse_order

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
UPLOADS_DIR = ROOT / "var" / "uploads"
REPORTS_DIR = ROOT / "var" / "reports"
REGULATIONS_DIR = ROOT / "regulations"
DRAFTS_DIR = ROOT / "var" / "drafts"

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


@router.get("/")
def index(request: Request):
    regulations = sorted(p.stem for p in REGULATIONS_DIR.glob("*.owl"))
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "regulations": regulations,
            "llm_active": _llm_active(),
        },
    )


_ALLOWED_EXT = {".pdf", ".docx", ".txt"}


@router.post("/check")
async def check_order(file: UploadFile, background_tasks: BackgroundTasks):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Файл не передан")
    suffix = Path(file.filename).suffix.lower()
    if suffix not in _ALLOWED_EXT:
        raise HTTPException(
            status_code=400,
            detail=f"Поддерживаются только {', '.join(sorted(_ALLOWED_EXT))}",
        )

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    report_id = str(uuid4())
    pdf_path = UPLOADS_DIR / f"{report_id}{suffix}"
    with pdf_path.open("wb") as out:
        shutil.copyfileobj(file.file, out)

    pending = CheckReport(
        id=report_id,
        status="pending",
        order=OrderMeta(number=file.filename or "uploaded.pdf"),
    )
    save_report(pending, REPORTS_DIR / f"{report_id}.json")

    background_tasks.add_task(_run_pipeline, report_id, pdf_path)

    return RedirectResponse(url=f"/report/{report_id}", status_code=303)


@router.get("/ontology")
def ontology_list(request: Request, uploaded: int = 0, error: str = ""):
    """List downloadable .owl files (final regulations + LLM drafts)."""
    items = []
    for p in sorted(REGULATIONS_DIR.glob("*.owl")):
        items.append({"name": p.name, "kind": "final", "size": p.stat().st_size, "url": f"/ontology/final/{p.name}"})
    if DRAFTS_DIR.is_dir():
        for p in sorted(DRAFTS_DIR.glob("*.owl")):
            items.append({"name": p.name, "kind": "draft", "size": p.stat().st_size, "url": f"/ontology/draft/{p.name}"})
    return templates.TemplateResponse(
        request,
        "ontology.html",
        {"items": items, "uploaded": uploaded, "error": error},
    )


@router.get("/ontology/final/{name}")
def ontology_final(name: str):
    p = REGULATIONS_DIR / name
    if not p.is_file() or p.suffix != ".owl":
        raise HTTPException(status_code=404)
    return FileResponse(p, media_type="application/rdf+xml", filename=name)


@router.get("/ontology/draft/{name}")
def ontology_draft(name: str):
    p = DRAFTS_DIR / name
    if not p.is_file() or p.suffix != ".owl":
        raise HTTPException(status_code=404)
    return FileResponse(p, media_type="application/rdf+xml", filename=name)


@router.get("/ontology/workflow")
def ontology_workflow():
    p = ROOT / "docs" / "protege_workflow.md"
    if not p.is_file():
        raise HTTPException(status_code=404)
    return FileResponse(p, media_type="text/markdown; charset=utf-8", filename=p.name)


@router.get("/docs/onto-practice.pdf")
def project_doc_pdf():
    p = ROOT / "docs" / "onto-practice.pdf"
    if not p.is_file():
        raise HTTPException(status_code=404)
    return FileResponse(p, media_type="application/pdf", filename=p.name)


@router.get("/docs/onto-practice-source.zip")
def project_source_zip():
    p = ROOT / "docs" / "onto-practice-source.zip"
    if not p.is_file():
        raise HTTPException(status_code=404, detail="Архив не собран — запустите scripts/build_source_archive.py")
    return FileResponse(p, media_type="application/zip", filename=p.name)


_MAX_OWL_BYTES = 5 * 1024 * 1024  # 5 MB cap — onto files are tiny


@router.post("/ontology/upload")
async def ontology_upload(file: UploadFile):
    """Replace regulations/practice.owl with the uploaded file.

    Validates that the file actually loads as an OWL ontology before swap.
    Old version is moved to var/backups/ with timestamp so nothing is lost.
    """
    if not file.filename or not file.filename.lower().endswith(".owl"):
        return RedirectResponse(
            url="/ontology?error=Ожидался+.owl+файл", status_code=303,
        )

    REGULATIONS_DIR.mkdir(parents=True, exist_ok=True)
    tmp_path = REGULATIONS_DIR / "_uploading.owl"
    bytes_written = 0
    with tmp_path.open("wb") as out:
        while True:
            chunk = await file.read(64 * 1024)
            if not chunk:
                break
            bytes_written += len(chunk)
            if bytes_written > _MAX_OWL_BYTES:
                tmp_path.unlink(missing_ok=True)
                return RedirectResponse(
                    url="/ontology?error=Файл+больше+5+МБ", status_code=303,
                )
            out.write(chunk)

    try:
        from owlready2 import World

        world = World()
        world.get_ontology(tmp_path.absolute().as_uri()).load()
    except Exception as e:  # noqa: BLE001
        tmp_path.unlink(missing_ok=True)
        msg = f"Невалидный+OWL%3A+{type(e).__name__}"
        return RedirectResponse(url=f"/ontology?error={msg}", status_code=303)

    target = REGULATIONS_DIR / "practice.owl"
    if target.exists():
        from datetime import datetime
        backup_dir = ROOT / "var" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        target.replace(backup_dir / f"practice-{ts}.owl")
        log.info("backed up previous practice.owl to backups/practice-%s.owl", ts)

    tmp_path.replace(target)
    log.info("ontology replaced (%d bytes)", bytes_written)
    return RedirectResponse(url="/ontology?uploaded=1", status_code=303)


@router.get("/report/{report_id}")
def report_page(request: Request, report_id: str):
    src = REPORTS_DIR / f"{report_id}.json"
    if not src.exists():
        raise HTTPException(status_code=404, detail="Отчёт не найден")
    report = load_report(src)
    rule_index = {r.id: r for r in report.rules}
    return templates.TemplateResponse(
        request,
        "report.html",
        {
            "report": report,
            "rule_index": rule_index,
        },
    )


def _run_pipeline(report_id: str, pdf_path: Path) -> None:
    """Background job: parse PDF + run reasoner + save final report."""
    dest = REPORTS_DIR / f"{report_id}.json"
    try:
        log.info("[%s] parsing PDF", report_id)
        facts = parse_order(pdf_path)
        log.info("[%s] running reasoner + checks (%d students)", report_id, len(facts.students))
        report = check(facts)
        report.id = report_id
        report.status = "ready"
        save_report(report, dest)
        log.info(
            "[%s] done — %d violations, reasoner=%s",
            report_id, report.violation_count, "OK" if report.reasoner_consistent else "FAIL",
        )
    except Exception as e:  # noqa: BLE001
        log.exception("[%s] pipeline failed", report_id)
        existing = load_report(dest) if dest.exists() else CheckReport(
            id=report_id, status="error", order=OrderMeta(number="?")
        )
        existing.status = "error"
        existing.error_message = f"{type(e).__name__}: {e}"
        save_report(existing, dest)


def _llm_active() -> bool:
    import os

    return bool(os.getenv("OPENROUTER_API_KEYS") or os.getenv("OPENROUTER_API_KEY"))
