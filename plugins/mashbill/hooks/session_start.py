#!/usr/bin/env python3
"""SessionStart hook for Novel — surface VISION + recent DECISIONS.

Prints the project essence (VISION.md first sentence) and the last 5
DECISIONS.md entries to additionalContext so every Novel session begins
with the user's anchor in the assistant's working set.

Doc homes (2026-07-10 public-repository consolidation):
  - VISION.md          → the public novel-ai docs/ canon, mirrored into plugin docs/
  - DECISIONS.md       → the installed plugin's docs/ directory
  - NEXT_SESSION.md    → the installed plugin's docs/ directory
The installed plugin mirror keeps SessionStart self-contained outside the source checkout.

Cross-platform (macOS, Linux, Windows) — pure Python stdlib only.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path


def find_plugin_root() -> Path | None:
    """Locate the Mashbill plugin directory holding docs/DECISIONS.md."""
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if plugin_root:
        candidate = Path(plugin_root)
        if (candidate / "docs" / "DECISIONS.md").exists():
            return candidate
    # Fallback: the hook lives at <plugin>/hooks/session_start.py
    here = Path(__file__).resolve()
    candidate = here.parent.parent
    if (candidate / "docs" / "DECISIONS.md").exists():
        return candidate
    return None


def find_vision() -> Path | None:
    """Find the nearest docs/VISION.md, including the installed-plugin mirror."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        vision = parent / "docs" / "VISION.md"
        if vision.exists():
            return vision
    return None


def read_vision_essence(vision_path: Path | None) -> str:
    """Extract the bolded one-sentence essence from Korean or English VISION.md."""
    if vision_path is None or not vision_path.exists():
        return "(VISION.md not found)"
    text = vision_path.read_text(encoding="utf-8")
    # The essence is the first **bolded** block after the essence heading.
    match = re.search(r"##\s*(?:본질|Essence).*?\*\*(.*?)\*\*", text, re.DOTALL)
    if match:
        return re.sub(r"\s+", " ", match.group(1)).strip()
    return "(essence sentence not found in VISION.md)"


def read_recent_decisions(plugin_root: Path | None, n: int = 5) -> list[str]:
    """Return the headings of the last N DECISIONS entries."""
    if plugin_root is None:
        return ["(DECISIONS.md not found)"]
    decisions_path = plugin_root / "docs" / "DECISIONS.md"
    if not decisions_path.exists():
        return ["(DECISIONS.md not found)"]
    text = decisions_path.read_text(encoding="utf-8")
    headings = re.findall(r"^### (D-\d{4}-\d{2}-\d{2}-[A-Z]+ — .+)$", text, re.MULTILINE)
    if not headings:
        return ["(no decisions found)"]
    # Entries are newest-first in the log, so the most recent are at the top.
    return headings[:n]


def read_next_session_queue(plugin_root: Path | None) -> list[tuple[str, str]]:
    """Return [(trigger_keyword, short_title)] for every active queue item."""
    if plugin_root is None:
        return []
    next_path = plugin_root / "docs" / "NEXT_SESSION.md"
    if not next_path.exists():
        return []
    text = next_path.read_text(encoding="utf-8")
    active_match = re.search(
        r"^## Active queue\s*\n(.*?)(?=^## Completed|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if not active_match:
        return []
    active_section = active_match.group(1)
    items = re.findall(
        r"^###\s+`([^`]+)`\s+—\s+(.+)$",
        active_section,
        re.MULTILINE,
    )
    return items


def main() -> int:
    plugin_root = find_plugin_root()
    vision_path = find_vision()
    if plugin_root is None and vision_path is None:
        # Silently no-op outside a Novel context
        print(json.dumps({"continue": True}))
        return 0

    essence = read_vision_essence(vision_path)
    recent = read_recent_decisions(plugin_root, n=5)
    decisions_source = (
        str((plugin_root / "docs" / "DECISIONS.md").resolve())
        if plugin_root is not None
        else "mashbill/docs/DECISIONS.md"
    )
    additional_context_lines = [
        "# Novel session anchor",
        "",
        "**Novel's essence (read this first, every session):**",
        "",
        f"> {essence}",
        "",
        "Source of truth: public `novel-ai/docs/` (map: `index.md`; essence: `VISION.md`; "
        "meaning: `concepts/`; behavior: `specs/`). Three phases: Discovery (Foundation) "
        "→ Retention (anchor) → Execution (Actors / Services / Feature) with "
        "AICollaboration cross-cutting.",
        "",
        "**Recent decisions (last 5):**",
        "",
    ]
    for d in recent:
        additional_context_lines.append(f"- `{d}`")
    additional_context_lines.extend(
        [
            "",
            f"Source: `{decisions_source}`. Always read the full entry before "
            "re-proposing related work.",
        ]
    )

    additional_context_lines.extend(
        [
            "",
            "**Runtime contract:**",
            "- Novel project data lives under the user's `.noory/novel/` directory.",
            "- Pass the current workspace as `project_path` to Mashbill MCP tools.",
            "- Prefer `update_node` for one node; use `update_canvas` for a full canvas.",
            "- Publishing format-F snapshots is explicit and never auto-committed.",
            "- The public Mashbill plugin is headless; it does not bundle the commercial UI.",
            "",
            "Use the bundled `mashbill-help`, `mashbill-new-project`, "
            "`mashbill-new-sketch`, and `mashbill-read-sketch` skills for workflows.",
        ]
    )
    additional_context = "\n".join(additional_context_lines)

    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": additional_context,
        }
    }
    print(json.dumps(output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
