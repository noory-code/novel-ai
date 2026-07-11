#!/usr/bin/env python3
"""Stop hook for Solera — remind, do not trap, when a leaf is left mid-flight.

If the active leaf is still ``doing`` when the session is ending, print a
reminder to run ``solera complete`` (or write feedback if blocked). This is
advisory only: it never blocks the stop, so it can't trap the loop.

Cross-platform — pure Python stdlib only, no import of the solera package.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _value(text: str, key: str) -> str:
    for line in text.splitlines():
        if line.startswith(f"{key}:"):
            return line.partition(":")[2].strip().strip('"').strip("'")
    return ""


def main() -> int:
    ws = Path.cwd() / ".noory" / "solera"
    progress = ws / "progress.md"
    if not progress.exists():
        return 0

    item_id = _value(progress.read_text(encoding="utf-8"), "item")
    if item_id in ("", "null", "None"):
        return 0

    item_file = ws / "items" / f"{item_id}.md"
    if item_file.exists() and _value(item_file.read_text(encoding="utf-8"), "status") == "doing":
        print(
            f"Solera: leaf {item_id} is still in progress (doing). Run `solera complete` "
            "to verify it, or write a feedback note (solera-feedback) if you are blocked.",
            file=sys.stderr,
        )
    return 0  # advisory only — never block the stop


if __name__ == "__main__":
    sys.exit(main())
