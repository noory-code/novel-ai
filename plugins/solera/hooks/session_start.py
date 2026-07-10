#!/usr/bin/env python3
"""SessionStart hook for Solera — orient the agent in the active workspace.

Reads ``./.noory/solera/`` in the project and, if work is in progress, surfaces
the active leaf (its goal and gate) plus the next command to additionalContext,
so a session never starts blind to where the loop left off. No-op outside a
Solera workspace.

Cross-platform (macOS, Linux, Windows) — pure Python stdlib only, no import of
the solera package (the hook must run even when nothing is installed).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _frontmatter(text: str) -> dict[str, str]:
    """Tiny ``key: value`` frontmatter reader (flat scalars only)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    out: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" in line and not line.startswith((" ", "-")):
            key, _, value = line.partition(":")
            out[key.strip()] = value.strip().strip('"').strip("'")
    return out


def _body(text: str) -> str:
    parts = text.split("---", 2)
    return parts[2].strip() if len(parts) >= 3 else ""


def _emit(context: str | None) -> int:
    if context is None:
        print(json.dumps({"continue": True}))
    else:
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "SessionStart",
                        "additionalContext": context,
                    }
                }
            )
        )
    return 0


def main() -> int:
    ws = Path.cwd() / ".noory" / "solera"
    progress = ws / "progress.md"
    if not progress.exists():
        return _emit(None)  # not a Solera workspace

    item_id = _frontmatter(progress.read_text(encoding="utf-8")).get("item", "")
    if item_id in ("", "null", "None"):
        return _emit(
            "# Solera\n\nA Solera workspace is present but no leaf is in progress. "
            "Run `solera next` to start the next leaf, or `solera plan` / `solera add` to plan."
        )

    item_file = ws / "items" / f"{item_id}.md"
    if not item_file.exists():
        return _emit(f"# Solera\n\nActive pointer is `{item_id}` but its file is missing. "
                     "Run `solera status` to check the workspace.")

    text = item_file.read_text(encoding="utf-8")
    fm = _frontmatter(text)
    context = (
        "# Solera — resume the loop\n\n"
        f"Active leaf: **{item_id}** ({fm.get('level', '?')}, {fm.get('status', '?')}).\n\n"
        f"Goal: {_body(text)}\n\n"
        f"Gate: `{fm.get('gate', '')}`\n\n"
        "Do the work, then run `solera complete`. If it is already done, "
        "`solera next` moves on. Solera plans and verifies; you do the building."
    )
    return _emit(context)


if __name__ == "__main__":
    sys.exit(main())
