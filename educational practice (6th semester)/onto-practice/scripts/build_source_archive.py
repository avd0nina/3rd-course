"""Bundle the project sources into docs/onto-practice-source.zip.

Uses `git archive HEAD` so the snapshot is exactly the committed state —
.gitignore'd content (var/, .venv/, .env, caches) stays out automatically,
no manual exclusion lists.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "onto-practice-source.zip"


def build() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.unlink(missing_ok=True)
    cmd = [
        "git", "archive",
        "--format=zip",
        "--prefix=onto-practice/",
        f"--output={OUT}",
        "HEAD",
    ]
    res = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if res.returncode != 0:
        print(res.stderr, file=sys.stderr)
        sys.exit(res.returncode)
    size = OUT.stat().st_size
    print(f"wrote {OUT} ({size} bytes)")


if __name__ == "__main__":
    build()
