"""Cross-file workspace audit — the capstone guard for the WorkItem tree.

Per-file parsing fails fast on its own. This audit checks the relations between
items: every referenced child has a parseable file, no child has two parents,
there are no cycles, and the ``progress.md`` pointer points at something that
exists. It collects problems and returns them rather than raising, so a caller
can report every issue at once. (An unreferenced item is not a problem — it is
simply a root of the forest.)
"""

from __future__ import annotations

from dataclasses import dataclass

from .errors import FormatError
from .formats import WorkItem
from .workspace import Workspace


@dataclass(frozen=True)
class Problem:
    """One integrity problem found by the audit."""

    kind: str
    detail: str


def audit_workspace(ws: Workspace) -> list[Problem]:
    """Return every referential-integrity problem in the workspace (possibly empty)."""
    problems: list[Problem] = []

    parsed: dict[str, WorkItem] = {}
    for item_id in ws.list_items():
        try:
            parsed[item_id] = ws.load_item(item_id)
        except FormatError as exc:
            problems.append(Problem("malformed-item", f"{item_id}: cannot parse ({exc})"))

    parent_of: dict[str, str] = {}
    for item_id, item in parsed.items():
        for child in item.children:
            if child not in parsed and not ws.item_path(child).exists():
                problems.append(
                    Problem("missing-child", f"{item_id} references {child} which has no file")
                )
            if child in parent_of:
                problems.append(
                    Problem(
                        "multi-parent",
                        f"{child} is a child of both {parent_of[child]} and {item_id}",
                    )
                )
            else:
                parent_of[child] = item_id

    problems.extend(_find_cycles(parsed, parent_of))
    problems.extend(_audit_pointer(ws, parsed))
    return problems


def _find_cycles(parsed: dict[str, WorkItem], parent_of: dict[str, str]) -> list[Problem]:
    reported: set[str] = set()
    out: list[Problem] = []
    for start in parsed:
        seen = {start}
        current = parent_of.get(start)
        while current is not None:
            if current in seen:
                if current not in reported:
                    reported.add(current)
                    out.append(Problem("cycle", f"cycle detected through {current}"))
                break
            seen.add(current)
            current = parent_of.get(current)
    return out


def _audit_pointer(ws: Workspace, parsed: dict[str, WorkItem]) -> list[Problem]:
    if not ws.progress_path.exists():
        return []
    try:
        prog = ws.load_progress()
    except FormatError as exc:
        return [Problem("malformed-progress", f"progress.md: cannot parse ({exc})")]
    if prog.item is not None and prog.item not in parsed and not ws.item_path(prog.item).exists():
        return [Problem("dangling-pointer", f"progress points at {prog.item} which does not exist")]
    return []
