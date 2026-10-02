"""Planning — create and edit WorkItems and their tree/order relationships.

The *judgement* (how to split a goal, what each gate checks) belongs to the
agent and the plan skill. These helpers own the mechanics: allocating
level-prefixed ids and writing well-formed files, so every operation satisfies
the format and validates the complete future order graph before writing it.
"""

from __future__ import annotations

import re

from pydantic import ValidationError

from .errors import (
    BlankGoalError,
    ChildIndexOutOfRangeError,
    DuplicateRealizesSlugError,
    InvalidGateError,
    InvalidOrderLinkError,
    InvalidRealizesSlugError,
    MoveUnderDescendantError,
    MoveUnderSelfError,
    MultipleParentsError,
    OrderCycleError,
    OrderError,
    OrderWaitsOnAncestorError,
    OrderWaitsOnDescendantError,
    ParentIsLeafError,
    PlanningValueError,
    RootIndexNotSupportedError,
    UnknownParentError,
    UnknownPredecessorError,
    UnknownWorkItemError,
)
from .formats import WorkItem
from .graph import load_items, order_problems
from .supervisor import invalidate_done_ancestors, rollup_item_and_ancestors
from .workspace import Workspace, validate_path_name, workspace_locked

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


def _validate_realizes(realizes: list[str]) -> None:
    if any(not slug.strip() for slug in realizes):
        raise InvalidRealizesSlugError("realizes slugs must not be empty or blank")
    if len(set(realizes)) != len(realizes):
        raise DuplicateRealizesSlugError("realizes slugs must not contain duplicates")


def _validated_item(data: dict[str, object]) -> WorkItem:
    """Build a WorkItem while assigning input failures stable core codes."""
    try:
        return WorkItem.model_validate(data)
    except ValidationError as exc:
        goal = data.get("goal")
        gate = data.get("gate")
        after = data.get("after", [])
        item_id = data.get("id")
        if isinstance(goal, str) and not goal.strip():
            raise BlankGoalError(str(exc)) from exc
        if isinstance(gate, str) and gate and not gate.strip():
            raise InvalidGateError(str(exc)) from exc
        if isinstance(after, list):
            string_after = [value for value in after if isinstance(value, str)]
            if any(not value.strip() for value in string_after) or len(set(string_after)) != len(
                string_after
            ):
                raise InvalidOrderLinkError(str(exc)) from exc
            if item_id in string_after:
                raise OrderCycleError(str(exc)) from exc
        raise PlanningValueError(str(exc)) from exc


def _raise_order_problems(problems: list[tuple[str, str]]) -> None:
    """Raise a coded rejection from structured graph problem kinds."""
    if not problems:
        return
    message = "; ".join(detail for _kind, detail in problems)
    kinds = {kind for kind, _detail in problems}
    if "after-missing" in kinds:
        raise UnknownPredecessorError(message)
    if "after-cycle" in kinds:
        raise OrderCycleError(message)
    if "order_waits_on_descendant" in kinds:
        raise OrderWaitsOnDescendantError(message)
    if "order_waits_on_ancestor" in kinds:
        raise OrderWaitsOnAncestorError(message)
    raise OrderError(message)


@workspace_locked
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
    realizes = realizes or []
    _validate_realizes(realizes)
    item = _validated_item(
        {
            "id": item_id,
            "level": level,
            "status": "todo",
            "gate": gate,
            "goal": goal,
            "realizes": realizes,
            "after": after or [],
        }
    )
    items = load_items(ws)
    items[item.id] = item
    updated_box: WorkItem | None = None
    if box is not None:
        try:
            updated_box = WorkItem.model_validate(
                {**box.model_dump(), "children": [*box.children, item.id]}
            )
        except ValidationError as exc:
            if box.gate:
                raise ParentIsLeafError(str(exc)) from exc
            raise PlanningValueError(str(exc)) from exc
        items[box.id] = updated_box
    problems = order_problems(items)
    _raise_order_problems(problems)
    ws.write_item(item)
    if updated_box is not None:
        ws.write_item(updated_box)
    return item


@workspace_locked
def set_after(ws: Workspace, item_id: str, after: list[str]) -> WorkItem:
    """Replace one item's order links after validating the complete future graph."""
    item = ws.load_item(item_id)
    updated = _validated_item({**item.model_dump(), "after": after})
    items = load_items(ws)
    items[item_id] = updated
    problems = order_problems(items)
    _raise_order_problems(problems)
    ws.write_item(updated)
    return updated


@workspace_locked
def set_goal(ws: Workspace, item_id: str, goal: str) -> WorkItem:
    """Replace one item's goal, rejecting the same blank goals as creation."""
    item = ws.load_item(item_id)
    updated = _validated_item({**item.model_dump(), "goal": goal})
    ws.write_item(updated)
    return updated


