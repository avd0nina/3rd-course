"""Run the reasoner and apply rule checks on the injected ontology."""

from __future__ import annotations

import logging
from datetime import date, datetime
from pathlib import Path
from uuid import uuid4

from owlready2 import Ontology, sync_reasoner_hermit

from src.core.fact_injector import _InjectedRefs, inject
from src.core.loader import load_regulations
from src.core.report import (
    CheckReport,
    OrderMeta,
    ReportRule,
    ReportViolation,
)
from src.extractors.models import OrderFacts

log = logging.getLogger(__name__)

REGULATIONS_DIR = Path(__file__).resolve().parents[2] / "regulations"


def _parse_iso_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s).date() if "T" in s else date.fromisoformat(s)
    except ValueError:
        return None


def _read_rules_from_ontology(onto: Ontology) -> dict[str, ReportRule]:
    rules: dict[str, ReportRule] = {}
    for ind in onto.ViolationRule.instances():
        rid = ind.ruleId
        if not rid:
            continue
        rules[rid] = ReportRule(
            id=rid,
            name=ind.ruleName or "",
            description=ind.ruleDescription or "",
            source=ind.ruleSource,
        )
    return rules


def _ensure_java_on_path() -> None:
    """Auto-discover a JDK installed under `~/.jdk/...` (e.g. via install-jdk)
    and prepend its bin/ to PATH so HermiT can spawn `java`."""
    import os
    import shutil
    from pathlib import Path

    if shutil.which("java"):
        return
    jdk_root = Path.home() / ".jdk"
    if not jdk_root.is_dir():
        return
    for entry in jdk_root.iterdir():
        candidate = entry / "bin"
        if (candidate / "java").is_file():
            os.environ["PATH"] = f"{candidate}:{os.environ.get('PATH', '')}"
            return


def _try_run_reasoner(world) -> tuple[bool, str | None]:
    """Run HermiT. Return (consistent, error_message)."""
    _ensure_java_on_path()
    try:
        with world:
            sync_reasoner_hermit(infer_property_values=False)
        return True, None
    except OSError as e:
        # Java not available — common in minimal environments.
        log.warning("HermiT reasoner unavailable: %s", e)
        return True, f"reasoner not run ({e.__class__.__name__}: {e})"
    except Exception as e:  # noqa: BLE001 — surface inconsistencies
        log.warning("Reasoner error: %s", e)
        msg = str(e)
        if "OWL2_MODE" in msg or "inconsistent" in msg.lower():
            return False, msg
        return True, f"reasoner error: {msg}"


def check(facts: OrderFacts, regulations_dir: Path = REGULATIONS_DIR) -> CheckReport:
    """End-to-end check: load ontology, inject facts, reason, apply rules."""
    world, ontologies = load_regulations(regulations_dir)
    onto = ontologies[0]
    rules = _read_rules_from_ontology(onto)

    refs = inject(onto, facts)

    consistent, reasoner_error = _try_run_reasoner(world)

    violations: list[ReportViolation] = []
    violations += _check_required_fields(refs)
    violations += _check_program_code(facts)
    violations += _check_dates_order(facts)
    violations += _check_lead_time(facts)
    violations += _check_one_supervisor(refs)
    violations += _check_unique_record_books(refs)
    violations += _check_practice_type(facts)

    meta = OrderMeta(
        number=facts.number,
        issue_date=facts.issue_date,
        practice_start=facts.practice_start,
        practice_end=facts.practice_end,
        program_code=facts.program_code,
        program_name=facts.program_name,
        practice_type=facts.practice_type,
        student_count=len(facts.students),
    )

    return CheckReport(
        id=str(uuid4()),
        order=meta,
        rules=list(rules.values()),
        violations=violations,
        reasoner_consistent=consistent,
        reasoner_error=reasoner_error,
    )


# --- Individual rule checks ----------------------------------------------------

