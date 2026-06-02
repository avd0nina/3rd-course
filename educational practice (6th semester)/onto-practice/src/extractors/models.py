"""Pydantic schemas for parsed practice order data."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class Supervisor(BaseModel):
    model_config = ConfigDict(extra="ignore")

    full_name: str | None = None
    position: str | None = None
    department: str | None = None


class PracticeLocation(BaseModel):
    model_config = ConfigDict(extra="ignore")

    organization: str | None = None
    structural_unit: str | None = None
    address: str | None = None


class StudentAssignment(BaseModel):
    """One row in the order: a student directed to practice."""

    model_config = ConfigDict(extra="ignore")

    full_name: str
    group: str | None = None
    record_book_number: str | None = None
    course: int | None = None
    location: PracticeLocation = Field(default_factory=PracticeLocation)
    supervisor: Supervisor = Field(default_factory=Supervisor)


class OrderFacts(BaseModel):
    """Top-level structure extracted from the PDF order."""

    model_config = ConfigDict(extra="ignore")

    number: str
    issue_date: date | None = None
    practice_start: date | None = None
    practice_end: date | None = None
    program_code: str | None = None  # "09.03.01"
    program_name: str | None = None
    practice_type: str | None = None  # "учебная" / "производственная"
    practice_subtype: str | None = None  # "эксплуатационная" и т.п.
    faculty: str | None = None
    dean: str | None = None
    approved_at: date | None = None
    students: list[StudentAssignment] = Field(default_factory=list)
