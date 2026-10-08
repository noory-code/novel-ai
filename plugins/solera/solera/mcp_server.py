"""FastMCP adapter over Solera's deterministic file-based core.

The MCP layer owns no workflow state and makes no planning decisions. It only
maps host-neutral tool calls onto the same functions used by the CLI and skills.
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .audit import audit_workspace
from .errors import AcceptRequiredError
from .formats import Accept, Feedback, Phase, Retrospective
from .graph import completion, items_by_slugs, load_items
from .intake import import_release, load_imported_release
from .notes import record_feedback, record_retrospective
from .planning import (
    add_after,
    create_item,
    move_item,
    remove_after,
    set_after,
    set_goal,
    set_phase,
    set_realizes,
)
from .repin import apply_repin, propose_repin
from .supervisor import complete, instruction, ready_leaves, start_next
from .workspace import Workspace

if TYPE_CHECKING:
    from fastmcp import FastMCP

_MCP_INSTRUCTIONS = (
    "Solera stores an executable work tree under .noory/solera. Plan or add "
    "items, ask for exactly one next leaf, and complete that leaf only after "
    "the implementation is ready for its deterministic gate. Re-pin is a "
    "two-step operation: inspect and approve the proposal first, then apply "
    "that exact proposal ID. --accept is required without a gate; children rolls "
    "up finished children, person waits for the person's judgment, and agents never "
    "judge a person's result."
)
_mcp: FastMCP | None = None


def _workspace(project_root: str) -> Workspace:
    return Workspace(Path(project_root).expanduser().resolve() / ".noory" / "solera")


def plan_work(
    project_root: str,
    goal: str,
    level: str = "story",
    after: list[str] | None = None,
    accept: Accept | None = None,
) -> dict[str, Any]:
    """Create a root work container. Add gated child leaves before asking for next work.

    ``accept`` is required without a gate; ``children`` rolls up finished children,
    while ``person`` waits for that person's judgment. Agents never judge a person's result.
    """
    if accept is None:
        raise AcceptRequiredError(
            "accept is required when an item has no gate; choose children or person"
        )
    item = create_item(_workspace(project_root), level, goal, after=after, accept=accept)
    return item.model_dump()


def add_work_item(
    project_root: str,
    parent: str,
    goal: str,
    level: str = "action",
    gate: str = "",
    realizes: list[str] | None = None,
    after: list[str] | None = None,
    accept: Accept | None = None,
) -> dict[str, Any]:
    """Add a child to ``parent``. Pass a deterministic command in ``gate`` for a leaf.

    ``accept`` is required without a gate; ``children`` rolls up finished children,
    while ``person`` waits for that person's judgment. Agents never judge a person's result.
    """
    if not gate and accept is None:
        raise AcceptRequiredError(
            "accept is required when an item has no gate; choose children or person"
        )
    item = create_item(
        _workspace(project_root),
        level,
        goal,
        parent=parent,
        gate=gate,
        realizes=realizes,
        after=after,
        accept=accept,
    )
    return item.model_dump()


def set_work_item_after(project_root: str, item: str, after: list[str]) -> dict[str, Any]:
    """Replace an item's order links (ids that must be done before it starts).

    An empty list clears them.
    """
    return set_after(_workspace(project_root), item, after).model_dump()


def set_work_item_goal(project_root: str, item: str, goal: str) -> dict[str, Any]:
    """Replace an item's goal. Unknown items and blank goals are rejected."""
    return set_goal(_workspace(project_root), item, goal).model_dump()


def set_work_item_realizes(project_root: str, item: str, realizes: list[str]) -> dict[str, Any]:
    """Replace an item's realizes slugs; empty clears them.

    Unknown items and blank or duplicate slugs are rejected.
    """
    return set_realizes(_workspace(project_root), item, realizes).model_dump()


def set_work_item_phase(
    project_root: str,
    item: str,
    phase: Phase,
    phase_note: str = "",
) -> dict[str, Any]:
    """Record an item's progress phase and note without changing its status."""
    return set_phase(_workspace(project_root), item, phase, phase_note).model_dump()


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


