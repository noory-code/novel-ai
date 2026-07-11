"""FastMCP adapter over Solera's deterministic file-based core.

The MCP layer owns no workflow state and makes no planning decisions. It only
maps host-neutral tool calls onto the same functions used by the CLI and skills.
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from .audit import audit_workspace
from .formats import Feedback, Retrospective
from .intake import import_release, load_imported_elements
from .planning import create_item
from .repin import propose_repin, reopen_items
from .supervisor import complete, instruction, start_next
from .workspace import Workspace

mcp = FastMCP(
    "solera",
    instructions=(
        "Solera stores an executable work tree under .noory/solera. Plan or add "
        "items, ask for exactly one next leaf, and complete that leaf only after "
        "the implementation is ready for its deterministic gate. Re-pin is a "
        "two-step operation: inspect the proposal first, then explicitly apply it."
    ),
)


def _workspace(project_root: str) -> Workspace:
    return Workspace(Path(project_root).expanduser().resolve() / ".noory" / "solera")


@mcp.tool()
def plan_work(project_root: str, goal: str, level: str = "story") -> dict[str, Any]:
    """Create a root work container. Add gated child leaves before asking for next work."""
    item = create_item(_workspace(project_root), level, goal)
    return item.model_dump()


@mcp.tool()
def add_work_item(
    project_root: str,
    parent: str,
    goal: str,
    level: str = "action",
    gate: str = "",
    realizes: list[str] | None = None,
) -> dict[str, Any]:
    """Add a child to ``parent``. Pass a deterministic command in ``gate`` for a leaf."""
    item = create_item(
        _workspace(project_root),
        level,
        goal,
        parent=parent,
        gate=gate,
        realizes=realizes,
    )
    return item.model_dump()


@mcp.tool()
def next_work_item(project_root: str) -> dict[str, Any]:
    """Select or resume the next open leaf and return its complete execution instruction."""
    ws = _workspace(project_root)
    item_id = start_next(ws)
    if item_id is None:
        return {"item": None, "instruction": ""}
    return {
        "item": ws.load_item(item_id).model_dump(),
        "instruction": instruction(ws, item_id),
    }


@mcp.tool()
def complete_current(project_root: str, timeout_seconds: float = 120.0) -> dict[str, Any]:
    """Run the current leaf's stored gate; mark it done only when the gate passes."""
    root = Path(project_root).expanduser().resolve()
    ws = _workspace(project_root)
    progress = ws.load_progress()
    if progress.item is None:
        raise ValueError("no Solera work item is currently active")
    result = complete(ws, progress.item, cwd=root, timeout=timeout_seconds)
    return asdict(result)


@mcp.tool()
def workspace_status(project_root: str) -> dict[str, Any]:
    """Return the active pointer, all work items, and every integrity problem."""
    ws = _workspace(project_root)
    pointer = ws.load_progress().item if ws.progress_path.is_file() else None
    return {
        "current": pointer,
        "items": [ws.load_item(item_id).model_dump() for item_id in ws.list_items()],
        "problems": [asdict(problem) for problem in audit_workspace(ws)],
    }


@mcp.tool()
def import_spec(project_root: str, source: str, label: str) -> dict[str, Any]:
    """Import one immutable format-F service release into ``specs/{label}``."""
    return import_release(
        _workspace(project_root), Path(source).expanduser().resolve(), label=label
    )


@mcp.tool()
def propose_spec_repin(project_root: str, old_label: str, new_label: str) -> dict[str, Any]:
    """Read two imported releases and propose stale items without changing work state."""
    ws = _workspace(project_root)
    return propose_repin(
        ws,
        load_imported_elements(ws, old_label),
        load_imported_elements(ws, new_label),
    )


@mcp.tool()
def apply_spec_repin(project_root: str, old_label: str, new_label: str) -> dict[str, Any]:
    """Reopen exactly the stale items in a previously reviewed re-pin proposal."""
    proposal = propose_spec_repin(project_root, old_label, new_label)
    stale = list(proposal["stale"])
    reopen_items(_workspace(project_root), stale)
    return {**proposal, "reopened": stale}


@mcp.tool()
def write_retrospective(
    project_root: str,
    item: str,
    body: str,
    about: list[str] | None = None,
) -> dict[str, Any]:
    """Write the retrospective attached to a completed work-item identifier."""
    ws = _workspace(project_root)
    note = Retrospective(id=item, body=body, about=about or [])
    ws.write_retrospective(note)
    return note.model_dump()


@mcp.tool()
def write_feedback(
    project_root: str,
    feedback_id: str,
    body: str,
    about: list[str] | None = None,
) -> dict[str, Any]:
    """Write a blocked-work feedback note with an explicit stable identifier."""
    ws = _workspace(project_root)
    note = Feedback(id=feedback_id, body=body, about=about or [])
    ws.write_feedback(note)
    return note.model_dump()


def main() -> None:
    """Run the host-neutral stdio MCP transport."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