@workspace_locked
def set_realizes(ws: Workspace, item_id: str, realizes: list[str]) -> WorkItem:
    """Replace one item's complete realizes-slug list; an empty list clears it."""
    item = ws.load_item(item_id)
    _validate_realizes(realizes)
    updated = _validated_item({**item.model_dump(), "realizes": realizes})
    ws.write_item(updated)
    return updated


@workspace_locked
def add_after(ws: Workspace, item_id: str, predecessor: str) -> WorkItem:
    """Add one order link, or return the unchanged item when it already exists."""
    item = ws.load_item(item_id)
    if predecessor in item.after:
        return item
    return set_after(ws, item_id, [*item.after, predecessor])


@workspace_locked
def remove_after(ws: Workspace, item_id: str, predecessor: str) -> WorkItem:
    """Remove one order link, or return the unchanged item when it is absent."""
    item = ws.load_item(item_id)
    if predecessor not in item.after:
        return item
    return set_after(
        ws, item_id, [candidate for candidate in item.after if candidate != predecessor]
    )


def _descendants(items: dict[str, WorkItem], item_id: str) -> set[str]:
    descendants: set[str] = set()
    pending = list(items[item_id].children)
    while pending:
        candidate = pending.pop()
        if candidate in descendants:
            continue
        descendants.add(candidate)
        if candidate in items:
            pending.extend(items[candidate].children)
    return descendants


def _insert_child(children: list[str], item_id: str, index: int | None) -> list[str]:
    without_item = [child_id for child_id in children if child_id != item_id]
    position = len(without_item) if index is None else index
    if position < 0 or position > len(without_item):
        raise ChildIndexOutOfRangeError(
            f"child index {position} is out of range; expected 0..{len(without_item)}"
        )
    without_item.insert(position, item_id)
    return without_item


@workspace_locked
def move_item(
    ws: Workspace,
    item_id: str,
    new_parent: str | None,
    index: int | None,
) -> WorkItem:
    """Reparent or reorder an item while preserving tree and order invariants.

    Root traversal is fixed by item-id order because roots have no stored order;
    moving to the root therefore rejects an ``index`` instead of ignoring it.
    """
    items = load_items(ws)
    if item_id not in items:
        raise UnknownWorkItemError(f"unknown work item: {item_id}")
    if new_parent is not None and new_parent not in items:
        raise UnknownParentError(f"unknown destination parent: {new_parent}")
    if new_parent is None and index is not None:
        raise RootIndexNotSupportedError(
            "root order is fixed by item ID; index is not supported for roots"
        )
    if new_parent == item_id:
        raise MoveUnderSelfError(f"cannot move {item_id} under itself")
    if new_parent is not None and new_parent in _descendants(items, item_id):
        raise MoveUnderDescendantError(f"cannot move {item_id} under its descendant {new_parent}")
    if new_parent is not None and items[new_parent].gate:
        raise ParentIsLeafError(f"cannot move under gated leaf {new_parent}")

    source_parents = [parent_id for parent_id, item in items.items() if item_id in item.children]
    if len(source_parents) > 1:
        joined = ", ".join(source_parents)
        raise MultipleParentsError(f"cannot move {item_id}: item has multiple parents: {joined}")
    source_parent = source_parents[0] if source_parents else None

    source_original = items[source_parent] if source_parent is not None else None
    destination_original = items[new_parent] if new_parent is not None else None
    structural_writes: list[tuple[WorkItem | None, WorkItem | None]]

    if source_parent == new_parent:
        if source_original is None:
            return items[item_id]
        assert source_parent is not None
        reordered = source_original.model_copy(
            update={"children": _insert_child(source_original.children, item_id, index)}
        )
        items[source_parent] = reordered
        structural_writes = [(reordered, None)]
    else:
        source_updated = (
            source_original.model_copy(
                update={
                    "children": [
                        child_id for child_id in source_original.children if child_id != item_id
                    ]
                }
            )
            if source_original is not None
            else None
        )
        destination_updated = (
            destination_original.model_copy(
                update={"children": _insert_child(destination_original.children, item_id, index)}
            )
            if destination_original is not None
            else None
        )
        if source_updated is not None:
            items[source_updated.id] = source_updated
        if destination_updated is not None:
            items[destination_updated.id] = destination_updated
        # Attach first so a failed second write cannot orphan the item. If the
        # source write fails, restoring this original removes the duplicate.
        structural_writes = [(destination_updated, destination_original), (source_updated, None)]

    problems = order_problems(items)
    _raise_order_problems(problems)

    first, first_original = structural_writes[0]
    if first is not None:
        ws.write_item(first)
    if len(structural_writes) > 1:
        second, _ = structural_writes[1]
        try:
            if second is not None:
                ws.write_item(second)
        except BaseException:
            if first is not None and first_original is not None:
                ws.write_item(first_original)
            raise

    invalidate_done_ancestors(ws, item_id)
    if source_parent is not None and source_parent != new_parent:
        rollup_item_and_ancestors(ws, source_parent)
    if new_parent is not None:
        rollup_item_and_ancestors(ws, new_parent)
    return ws.load_item(item_id)
