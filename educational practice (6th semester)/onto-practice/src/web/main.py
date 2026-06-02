"""FastAPI app entry point."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.web.routes import router

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def create_app() -> FastAPI:
    app = FastAPI(title="onto-practice", version="0.1.0")
    app.mount(
        "/static",
        StaticFiles(directory=str(Path(__file__).parent / "static")),
        name="static",
    )
    app.include_router(router)
    _mark_orphaned_pending_as_error()
    return app


def _mark_orphaned_pending_as_error() -> None:
    """Reports left in 'pending' from a previous process are abandoned."""
    from src.core.report import load_report, save_report

    reports_dir = ROOT / "var" / "reports"
    if not reports_dir.is_dir():
        return
    for f in reports_dir.glob("*.json"):
        try:
            r = load_report(f)
        except Exception:  # noqa: BLE001
            continue
        if r.status == "pending":
            r.status = "error"
            r.error_message = (
                "Обработка была прервана (сервер был перезапущен). "
                "Загрузите файл заново."
            )
            save_report(r, f)


app = create_app()
