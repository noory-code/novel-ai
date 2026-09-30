"""Planning — create WorkItems at any altitude and decompose them.

The *judgement* (how to split a goal, what each gate checks) belongs to the
agent and the plan skill. These helpers own the mechanics: allocating
level-prefixed ids and writing well-formed files, so anything they create
satisfies the format. A child is appended to its parent's ``children`` list in
lock-step; adding a child to a leaf (one with a gate) is rejected by the model.
"""

from __future__ import annotations

import re

from .errors import OrderError
from .formats import WorkItem
from .graph import load_items, order_problems
from .workspace import Workspace, validate_path_name

_LEVEL_PREFIX = {
    "initiative": "INIT",
    "epic": "EPIC",
    "story": "STORY",
    "action": "ACT",
}


def _prefix(level: str) -> str:
    return _LEVEL_PREFIX.get(level) or level.upper()


def next_item_id(ws: Workspace, level: str) -> str:
    """The next free ``{PREFIX}-NNN`` id for ``level`` in the workspace."""
    prefix = validate_path_name(_prefix(level))
    pattern = re.compile(rf"^{re.escape(prefix)}-(\d+)$")
    highest = 0
    for item_id in ws.list_items():
        match = pattern.match(item_id)
        if match:
            highest = max(highest, int(match.group(1)))
    return f"{prefix}-{highest + 1:03d}"


def create_item(
    ws: Workspace,
    level: str,
    goal: str,
    *,
    gate: str = "",
    parent: str | None = None,
    realizes: list[str] | None = None,
    after: list[str] | None = None,
) -> WorkItem:
    """Create a WorkItem (optionally a gated leaf, optionally under a parent).

    A leaf is created by passing a ``gate``; a container is created without one
    and grows children as later items are added under it. ``realizes`` links the
    item to the format F slug(s) it builds (by value — no Novel import).
    """
    item_id = next_item_id(ws, level)
    box = ws.load_item(parent) if parent is not None else None
    item = WorkItem(
        id=item_id,
        level=level,
        status="todo",
        gate=gate,
        goal=goal,
        realizes=realizes or [],
        after=after or [],
    )
    items = load_items(ws)
    items[item.id] = item
    if box is not None:
        items[box.id] = box.model_copy(update={"children": [*box.children, item.id]})
    problems = order_problems(items)
    if problems:
        raise OrderError("; ".join(detail for _kind, detail in problems))
    ws.write_item(item)
    if box is not None:
        ws.write_item(box.model_copy(update={"children": [*box.children, item.id]}))
    return item


def set_after(ws: Workspace, item_id: str, after: list[str]) -> WorkItem:
    """Replace one item's order links after validating the complete future graph."""
    item = ws.load_item(item_id)
    updated = WorkItem.model_validate({**item.model_dump(), "after": after})
    items = load_items(ws)
    items[item_id] = updated
    problems = order_problems(items)
    if problems:
        raise OrderError("; ".join(detail for _kind, detail in problems))
    ws.write_item(updated)
    return updated
