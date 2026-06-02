"""Manually build the curated `regulations/practice.owl` ontology.

This script materialises the result of step T-005 (manual refinement that would
normally happen in Protégé). Run once; the produced file is committed.

Re-run: `python scripts/init_practice_ontology.py`.
"""

from __future__ import annotations

from pathlib import Path

from owlready2 import (
    DataProperty,
    FunctionalProperty,
    ObjectProperty,
    Thing,
    get_ontology,
    locstr,
)

ROOT = Path(__file__).resolve().parents[1]
OUT_FILE = ROOT / "regulations" / "practice.owl"
IRI = "http://onto-practice.local/practice.owl"


def build() -> None:
    onto = get_ontology(IRI)

    with onto:
        # --- Core domain classes -------------------------------------------------
        class Order(Thing):
            comment = [locstr("Приказ ректора о направлении на практику", lang="ru")]

        class Assignment(Thing):
            comment = [locstr("Запись о направлении конкретного студента на практику", lang="ru")]

        class Student(Thing):
            comment = [locstr("Обучающийся, направляемый на практику", lang="ru")]

        class Supervisor(Thing):
            comment = [locstr("Руководитель практики от университета (ППС)", lang="ru")]

        class PracticeLocation(Thing):
            comment = [locstr("Место прохождения практики", lang="ru")]

        class Department(Thing):
            comment = [locstr("Кафедра", lang="ru")]

        # --- Validation classes -------------------------------------------------
        class ViolationRule(Thing):
            comment = [locstr("Правило проверки соответствия регламенту", lang="ru")]

        class Violation(Thing):
            comment = [locstr("Зафиксированное нарушение правила в приказе", lang="ru")]

        # --- Object properties --------------------------------------------------
        class hasAssignment(ObjectProperty):
            domain = [Order]
            range = [Assignment]

        class forStudent(ObjectProperty, FunctionalProperty):
            domain = [Assignment]
            range = [Student]

        class atLocation(ObjectProperty, FunctionalProperty):
            domain = [Assignment]
            range = [PracticeLocation]

        class supervisedBy(ObjectProperty, FunctionalProperty):
            domain = [Assignment]
            range = [Supervisor]

        class inDepartment(ObjectProperty, FunctionalProperty):
            domain = [Supervisor]
            range = [Department]

        class hasViolation(ObjectProperty):
            domain = [Order]
            range = [Violation]

        class violatesRule(ObjectProperty, FunctionalProperty):
            domain = [Violation]
            range = [ViolationRule]

        class concernsAssignment(ObjectProperty):
            domain = [Violation]
            range = [Assignment]

        # --- Data properties ----------------------------------------------------
        class orderNumber(DataProperty, FunctionalProperty):
            domain = [Order]
            range = [str]

        class orderDate(DataProperty, FunctionalProperty):
            domain = [Order]
            range = [str]  # ISO date as str (owlready2 + xsd:date is finicky)

        class practiceStart(DataProperty, FunctionalProperty):
            domain = [Order]
            range = [str]

        class practiceEnd(DataProperty, FunctionalProperty):
            domain = [Order]
            range = [str]

        class programCode(DataProperty, FunctionalProperty):
            domain = [Order]
            range = [str]

        class programName(DataProperty, FunctionalProperty):
            domain = [Order]
            range = [str]

        class practiceType(DataProperty, FunctionalProperty):
            domain = [Order]
            range = [str]

        class studentName(DataProperty, FunctionalProperty):
            domain = [Student]
            range = [str]

        class studentGroup(DataProperty, FunctionalProperty):
            domain = [Student]
            range = [str]

        class recordBookNumber(DataProperty, FunctionalProperty):
            domain = [Student]
            range = [str]

        class studentCourse(DataProperty, FunctionalProperty):
            domain = [Student]
            range = [int]

        class locationOrganization(DataProperty, FunctionalProperty):
            domain = [PracticeLocation]
            range = [str]

        class locationAddress(DataProperty, FunctionalProperty):
            domain = [PracticeLocation]
            range = [str]

        class supervisorName(DataProperty, FunctionalProperty):
            domain = [Supervisor]
            range = [str]

        class supervisorPosition(DataProperty, FunctionalProperty):
            domain = [Supervisor]
            range = [str]

        class departmentName(DataProperty, FunctionalProperty):
            domain = [Department]
            range = [str]

        class violationMessage(DataProperty, FunctionalProperty):
            domain = [Violation]
            range = [str]

        class violationSeverity(DataProperty, FunctionalProperty):
            domain = [Violation]
            range = [str]

        class ruleId(DataProperty, FunctionalProperty):
            domain = [ViolationRule]
            range = [str]

        class ruleName(DataProperty, FunctionalProperty):
            domain = [ViolationRule]
            range = [str]

        class ruleDescription(DataProperty, FunctionalProperty):
            domain = [ViolationRule]
            range = [str]

        class ruleSource(DataProperty, FunctionalProperty):
            domain = [ViolationRule]
            range = [str]

    # --- Rule individuals (ABox) ----------------------------------------------
    rule_specs = [
        (
            "R-01",
            "Заполнение обязательных полей",
            "У каждого студента в приказе должны быть указаны: ФИО, группа, "
            "номер зачётной книжки, место практики (организация и адрес), "
            "руководитель и его кафедра.",
            "Приложения 1–3, стр. 28–33",
        ),
        (
            "R-02",
            "Корректное направление подготовки",
            "Приказ должен быть оформлен по направлению 09.03.01 «Информатика и "
            "вычислительная техника» (бакалавриат) или 09.04.01 (магистратура).",
            "стр. 2",
        ),
        (
            "R-03",
            "Корректные сроки практики",
            "Дата начала практики должна предшествовать дате окончания.",
            "здравый смысл",
        ),
        (
            "R-04",
            "Минимальный срок подготовки приказа",
            "Между датой издания приказа и датой начала практики должно быть не "
            "менее 30 календарных дней (приказ готовится не позднее чем за 1 "
            "месяц до начала практики).",
            "стр. 9",
        ),
        (
            "R-05",
            "Назначен один руководитель от НГУ",
            "Каждому студенту в приказе должен быть назначен ровно один "
            "руководитель практики со стороны НГУ из числа ППС.",
            "стр. 6",
        ),
        (
            "R-06",
            "Уникальность зачётных книжек",
            "Номера зачётных книжек студентов в приказе должны быть уникальны.",
            "здравый смысл",
        ),
        (
            "R-07",
            "Указан тип практики",
            "В приказе должен быть указан вид практики: учебная или производственная.",
            "стр. 3",
        ),
    ]

    for rid, rname, rdesc, rsrc in rule_specs:
        ind = onto.ViolationRule(f"rule_{rid.replace('-', '_')}")
        ind.ruleId = rid
        ind.ruleName = rname
        ind.ruleDescription = rdesc
        ind.ruleSource = rsrc

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    onto.save(file=str(OUT_FILE), format="rdfxml")
    print(f"wrote {OUT_FILE} ({OUT_FILE.stat().st_size} bytes)")


if __name__ == "__main__":
    build()
