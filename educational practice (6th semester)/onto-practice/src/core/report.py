"""Pydantic schemas for the compliance report and helpers to serialise it."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class ReportRule(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    description: str
    source: str | None = None


class ReportViolation(BaseModel):
    model_config = ConfigDict(extra="ignore")

    rule_id: str
    message: str
    severity: str = "error"  # "error" | "warning"
    assignment_index: int | None = None
    student_name: str | None = None


class OrderMeta(BaseModel):
    model_config = ConfigDict(extra="ignore")

    number: str
    issue_date: date | None = None
    practice_start: date | None = None
    practice_end: date | None = None
    program_code: str | None = None
    program_name: str | None = None
    practice_type: str | None = None
    student_count: int = 0


class CheckReport(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    status: str = "ready"  # "pending" | "ready" | "error"
    error_message: str | None = None
    regulation_id: str = "practice"
    order: OrderMeta
    rules: list[ReportRule] = Field(default_factory=list)
    violations: list[ReportViolation] = Field(default_factory=list)
    reasoner_used: str = "HermiT"
    reasoner_consistent: bool = True
    reasoner_error: str | None = None

    @property
    def violation_count(self) -> int:
        return len(self.violations)

    @property
    def has_violations(self) -> bool:
        return bool(self.violations)

    @property
    def is_pending(self) -> bool:
        return self.status == "pending"

    @property
    def is_error(self) -> bool:
        return self.status == "error"


def save_report(report: CheckReport, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(report.model_dump_json(indent=2), encoding="utf-8")


def load_report(src: Path) -> CheckReport:
    data = json.loads(src.read_text(encoding="utf-8"))
    return CheckReport.model_validate(data)
