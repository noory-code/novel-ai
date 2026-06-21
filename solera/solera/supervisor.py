"""The supervisor — Solera's ordering (L) over the WorkItem tree.

The supervisor never builds anything. It walks the tree to the next open leaf,
hands the agent a plain-text instruction, runs the leaf's gate, and either
advances (on pass) or stops for a human (on fail). All state is the workspace
files; the supervisor holds none of its own.

The tree is reconstructed from each item's ``children`` list. The ``progress.md``
pointer names the single active leaf: :func:`start_next` sets it and clears it to
``null`` when nothing is open. A gate failure leaves the leaf in ``doing`` on
purpose — :func:`find_next_open` resumes it rather than skipping past it (one
active leaf at a time).
"""

from __future__ import annotations

from pathlib import Path

from .formats import Progress, Status, WorkItem
from .gate import DEFAULT_TIMEOUT_SECONDS, GateResult, run_item_gate
from .workspace import Workspace


def parent_map(ws: Workspace) -> dict[str, str]:
    """Map each child id to its parent id, derived from every item's children."""
    out: dict[str, str] = {}
    for item_id in ws.list_items():
        for child_id in ws.load_item(item_id).children:
            out[child_id] = item_id
    return out


def roots(ws: Workspace) -> list[str]:
    """Item ids that are no one's child — the tops of the forest, in id order."""
    children = parent_map(ws)
    return [item_id for item_id in ws.list_items() if item_id not in children]


def _leaves_in_order(ws: Workspace) -> list[str]:
    """Leaf ids in depth-first, declaration order across the forest."""
    leaves: list[str] = []
    seen: set[str] = set()

    def visit(item_id: str) -> None:
        if item_id in seen:  # defensive against a malformed cycle
            return
        seen.add(item_id)
        item = ws.load_item(item_id)
        if item.is_container:
            for child_id in item.children:
                visit(child_id)
        elif item.is_leaf:
            leaves.append(item_id)

    for root in roots(ws):
        visit(root)
    return leaves


def find_next_open(ws: Workspace) -> str | None:
    """The next leaf to work on, or ``None`` if every leaf is done.

    A ``doing`` leaf is resumed before any ``todo`` leaf is started — one active
    leaf at a time, so a leaf stuck after a failed gate is re-offered, not skipped.
    """
    first_todo: str | None = None
    for leaf_id in _leaves_in_order(ws):
        status = ws.load_item(leaf_id).status
        if status == "doing":
            return leaf_id
        if status == "todo" and first_todo is None:
            first_todo = leaf_id
    return first_todo


def set_item_status(ws: Workspace, item_id: str, status: Status) -> WorkItem:
    """Rewrite one item's status, preserving its other fields."""
    updated = ws.load_item(item_id).model_copy(update={"status": status})
    ws.write_item(updated)
    return updated


def start_next(ws: Workspace) -> str | None:
    """Pick the next open leaf, mark it ``doing``, and point at it.

    Returns the leaf id now in progress, or ``None`` when nothing is open — in
    which case the pointer is cleared to ``null``.
    """
    nxt = find_next_open(ws)
    if nxt is None:
        ws.write_progress(Progress(item=None))
        return None
    set_item_status(ws, nxt, "doing")
    ws.write_progress(Progress(item=nxt))
    return nxt


def instruction(ws: Workspace, item_id: str) -> str:
    """The plain-text handoff given to the external agent for one leaf."""
    item = ws.load_item(item_id)
    return (
        f"You are working on {item_id} ({item.level}).\n\n"
        f"Goal:\n{item.goal}\n\n"
        "When you are done, Solera verifies your work by running this gate "
        "(do not run it yourself — just make it pass):\n"
        f"  {item.gate}\n"
    )


def _rollup(ws: Workspace, leaf_id: str) -> None:
    """Mark each ancestor done once all of its children are done."""
    parents = parent_map(ws)
    current = parents.get(leaf_id)
    while current is not None:
        item = ws.load_item(current)
        if all(ws.load_item(child).status == "done" for child in item.children):
            set_item_status(ws, current, "done")
            current = parents.get(current)
        else:
            break


def complete(
    ws: Workspace,
    item_id: str,
    *,
    cwd: Path,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> GateResult:
    """Run a leaf's gate and branch on the verdict.

    Pass: the leaf becomes ``done`` and each ancestor whose children are all done
    rolls up to ``done`` too. Fail: the leaf stays ``doing`` and the result is
    returned so the caller stops and escalates to a human.
    """
    item = ws.load_item(item_id)
    result = run_item_gate(item, cwd=cwd, timeout=timeout)
    if not result.passed:
        return result
    set_item_status(ws, item_id, "done")
    _rollup(ws, item_id)
    return result