def add_work_item_after(project_root: str, item: str, predecessor: str) -> dict[str, Any]:
    """Add one order link; unknown ids and unsatisfiable links are rejected.

    Adding an existing link is an idempotent no-op.
    """
    return add_after(_workspace(project_root), item, predecessor).model_dump()


def remove_work_item_after(project_root: str, item: str, predecessor: str) -> dict[str, Any]:
    """Remove one order link; an unknown item is rejected.

    Removing a link that is not present is an idempotent no-op.
    """
    return remove_after(_workspace(project_root), item, predecessor).model_dump()


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


def work_items_by_slugs(project_root: str, slugs: list[str]) -> dict[str, Any]:
    """Return item ids realizing each requested design slug, including empty matches."""
    items = load_items(_workspace(project_root))
    return {"by_slug": items_by_slugs(items, slugs)}


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


def complete_current(project_root: str, timeout_seconds: float = 120.0) -> dict[str, Any]:
    """Run the current leaf's stored gate; mark it done only when the gate passes."""
    root = Path(project_root).expanduser().resolve()
    ws = _workspace(project_root)
    with ws.lock():
        progress = ws.load_progress()
        if progress.item is None:
            raise ValueError("no Solera work item is currently active")
    result = complete(ws, progress.item, cwd=root, timeout=timeout_seconds)
    return asdict(result)


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


def import_spec(project_root: str, source: str, label: str) -> dict[str, Any]:
    """Import one immutable format-F service release into ``specs/{label}``."""
    return import_release(
        _workspace(project_root), Path(source).expanduser().resolve(), label=label
    )


def propose_spec_repin(project_root: str, old_label: str, new_label: str) -> dict[str, Any]:
    """Return a proposal and its approval ID without changing work state."""
    ws = _workspace(project_root)
    return propose_repin(
        ws,
        load_imported_release(ws, old_label),
        load_imported_release(ws, new_label),
    )


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


def write_retrospective(
    project_root: str,
    item: str,
    body: str,
    about: list[str] | None = None,
) -> dict[str, Any]:
    """Write the retrospective attached to a completed work-item identifier."""
    ws = _workspace(project_root)
    note = Retrospective(id=item, body=body, about=about or [])
    record_retrospective(ws, note)
    return note.model_dump()


def write_feedback(
    project_root: str,
    feedback_id: str,
    body: str,
    about: list[str] | None = None,
) -> dict[str, Any]:
    """Write a blocked-work feedback note with an explicit stable identifier."""
    ws = _workspace(project_root)
    note = Feedback(id=feedback_id, body=body, about=about or [])
    record_feedback(ws, note)
    return note.model_dump()


def _get_mcp() -> FastMCP:
    """Build the FastMCP adapter only when a host asks for it.

    Keeping this import lazy means importing :mod:`solera.mcp_server` does not
    initialize FastMCP's transport stack.
    """
    global _mcp
    if _mcp is None:
        from fastmcp import FastMCP

        server = FastMCP("solera", instructions=_MCP_INSTRUCTIONS)
        for tool in (
            plan_work,
            add_work_item,
            set_work_item_after,
            set_work_item_goal,
            set_work_item_phase,
            set_work_item_realizes,
            move_work_item,
            add_work_item_after,
            remove_work_item_after,
            ready_work_items,
            work_items_by_slugs,
            next_work_item,
            complete_current,
            workspace_status,
            import_spec,
            propose_spec_repin,
            apply_spec_repin,
            write_retrospective,
            write_feedback,
        ):
            server.tool()(tool)
        _mcp = server
    return _mcp


def __getattr__(name: str) -> FastMCP:
    if name == "mcp":
        return _get_mcp()
    raise AttributeError(name)


def main() -> None:
    """Run the host-neutral stdio MCP transport."""
    _get_mcp().run(transport="stdio")


if __name__ == "__main__":
    main()
