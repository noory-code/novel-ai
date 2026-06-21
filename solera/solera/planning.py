"""Planning — create WorkItems at any altitude and decompose them.

The *judgement* (how to split a goal, what each gate checks) belongs to the
agent and the plan skill. These helpers own the mechanics: allocating
level-prefixed ids and writing well-formed files, so anything they create
satisfies the format. A child is appended to its parent's ``children`` list in
lock-step; adding a child to a leaf (one with a gate) is rejected by the model.
"""

from __future__ import annotations

import re

from .formats import WorkItem
from .workspace import Workspace

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
    prefix = _prefix(level)
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
) -> WorkItem:
    """Create a WorkItem (optionally a gated leaf, optionally under a parent).

    A leaf is created by passing a ``gate``; a container is created without one
    and grows children as later items are added under it.
    """
    item = WorkItem(id=next_item_id(ws, level), level=level, status="todo", gate=gate, goal=goal)
    ws.write_item(item)
    if parent is not None:
        box = ws.load_item(parent)
        ws.write_item(box.model_copy(update={"children": [*box.children, item.id]}))
    return item
