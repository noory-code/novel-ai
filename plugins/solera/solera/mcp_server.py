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
from .graph import completion, load_items
from .intake import import_release, load_imported_release
from .planning import (
    add_after,
    create_item,
    move_item,
    remove_after,
    set_after,
    set_goal,
    set_realizes,
)
from .repin import apply_repin, propose_repin
from .supervisor import complete, instruction, ready_leaves, start_next
from .workspace import Workspace

mcp = FastMCP(
    "solera",
    instructions=(
        "Solera stores an executable work tree under .noory/solera. Plan or add "
        "items, ask for exactly one next leaf, and complete that leaf only after "
        "the implementation is ready for its deterministic gate. Re-pin is a "
        "two-step operation: inspect and approve the proposal first, then apply "
        "that exact proposal ID."
    ),
)


def _workspace(project_root: str) -> Workspace:
    return Workspace(Path(project_root).expanduser().resolve() / ".noory" / "solera")


@mcp.tool()
def plan_work(
    project_root: str,
    goal: str,
    level: str = "story",
    after: list[str] | None = None,
) -> dict[str, Any]:
    """Create a root work container. Add gated child leaves before asking for next work."""
    item = create_item(_workspace(project_root), level, goal, after=after)
    return item.model_dump()


@mcp.tool()
def add_work_item(
    project_root: str,
    parent: str,
    goal: str,
    level: str = "action",
    gate: str = "",
    realizes: list[str] | None = None,
    after: list[str] | None = None,
) -> dict[str, Any]:
    """Add a child to ``parent``. Pass a deterministic command in ``gate`` for a leaf."""
    item = create_item(
        _workspace(project_root),
        level,
        goal,
        parent=parent,
        gate=gate,
        realizes=realizes,
        after=after,
    )
    return item.model_dump()


@mcp.tool()
def set_work_item_after(project_root: str, item: str, after: list[str]) -> dict[str, Any]:
    """Replace an item's order links (ids that must be done before it starts).

    An empty list clears them.
    """
    return set_after(_workspace(project_root), item, after).model_dump()


@mcp.tool()
def set_work_item_goal(project_root: str, item: str, goal: str) -> dict[str, Any]:
    """Replace an item's goal. Unknown items and blank goals are rejected."""
    return set_goal(_workspace(project_root), item, goal).model_dump()


@mcp.tool()
def set_work_item_realizes(project_root: str, item: str, realizes: list[str]) -> dict[str, Any]:
    """Replace an item's realizes slugs; empty clears them.

    Unknown items and blank or duplicate slugs are rejected.
    """
    return set_realizes(_workspace(project_root), item, realizes).model_dump()


@mcp.tool()
def move_work_item(
    project_root: str,
    item: str,
    new_parent: str | None = None,
    index: int | None = None,
) -> dict[str, Any]:
    """Reparent or reorder an item; ``None`` makes it a root.

    Unknown ids, root indices, invalid indices, self/descendant destinations,
    gated destination leaves, and moves that create order problems are rejected.
    """
    return move_item(_workspace(project_root), item, new_parent, index).model_dump()


@mcp.tool()
def add_work_item_after(project_root: str, item: str, predecessor: str) -> dict[str, Any]:
    """Add one order link; unknown ids and unsatisfiable links are rejected.

    Adding an existing link is an idempotent no-op.
    """
    return add_after(_workspace(project_root), item, predecessor).model_dump()


@mcp.tool()
def remove_work_item_after(project_root: str, item: str, predecessor: str) -> dict[str, Any]:
    """Remove one order link; an unknown item is rejected.

    Removing a link that is not present is an idempotent no-op.
    """
    return remove_after(_workspace(project_root), item, predecessor).model_dump()


@mcp.tool()
def ready_work_items(project_root: str) -> dict[str, Any]:
    """List todo leaves that can start now and blocked leaves with their reasons.

    Ready leaves are safe to work on together. This query is read-only.
    """
    ready, blocked = ready_leaves(_workspace(project_root))
    return {
        "ready": ready,
        "blocked": [
            {
                "id": leaf.leaf_id,
                "waiting_on": list(leaf.waiting_on),
                "reasons": list(leaf.reasons),
            }
            for leaf in blocked
        ],
    }


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
    items = load_items(ws)
    return {
        "current": pointer,
        "items": [item.model_dump() for item in items.values()],
        "progress": {item_id: asdict(value) for item_id, value in completion(items).items()},
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
    """Return a proposal and its approval ID without changing work state."""
    ws = _workspace(project_root)
    return propose_repin(
        ws,
        load_imported_release(ws, old_label),
        load_imported_release(ws, new_label),
    )


@mcp.tool()
def apply_spec_repin(
    project_root: str,
    old_label: str,
    new_label: str,
    proposal_id: str,
) -> dict[str, Any]:
    """Apply a reviewed proposal by ID, rejecting it if the proposal changed."""
    ws = _workspace(project_root)
    return apply_repin(
        ws,
        load_imported_release(ws, old_label),
        load_imported_release(ws, new_label),
        proposal_id,
    )


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
