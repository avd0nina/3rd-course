"""Load all regulation ontologies from `regulations/` into a single owlready2 World."""

from __future__ import annotations

from pathlib import Path

from owlready2 import Ontology, World


def load_regulations(regulations_dir: Path) -> tuple[World, list[Ontology]]:
    """Load every `*.owl` file in the directory into a fresh World.

    Returns (world, ontologies). The first ontology is treated as the primary one.
    """
    world = World()
    files = sorted(regulations_dir.glob("*.owl"))
    if not files:
        raise FileNotFoundError(f"No .owl files found in {regulations_dir}")
    ontologies: list[Ontology] = []
    for f in files:
        onto = world.get_ontology(f.absolute().as_uri()).load()
        ontologies.append(onto)
    return world, ontologies
