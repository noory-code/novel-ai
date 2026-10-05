"""Core WorkItem edits: goal, realizes, tree position, and single order links."""

from pathlib import Path

import pytest

from solera.errors import OrderError, OrderWaitsOnDescendantError, PlanningError
from solera.planning import (
    add_after,
    create_item,
    move_item,
    remove_after,
    set_goal,
    set_realizes,
)
from solera.workspace import Workspace


def _ws(tmp_path: Path) -> Workspace:
    return Workspace(tmp_path / ".noory" / "solera")


def test_set_goal_replaces_goal(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    item = create_item(ws, "story", "Old goal", accept="children")

    updated = set_goal(ws, item.id, "New goal\nwith detail")

    assert updated.goal == "New goal\nwith detail"
    assert ws.load_item(item.id) == updated


def test_set_goal_rejects_blank_without_writing(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    item = create_item(ws, "story", "Keep this", accept="children")

    with pytest.raises(ValueError, match="goal"):
        set_goal(ws, item.id, "   \n")

    assert ws.load_item(item.id).goal == "Keep this"


def test_set_realizes_replaces_and_clears_slugs(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    item = create_item(ws, "story", "Goal", realizes=["feature/old"], accept="children")

    updated = set_realizes(ws, item.id, ["feature/login", "entity/account"])
    assert updated.realizes == ["feature/login", "entity/account"]
    assert set_realizes(ws, item.id, []).realizes == []
    assert ws.load_item(item.id).realizes == []


@pytest.mark.parametrize("slugs", [[""], ["   "], ["feature/login", "feature/login"]])
def test_set_realizes_rejects_blank_or_duplicate_without_writing(
    tmp_path: Path, slugs: list[str]
) -> None:
    ws = _ws(tmp_path)
    item = create_item(ws, "story", "Goal", realizes=["feature/keep"], accept="children")

    with pytest.raises(ValueError, match="realizes"):
        set_realizes(ws, item.id, slugs)

    assert ws.load_item(item.id).realizes == ["feature/keep"]


def test_realizes_does_not_invent_a_slug_grammar(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    item = create_item(ws, "story", "Goal", accept="children")

    assert set_realizes(ws, item.id, ["Any nonblank slug!"]).realizes == ["Any nonblank slug!"]


def test_move_reparents_and_reorders_among_destination_siblings(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    old_parent = create_item(ws, "story", "Old", accept="children")
    new_parent = create_item(ws, "epic", "New", accept="children")
    moved = create_item(ws, "action", "Moved", gate="true", parent=old_parent.id)
    first = create_item(ws, "task", "First", gate="true", parent=new_parent.id)
    second = create_item(ws, "task", "Second", gate="true", parent=new_parent.id)

    result = move_item(ws, moved.id, new_parent.id, 1)

    assert result.id == moved.id
    assert ws.load_item(old_parent.id).children == []
    assert ws.load_item(new_parent.id).children == [first.id, moved.id, second.id]


def test_move_reorders_within_one_parent_and_none_means_end(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    parent = create_item(ws, "story", "Parent", accept="children")
    first = create_item(ws, "action", "First", gate="true", parent=parent.id)
    second = create_item(ws, "task", "Second", gate="true", parent=parent.id)
    third = create_item(ws, "step", "Third", gate="true", parent=parent.id)

    move_item(ws, third.id, parent.id, 0)
    assert ws.load_item(parent.id).children == [third.id, first.id, second.id]

    move_item(ws, third.id, parent.id, None)
    assert ws.load_item(parent.id).children == [first.id, second.id, third.id]


def test_move_to_root_succeeds_but_root_index_is_rejected(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    parent = create_item(ws, "story", "Parent", accept="children")
    child = create_item(ws, "action", "Child", gate="true", parent=parent.id)

    move_item(ws, child.id, None, None)
    assert ws.load_item(parent.id).children == []

    with pytest.raises(PlanningError, match="root order.*ID|index"):
        move_item(ws, child.id, None, 0)


@pytest.mark.parametrize("index", [-1, 2])
def test_move_rejects_invalid_sibling_index(tmp_path: Path, index: int) -> None:
    ws = _ws(tmp_path)
    parent = create_item(ws, "story", "Parent", accept="children")
    child = create_item(ws, "action", "Child", gate="true", parent=parent.id)

    with pytest.raises(PlanningError, match="index.*range"):
        move_item(ws, child.id, parent.id, index)

    assert ws.load_item(parent.id).children == [child.id]


@pytest.mark.parametrize("destination", ["self", "descendant"])
def test_move_rejects_self_or_descendant_without_writing(tmp_path: Path, destination: str) -> None:
    ws = _ws(tmp_path)
    root = create_item(ws, "initiative", "Root", accept="children")
    child = create_item(ws, "story", "Child", parent=root.id, accept="children")
    grandchild = create_item(ws, "action", "Leaf", gate="true", parent=child.id)
    new_parent = root.id if destination == "self" else grandchild.id

    with pytest.raises(PlanningError, match="itself|descendant"):
        move_item(ws, root.id, new_parent, None)

    assert ws.load_item(root.id).children == [child.id]
    assert ws.load_item(child.id).children == [grandchild.id]


def test_move_rejects_gated_destination_without_writing(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    source = create_item(ws, "story", "Source", accept="children")
    moved = create_item(ws, "action", "Moved", gate="true", parent=source.id)
    gated = create_item(ws, "task", "Gated", gate="true")

    with pytest.raises(PlanningError, match="gate|gated"):
        move_item(ws, moved.id, gated.id, None)

    assert ws.load_item(source.id).children == [moved.id]
    assert ws.load_item(gated.id).children == []


@pytest.mark.parametrize(("item_id", "parent_id"), [("MISSING", None), ("ACT-001", "MISSING")])
def test_move_rejects_unknown_ids(tmp_path: Path, item_id: str, parent_id: str | None) -> None:
    ws = _ws(tmp_path)
    create_item(ws, "action", "Known", gate="true")

    with pytest.raises(PlanningError, match="unknown.*MISSING"):
        move_item(ws, item_id, parent_id, None)


def test_move_rejects_new_inherited_order_cycle_without_writing(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    first = create_item(ws, "story", "First", accept="children")
    second = create_item(ws, "epic", "Second", accept="children")
    waiting = create_item(ws, "action", "Wait", gate="true", parent=first.id)
    create_item(ws, "task", "Other", gate="true", parent=second.id)
    add_after(ws, waiting.id, second.id)

    with pytest.raises(OrderError, match="never be satisfied"):
        move_item(ws, first.id, second.id, None)

    assert ws.load_item(first.id).children == [waiting.id]
    assert first.id not in ws.load_item(second.id).children


@pytest.mark.parametrize("gate", ["", "true"])
def test_move_rejects_waiting_item_becoming_parent_of_predecessor(
    tmp_path: Path, gate: str
) -> None:
    ws = _ws(tmp_path)
    epic = create_item(ws, "epic", "Epic", accept="children")
    first = create_item(ws, "action", "First", parent=epic.id, accept="children")
    second = create_item(ws, "action", "Second", parent=epic.id, accept="children")
    create_item(ws, "action", "Unrelated third", accept="children")
    create_item(ws, "action", "Unrelated fourth", accept="children")
    waiting = create_item(ws, "action", "Waiting", parent=epic.id, accept="children")
    predecessor = create_item(
        ws,
        "action",
        "Predecessor",
        gate=gate,
        parent=epic.id,
        accept="gate" if gate else "children",
    )
    add_after(ws, waiting.id, predecessor.id)
    assert ws.load_item(epic.id).children == [
        first.id,
        second.id,
        waiting.id,
        predecessor.id,
    ]
    before_epic = ws.item_path(epic.id).read_text()
    before_waiting = ws.item_path(waiting.id).read_text()

    with pytest.raises(OrderWaitsOnDescendantError) as exc_info:
        move_item(ws, predecessor.id, waiting.id, None)

    assert exc_info.value.code == "order_waits_on_descendant"
    assert ws.item_path(epic.id).read_text() == before_epic
    assert ws.item_path(waiting.id).read_text() == before_waiting


@pytest.mark.parametrize("gate", ["", "true"])
def test_add_after_rejects_parent_waiting_on_child(tmp_path: Path, gate: str) -> None:
    ws = _ws(tmp_path)
    parent = create_item(ws, "story", "Parent", accept="children")
    child = create_item(
        ws, "action", "Child", gate=gate, parent=parent.id, accept="gate" if gate else "children"
    )
    before = ws.item_path(parent.id).read_text()

    with pytest.raises(OrderWaitsOnDescendantError) as exc_info:
        add_after(ws, parent.id, child.id)

    assert exc_info.value.code == "order_waits_on_descendant"
    assert ws.item_path(parent.id).read_text() == before


@pytest.mark.parametrize("gate", ["", "true"])
def test_create_rejects_legacy_parent_waiting_on_would_be_sibling_chain(
    tmp_path: Path, gate: str
) -> None:
    ws = _ws(tmp_path)
    parent = create_item(ws, "story", "Parent", accept="children")
    sibling = create_item(
        ws, "action", "Sibling", gate=gate, parent=parent.id, accept="gate" if gate else "children"
    )
    ws.write_item(parent.model_copy(update={"children": [sibling.id], "after": [sibling.id]}))
    before_items = ws.list_items()
    before_parent = ws.item_path(parent.id).read_text()

    with pytest.raises(OrderWaitsOnDescendantError) as exc_info:
        create_item(
            ws,
            "task",
            "New sibling",
            gate=gate,
            parent=parent.id,
            accept="gate" if gate else "children",
        )

    assert exc_info.value.code == "order_waits_on_descendant"
    assert ws.list_items() == before_items
    assert ws.item_path(parent.id).read_text() == before_parent


def test_move_rolls_status_down_at_destination_and_up_at_source(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    source = create_item(ws, "story", "Source", accept="children")
    done_sibling = create_item(ws, "action", "Done", gate="true", parent=source.id)
    moved = create_item(ws, "task", "Open", gate="true", parent=source.id)
    destination = create_item(ws, "epic", "Destination", accept="children")
    destination_child = create_item(ws, "step", "Already done", gate="true", parent=destination.id)
    for item_id in (done_sibling.id, destination_child.id, destination.id):
        ws.write_item(ws.load_item(item_id).model_copy(update={"status": "done"}))

    move_item(ws, moved.id, destination.id, None)

    assert ws.load_item(source.id).status == "done"
    assert ws.load_item(destination.id).status == "todo"
    assert ws.load_item(moved.id).status == "todo"


def test_move_done_child_rolls_up_destination(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    source = create_item(ws, "story", "Source", accept="children")
    moved = create_item(ws, "action", "Moved", gate="true", parent=source.id)
    destination = create_item(ws, "epic", "Destination", accept="children")
    sibling = create_item(ws, "task", "Done", gate="true", parent=destination.id)
    for item_id in (moved.id, sibling.id):
        ws.write_item(ws.load_item(item_id).model_copy(update={"status": "done"}))

    move_item(ws, moved.id, destination.id, None)

    assert ws.load_item(destination.id).status == "done"


def test_move_restores_destination_if_source_write_fails(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    ws = _ws(tmp_path)
    source = create_item(ws, "story", "Source", accept="children")
    destination = create_item(ws, "epic", "Destination", accept="children")
    moved = create_item(ws, "action", "Moved", gate="true", parent=source.id)
    original_write = ws.write_item
    failed = False

    def fail_source_once(item):  # type: ignore[no-untyped-def]
        nonlocal failed
        if item.id == source.id and not failed:
            failed = True
            raise OSError("simulated source write failure")
        original_write(item)

    monkeypatch.setattr(ws, "write_item", fail_source_once)

    with pytest.raises(OSError, match="simulated"):
        move_item(ws, moved.id, destination.id, None)

    assert ws.load_item(source.id).children == [moved.id]
    assert ws.load_item(destination.id).children == []


def test_add_and_remove_after_are_idempotent(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    first = create_item(ws, "action", "First", gate="true")
    second = create_item(ws, "task", "Second", gate="true")

    assert add_after(ws, second.id, first.id).after == [first.id]
    unchanged_text = ws.item_path(second.id).read_text()
    assert add_after(ws, second.id, first.id).after == [first.id]
    assert ws.item_path(second.id).read_text() == unchanged_text

    assert remove_after(ws, second.id, first.id).after == []
    cleared_text = ws.item_path(second.id).read_text()
    assert remove_after(ws, second.id, first.id).after == []
    assert ws.item_path(second.id).read_text() == cleared_text


def test_add_after_reuses_complete_graph_validation(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    first = create_item(ws, "action", "First", gate="true")
    second = create_item(ws, "task", "Second", gate="true")
    add_after(ws, first.id, second.id)

    with pytest.raises(OrderError, match="cycle"):
        add_after(ws, second.id, first.id)

    assert ws.load_item(second.id).after == []
