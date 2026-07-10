"""Commercial-release licence audit (Track 2.6, D-2026-06-10-F).

Scans both halves of the shipped product for copyleft licences that would
block proprietary bundling (TECH_REVIEW sequence step 6):

  engine — pip-licenses over the plot dev env (GPL / AGPL / LGPL fail)
  viewer — license-checker over production npm deps (--failOn)

Run from `mashbill/`:

    uv run python scripts/license_audit.py

Exit 0 = clean. Exit 1 = a NEW copyleft / unknown licence appeared — resolve
or consciously allowlist it below (with a verified reason, never silently).
Wire into CI when the repo grows a pipeline (ROADMAP Track 2.6 note).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PLOT = Path(__file__).resolve().parent.parent

# Verified-by-hand exceptions. Key = package name, value = the reason the
# hit is acceptable. NEVER add an entry without checking the upstream
# licence text.
ALLOWLIST: dict[str, str] = {
    # Tri-licensed "BSD or GPL or Public Domain" — we elect the BSD terms.
    "docutils": "tri-licensed; BSD option elected",
    # Ships no licence classifier in metadata; upstream repo is Apache-2.0
    # (github.com/mosquito/caio). Re-verify on version bumps.
    "caio": "metadata gap; upstream Apache-2.0",
}

COPYLEFT = ("GPL", "AGPL", "LGPL")


def audit_engine() -> list[str]:
    out = subprocess.run(
        ["uv", "run", "--with", "pip-licenses", "pip-licenses", "--format=json"],
        cwd=PLOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    problems: list[str] = []
    for row in json.loads(out):
        name, lic = row["Name"], row["License"]
        if name in ALLOWLIST:
            continue
        if any(k in lic for k in COPYLEFT) or lic == "UNKNOWN":
            problems.append(f"engine: {name} — {lic}")
    return problems


def audit_viewer() -> list[str]:
    result = subprocess.run(
        [
            "npx",
            "--yes",
            "license-checker",
            "--production",
            "--excludePrivatePackages",
            "--failOn",
            ";".join(COPYLEFT),
        ],
        cwd=PLOT / "viewer",
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return [f"viewer: license-checker failed:\n{result.stdout}\n{result.stderr}"]
    return []


def main() -> int:
    problems = audit_engine() + audit_viewer()
    if problems:
        print("LICENCE AUDIT FAILED:")
        for p in problems:
            print(" !!", p)
        return 1
    print("licence audit clean (engine + viewer production deps)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