def _check_required_fields(refs: _InjectedRefs) -> list[ReportViolation]:
    out = []
    for r in refs.assignments:
        st = r.student_assignment
        missing: list[str] = []
        if not st.full_name:
            missing.append("ФИО")
        if not st.group:
            missing.append("группа")
        if not st.record_book_number:
            missing.append("номер зачётной книжки")
        if not (st.location.organization or st.location.structural_unit):
            missing.append("место практики")
        if not st.location.address:
            missing.append("адрес места практики")
        if not st.supervisor.full_name:
            missing.append("ФИО руководителя")
        if not st.supervisor.department:
            missing.append("кафедра руководителя")
        if missing:
            out.append(
                ReportViolation(
                    rule_id="R-01",
                    severity="error",
                    message=f"Не заполнены обязательные поля: {', '.join(missing)}",
                    assignment_index=r.index,
                    student_name=st.full_name,
                )
            )
    return out


_ALLOWED_PROGRAMS = {"09.03.01", "09.04.01"}


def _check_program_code(facts: OrderFacts) -> list[ReportViolation]:
    code = (facts.program_code or "").strip()
    if not code:
        return [
            ReportViolation(
                rule_id="R-02",
                severity="error",
                message="В приказе не указано направление подготовки",
            )
        ]
    if code not in _ALLOWED_PROGRAMS:
        return [
            ReportViolation(
                rule_id="R-02",
                severity="error",
                message=(
                    f"Направление подготовки «{code}» не входит в разрешённый список: "
                    f"{sorted(_ALLOWED_PROGRAMS)}"
                ),
            )
        ]
    return []


def _check_dates_order(facts: OrderFacts) -> list[ReportViolation]:
    if facts.practice_start and facts.practice_end and facts.practice_end < facts.practice_start:
        return [
            ReportViolation(
                rule_id="R-03",
                severity="error",
                message=(
                    f"Дата окончания практики ({facts.practice_end}) раньше даты начала "
                    f"({facts.practice_start})"
                ),
            )
        ]
    return []


def _check_lead_time(facts: OrderFacts) -> list[ReportViolation]:
    if not (facts.issue_date and facts.practice_start):
        return []
    delta_days = (facts.practice_start - facts.issue_date).days
    if delta_days < 30:
        return [
            ReportViolation(
                rule_id="R-04",
                severity="error",
                message=(
                    f"Между датой издания приказа ({facts.issue_date}) и началом практики "
                    f"({facts.practice_start}) всего {delta_days} дн., регламент требует "
                    f"не менее 30."
                ),
            )
        ]
    return []


def _check_one_supervisor(refs: _InjectedRefs) -> list[ReportViolation]:
    out = []
    for r in refs.assignments:
        if not r.student_assignment.supervisor.full_name:
            out.append(
                ReportViolation(
                    rule_id="R-05",
                    severity="error",
                    message="Студенту не назначен руководитель практики от НГУ",
                    assignment_index=r.index,
                    student_name=r.student_assignment.full_name,
                )
            )
    return out


def _check_unique_record_books(refs: _InjectedRefs) -> list[ReportViolation]:
    out = []
    seen: dict[str, int] = {}
    for r in refs.assignments:
        rb = r.student_assignment.record_book_number
        if not rb:
            continue
        if rb in seen:
            out.append(
                ReportViolation(
                    rule_id="R-06",
                    severity="error",
                    message=(
                        f"Дублирующийся номер зачётной книжки {rb} (также у студента в "
                        f"строке #{seen[rb]})"
                    ),
                    assignment_index=r.index,
                    student_name=r.student_assignment.full_name,
                )
            )
        else:
            seen[rb] = r.index
    return out


_ALLOWED_PRACTICE_TYPES = {"учебная", "производственная"}


def _check_practice_type(facts: OrderFacts) -> list[ReportViolation]:
    pt = (facts.practice_type or "").strip().lower()
    if not pt:
        return [
            ReportViolation(
                rule_id="R-07",
                severity="error",
                message="В приказе не указан тип практики (учебная / производственная)",
            )
        ]
    if not any(allowed in pt for allowed in _ALLOWED_PRACTICE_TYPES):
        return [
            ReportViolation(
                rule_id="R-07",
                severity="warning",
                message=(
                    f"Тип практики «{facts.practice_type}» не распознан как учебная или "
                    f"производственная"
                ),
            )
        ]
    return []
