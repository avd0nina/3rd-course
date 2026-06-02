"""CLI: build a draft ontology from a regulation PDF.

Usage:
    python scripts/build_ontology.py docs/source/onto/metod_rekomend_praktika.pdf
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from src.builder.extractor import extract_draft
from src.builder.owl_writer import write_draft
from src.builder.pdf_to_text import extract_text


def main() -> None:
    parser = argparse.ArgumentParser(description="Build draft ontology from regulation PDF")
    parser.add_argument("pdf", type=Path, help="Path to the regulation PDF")
    parser.add_argument(
        "-o",
        "--out",
        type=Path,
        default=ROOT / "var" / "drafts" / "practice.draft.owl",
        help="Output OWL file (default: var/drafts/practice.draft.owl)",
    )
    parser.add_argument(
        "--iri",
        default="http://onto-practice.local/practice.draft.owl",
        help="Ontology IRI",
    )
    args = parser.parse_args()

    if not args.pdf.exists():
        parser.error(f"PDF not found: {args.pdf}")

    print(f"reading {args.pdf}")
    text = extract_text(args.pdf)
    print(f"  text length: {len(text)} chars")

    print("extracting draft schema (LLM or stub depending on env)...")
    draft = extract_draft(text)
    print(
        f"  classes: {len(draft.classes)}, "
        f"obj_props: {len(draft.object_properties)}, "
        f"data_props: {len(draft.data_properties)}, "
        f"rules: {len(draft.rules)}"
    )

    print(f"writing {args.out}")
    write_draft(draft, args.out, args.iri)
    print(f"done: {args.out} ({args.out.stat().st_size} bytes)")
    print()
    print(
        "Next: open the draft in Protégé, refine class hierarchy / "
        "add SWRL rules, and save the final result as regulations/practice.owl"
    )


if __name__ == "__main__":
    main()
