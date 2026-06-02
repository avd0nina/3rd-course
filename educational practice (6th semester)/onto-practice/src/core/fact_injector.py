"""Inject parsed OrderFacts into the ontology as individuals."""

from __future__ import annotations

from owlready2 import Ontology

from src.extractors.models import OrderFacts, StudentAssignment


def _safe_iri(s: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in s).strip("_") or "x"


def inject(onto: Ontology, facts: OrderFacts) -> _InjectedRefs:
    """Create individuals for the given OrderFacts inside `onto`.

    Returns a small struct with references to the created order and assignments
    so the checker can iterate them deterministically.
    """
    Order = onto.Order
    Assignment = onto.Assignment
    Student = onto.Student
    Supervisor = onto.Supervisor
    PracticeLocation = onto.PracticeLocation
    Department = onto.Department

    order = Order(f"order_{_safe_iri(facts.number)}")
    order.orderNumber = facts.number
    if facts.issue_date:
        order.orderDate = facts.issue_date.isoformat()
    if facts.practice_start:
        order.practiceStart = facts.practice_start.isoformat()
    if facts.practice_end:
        order.practiceEnd = facts.practice_end.isoformat()
    if facts.program_code:
        order.programCode = facts.program_code
    if facts.program_name:
        order.programName = facts.program_name
    if facts.practice_type:
        order.practiceType = facts.practice_type

    assignments = []
    for idx, st in enumerate(facts.students, start=1):
        a, ref = _make_assignment(
            onto,
            Assignment,
            Student,
            Supervisor,
            PracticeLocation,
            Department,
            st,
            order_iri=_safe_iri(facts.number),
            idx=idx,
        )
        order.hasAssignment.append(a)
        assignments.append(ref)

    return _InjectedRefs(order=order, assignments=assignments)


def _make_assignment(
    onto: Ontology,
    Assignment,
    Student,
    Supervisor,
    PracticeLocation,
    Department,
    st: StudentAssignment,
    order_iri: str,
    idx: int,
) -> tuple[object, _AssignmentRef]:
    base = f"{order_iri}_{idx}"

    assignment = Assignment(f"assignment_{base}")

    student = Student(f"student_{base}")
    student.studentName = st.full_name
    if st.group:
        student.studentGroup = st.group
    if st.record_book_number:
        student.recordBookNumber = st.record_book_number
    if st.course is not None:
        student.studentCourse = st.course
    assignment.forStudent = student

    if any([st.location.organization, st.location.address, st.location.structural_unit]):
        loc = PracticeLocation(f"loc_{base}")
        if st.location.organization:
            loc.locationOrganization = st.location.organization
        if st.location.address:
            loc.locationAddress = st.location.address
        assignment.atLocation = loc
    else:
        loc = None

    sup = None
    if st.supervisor.full_name:
        sup = Supervisor(f"sup_{base}")
        sup.supervisorName = st.supervisor.full_name
        if st.supervisor.position:
            sup.supervisorPosition = st.supervisor.position
        if st.supervisor.department:
            dept = Department(f"dept_{base}")
            dept.departmentName = st.supervisor.department
            sup.inDepartment = dept
        assignment.supervisedBy = sup

    return assignment, _AssignmentRef(
        index=idx,
        student_assignment=st,
        ind_assignment=assignment,
        ind_student=student,
        ind_location=loc,
        ind_supervisor=sup,
    )


class _AssignmentRef:
    """Lightweight handle from injection — used by the checker."""

    __slots__ = (
        "index",
        "student_assignment",
        "ind_assignment",
        "ind_student",
        "ind_location",
        "ind_supervisor",
    )

    def __init__(
        self,
        index: int,
        student_assignment: StudentAssignment,
        ind_assignment,
        ind_student,
        ind_location,
        ind_supervisor,
    ):
        self.index = index
        self.student_assignment = student_assignment
        self.ind_assignment = ind_assignment
        self.ind_student = ind_student
        self.ind_location = ind_location
        self.ind_supervisor = ind_supervisor


class _InjectedRefs:
    __slots__ = ("order", "assignments")

    def __init__(self, order, assignments: list[_AssignmentRef]):
        self.order = order
        self.assignments = assignments
