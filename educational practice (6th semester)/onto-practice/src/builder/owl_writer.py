"""Convert an OntologyDraft into an OWL file via owlready2."""

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

from src.builder.extractor import OntologyDraft

_RANGE_PY = {"string": str, "integer": int, "date": str}


def write_draft(draft: OntologyDraft, out_path: Path, iri: str) -> None:
    """Materialise the draft as a fresh `.owl` file at `out_path`."""
    onto = get_ontology(iri)
    with onto:
        ns_classes: dict[str, type] = {}
        for c in draft.classes:
            klass = type(c.name, (Thing,), {"namespace": onto})
            if c.label_ru:
                klass.label = [locstr(c.label_ru, lang="ru")]
            if c.comment_ru:
                klass.comment = [locstr(c.comment_ru, lang="ru")]
            ns_classes[c.name] = klass

        # ViolationRule + Violation as standard validation classes
        for extra in ("ViolationRule", "Violation"):
            if extra not in ns_classes:
                ns_classes[extra] = type(extra, (Thing,), {"namespace": onto})

        for op in draft.object_properties:
            bases: tuple = (ObjectProperty,)
            if op.functional:
                bases = (ObjectProperty, FunctionalProperty)
            prop = type(op.name, bases, {"namespace": onto})
            prop.domain = [ns_classes[op.domain]]
            prop.range = [ns_classes[op.range]]

        for dp in draft.data_properties:
            bases: tuple = (DataProperty,)
            if dp.functional:
                bases = (DataProperty, FunctionalProperty)
            prop = type(dp.name, bases, {"namespace": onto})
            prop.domain = [ns_classes[dp.domain]]
            prop.range = [_RANGE_PY.get(dp.range, str)]

        # rule metadata properties (ruleId, ruleName, ruleDescription, ruleSource)
        for rule_prop_name in ("ruleId", "ruleName", "ruleDescription", "ruleSource"):
            type(
                rule_prop_name,
                (DataProperty, FunctionalProperty),
                {"namespace": onto, "domain": [ns_classes["ViolationRule"]], "range": [str]},
            )

    # ABox: rules
    for r in draft.rules:
        ind = onto.ViolationRule(f"rule_{r.id.replace('-', '_')}")
        ind.ruleId = r.id
        ind.ruleName = r.name
        ind.ruleDescription = r.description
        ind.ruleSource = r.source

    out_path.parent.mkdir(parents=True, exist_ok=True)
    onto.save(file=str(out_path), format="rdfxml")
