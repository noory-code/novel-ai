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

from dataclasses import dataclass
from pathlib import Path

from . import graph
from .errors import OrderError
from .formats import Progress, Status, WorkItem
from .gate import DEFAULT_TIMEOUT_SECONDS, GateResult, run_item_gate
from .intake import has_imported_design
from .workspace import Workspace


@dataclass(frozen=True)
class BlockedLeaf:
    """A todo leaf and every reason it cannot start."""

    leaf_id: str
    waiting_on: tuple[str, ...]
    names_no_design_node: bool

    @property
    def reasons(self) -> tuple[str, ...]:
        """Human-readable reasons suitable for CLI, MCP, and errors."""
        reasons: list[str] = []
        if self.waiting_on:
            reasons.append(f"{self.leaf_id} waits for {', '.join(self.waiting_on)}")
        if self.names_no_design_node:
            reasons.append(
                f"leaf {self.leaf_id} and its ancestors realize no design slug; "
                "name the node it serves with `realizes` (for example, `feature/login`)"
            )
        return tuple(reasons)


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
    return _leaves_from_items(graph.load_items(ws))


def _leaves_from_items(items: dict[str, WorkItem]) -> list[str]:
    """Leaf ids in depth-first order from an already loaded item mapping."""
    leaves: list[str] = []
    seen: set[str] = set()
    child_ids = graph.parents(items)

    def visit(item_id: str) -> None:
        if item_id in seen or item_id not in items:
            return
        seen.add(item_id)
        item = items[item_id]
        if item.is_container:
            for child_id in item.children:
                visit(child_id)
        elif item.is_leaf:
            leaves.append(item_id)

    for root in (item_id for item_id in items if item_id not in child_ids):
        visit(root)
    return leaves


def find_next_open(ws: Workspace) -> str | None:
    """The next leaf to work on, or ``None`` if every leaf is done.

    A ``doing`` leaf is resumed before any ``todo`` leaf is started — one active
    leaf at a time, so a leaf stuck after a failed gate is re-offered, not skipped.
    """
    items = graph.load_items(ws)
    leaves = _leaves_from_items(items)
    for leaf_id in leaves:
        if items[leaf_id].status == "doing":
            return leaf_id
    design_required = has_imported_design(ws)
    blocked: list[BlockedLeaf] = []
    for leaf_id in leaves:
        if items[leaf_id].status != "todo":
            continue
        blocked_leaf = _blocked_leaf(items, leaf_id, design_required=design_required)
        if blocked_leaf is None:
            return leaf_id
        blocked.append(blocked_leaf)
    if blocked:
        details = "; ".join(reason for leaf in blocked for reason in leaf.reasons)
        raise OrderError(f"no leaf can start: {details}")
    return None


def _blocked_leaf(
    items: dict[str, WorkItem],
    leaf_id: str,
    *,
    design_required: bool,
) -> BlockedLeaf | None:
    waiting_on = tuple(graph.waiting_on(items, leaf_id))
    names_no_design_node = design_required and not graph.reaches_design_node(items, leaf_id)
    if not waiting_on and not names_no_design_node:
        return None
    return BlockedLeaf(
        leaf_id=leaf_id,
        waiting_on=waiting_on,
        names_no_design_node=names_no_design_node,
    )


def ready_leaves(ws: Workspace) -> tuple[list[str], list[BlockedLeaf]]:
    """Return startable and blocked todo leaves in supervisor order."""
    items = graph.load_items(ws)
    design_required = has_imported_design(ws)
    ready: list[str] = []
    blocked: list[BlockedLeaf] = []
    for leaf_id in _leaves_from_items(items):
        if items[leaf_id].status != "todo":
            continue
        blocked_leaf = _blocked_leaf(items, leaf_id, design_required=design_required)
        if blocked_leaf is None:
            ready.append(leaf_id)
        else:
            blocked.append(blocked_leaf)
    return ready, blocked


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
    if current is not None:
        rollup_item_and_ancestors(ws, current)


def rollup_item_and_ancestors(ws: Workspace, item_id: str) -> None:
    """Mark a container and successive ancestors done when all children are done.

    Unlike :func:`_rollup`, this includes ``item_id`` itself. Tree edits use it
    after removing an open child from a container; gate completion starts from
    the completed leaf's parent through :func:`_rollup`.
    """
    parents = parent_map(ws)
    current: str | None = item_id
    while current is not None:
        item = ws.load_item(current)
        if item.children and all(ws.load_item(child).status == "done" for child in item.children):
            set_item_status(ws, current, "done")
            current = parents.get(current)
        else:
            break


def invalidate_done_ancestors(ws: Workspace, item_id: str) -> None:
    """The inverse of :func:`_rollup`. Reopening a descendant breaks the rollup
    invariant (a container is ``done`` only when all its children are done), so
    walk up and reset any ancestor that is ``done`` but now has a non-done child.
    Idempotent; stops at the first ancestor still legitimately done."""
    parents = parent_map(ws)
    current = parents.get(item_id)
    while current is not None:
        item = ws.load_item(current)
        if item.status == "done" and not all(
            ws.load_item(child).status == "done" for child in item.children
        ):
            set_item_status(ws, current, "todo")
            current = parents.get(current)
        else:
            break


def reopen_items(ws: Workspace, item_ids: list[str]) -> None:
    """Reopen items without leaving a done ancestor above an open descendant.

    Every target and its ancestor graph is loaded and validated before writes
    begin. The complete final state is then calculated in memory and written in
    root-to-leaf order. A retry after an interrupted write therefore converges
    on the same state without ever falsely claiming that open work is done.
    """
    if not item_ids:
        return

    items = {item_id: ws.load_item(item_id) for item_id in ws.list_items()}
    targets = set(item_ids)
    for item_id in targets:
        if item_id not in items:
            ws.load_item(item_id)

    parents_of: dict[str, list[str]] = {}
    for parent_id, item in items.items():
        for child_id in item.children:
            parents_of.setdefault(child_id, []).append(parent_id)

    ancestors: set[str] = set()
    depths: dict[str, int] = {}
    for target_id in targets:
        chain = [target_id]
        current = target_id
        while current in parents_of:
            parent_ids = parents_of[current]
            if len(parent_ids) != 1:
                joined = ", ".join(sorted(parent_ids))
                raise ValueError(f"{current} has multiple parents: {joined}")
            parent_id = parent_ids[0]
            if parent_id in chain:
                raise ValueError(f"cycle detected through {parent_id}")
            chain.append(parent_id)
            ancestors.add(parent_id)
            current = parent_id
        for depth, item_id in enumerate(reversed(chain)):
            depths[item_id] = max(depths.get(item_id, 0), depth)

    for ancestor_id in ancestors:
        for child_id in items[ancestor_id].children:
            if child_id not in items:
                ws.load_item(child_id)

    final: dict[str, WorkItem] = {}
    for item_id in targets:
        item = items[item_id]
        if item.status != "todo":
            final[item_id] = item.model_copy(update={"status": "todo"})
    for item_id in ancestors:
        item = items[item_id]
        if item.status == "done":
            final[item_id] = item.model_copy(update={"status": "todo"})

    for item_id in sorted(final, key=lambda candidate: (depths[candidate], candidate)):
        ws.write_item(final[item_id])


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
