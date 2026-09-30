"""Order-link validation and aggregate completion over the work tree."""

from pathlib import Path

import pytest

from solera.audit import audit_workspace
from solera.errors import OrderError
from solera.formats import Progress, WorkItem
from solera.graph import completion, load_items
from solera.planning import create_item, set_after
from solera.supervisor import complete, start_next
from solera.workspace import Workspace


def _ws(tmp_path: Path) -> Workspace:
    return Workspace(tmp_path / ".noory" / "solera")


def test_create_rejects_missing_after_without_writing(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    parent = create_item(ws, "story", "box")
    before_items = ws.list_items()
    before_parent = ws.item_path(parent.id).read_text()

    with pytest.raises(OrderError, match="NOPE-001"):
        create_item(
            ws,
            "action",
            "blocked",
            gate="true",
            parent=parent.id,
            after=["NOPE-001"],
        )

    assert ws.list_items() == before_items
    assert ws.item_path(parent.id).read_text() == before_parent


def test_after_may_reference_leaf_under_another_parent(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    first = create_item(ws, "story", "first")
    predecessor = create_item(ws, "action", "one", gate="true", parent=first.id)
    second = create_item(ws, "story", "second")

    dependent = create_item(
        ws,
        "action",
        "two",
        gate="true",
        parent=second.id,
        after=[predecessor.id],
    )

    assert dependent.after == [predecessor.id]


def test_set_after_rejects_cycle_without_writing(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    a = create_item(ws, "action", "a", gate="true")
    b = create_item(ws, "action", "b", gate="true")
    set_after(ws, a.id, [b.id])
    before = ws.item_path(b.id).read_text()

    with pytest.raises(OrderError, match="cycle|never be satisfied"):
        set_after(ws, b.id, [a.id])

    assert ws.item_path(b.id).read_text() == before


def test_set_after_rejects_unsplit_cycle_without_writing(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    a = create_item(ws, "story", "a")
    b = create_item(ws, "story", "b")
    set_after(ws, a.id, [b.id])
    before = ws.item_path(b.id).read_text()

    with pytest.raises(OrderError, match="order links form a cycle"):
        set_after(ws, b.id, [a.id])

    assert ws.item_path(b.id).read_text() == before


def test_set_after_rejects_three_item_unsplit_cycle(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    a = create_item(ws, "story", "a")
    b = create_item(ws, "story", "b")
    c = create_item(ws, "story", "c")
    set_after(ws, a.id, [b.id])
    set_after(ws, b.id, [c.id])
    before = ws.item_path(c.id).read_text()

    with pytest.raises(OrderError, match="order links form a cycle"):
        set_after(ws, c.id, [a.id])

    assert ws.item_path(c.id).read_text() == before


def test_audit_reports_after_cycle_once(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    a = WorkItem(
        id="A", level="action", status="todo", gate="true", goal="a", after=["B"]
    )
    b = WorkItem(
        id="B", level="action", status="todo", gate="true", goal="b", after=["A"]
    )
    ws.write_item(a)
    ws.write_item(b)

    problems = [problem for problem in audit_workspace(ws) if problem.kind == "after-cycle"]

    assert [problem.detail for problem in problems] == [
        "order links form a cycle: A -> B -> A"
    ]


def test_leaf_cannot_wait_for_its_ancestor(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    story = create_item(ws, "story", "box")
    leaf = create_item(ws, "action", "step", gate="true", parent=story.id)

    with pytest.raises(OrderError, match="never be satisfied"):
        set_after(ws, leaf.id, [story.id])


def test_container_cannot_wait_for_its_descendant(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    story = create_item(ws, "story", "box")
    leaf = create_item(ws, "action", "step", gate="true", parent=story.id)

    with pytest.raises(OrderError, match="never be satisfied"):
        set_after(ws, story.id, [leaf.id])


def test_adding_child_rejects_new_cycle_without_writing(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    a = create_item(ws, "initiative", "ancestor")
    b = create_item(ws, "story", "not split yet", parent=a.id, after=[a.id])
    before_items = ws.list_items()
    before_parent = ws.item_path(b.id).read_text()

    with pytest.raises(OrderError, match="never be satisfied"):
        create_item(ws, "action", "gated leaf", gate="true", parent=b.id)

    assert ws.list_items() == before_items
    assert ws.item_path(b.id).read_text() == before_parent


def test_set_after_validates_duplicates(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    a = create_item(ws, "action", "a", gate="true")
    b = create_item(ws, "action", "b", gate="true")

    with pytest.raises(ValueError, match="after"):
        set_after(ws, a.id, [b.id, b.id])


def test_set_after_empty_removes_key_from_file(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    a = create_item(ws, "action", "a", gate="true")
    b = create_item(ws, "action", "b", gate="true")
    set_after(ws, a.id, [b.id])
    assert "after:" in ws.item_path(a.id).read_text()

    set_after(ws, a.id, [])

    assert "after:" not in ws.item_path(a.id).read_text()


def test_completion_counts_done_leaf_descendants(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    story = create_item(ws, "story", "box")
    first = create_item(ws, "action", "one", gate="true", parent=story.id)
    create_item(ws, "action", "two", gate="true", parent=story.id)
    ws.write_item(first.model_copy(update={"status": "done"}))

    result = completion(load_items(ws))[story.id]

    assert (result.done, result.total, result.percent) == (1, 2, 50)


def test_completion_percentage_rounds_down(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    story = create_item(ws, "story", "box")
    first = create_item(ws, "action", "one", gate="true", parent=story.id)
    create_item(ws, "action", "two", gate="true", parent=story.id)
    create_item(ws, "action", "three", gate="true", parent=story.id)
    ws.write_item(first.model_copy(update={"status": "done"}))

    result = completion(load_items(ws))[story.id]

    assert (result.done, result.total, result.percent) == (1, 3, 33)


def test_completion_counts_leaves_at_all_depths(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    initiative = create_item(ws, "initiative", "top")
    story = create_item(ws, "story", "nested", parent=initiative.id)
    first = create_item(ws, "action", "one", gate="true", parent=story.id)
    create_item(ws, "action", "two", gate="true", parent=story.id)
    create_item(ws, "action", "top leaf", gate="true", parent=initiative.id)
    ws.write_item(first.model_copy(update={"status": "done"}))

    progress = completion(load_items(ws))

    assert (progress[story.id].done, progress[story.id].total) == (1, 2)
    assert (progress[initiative.id].done, progress[initiative.id].total) == (1, 3)


def test_completion_counts_unsplit_child_as_leaf(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    story = create_item(ws, "story", "box")
    leaf = create_item(ws, "action", "done", gate="true", parent=story.id)
    create_item(ws, "action", "not split", parent=story.id)
    ws.write_item(leaf.model_copy(update={"status": "done"}))

    result = completion(load_items(ws))[story.id]

    assert (result.done, result.total, result.percent) == (1, 2, 50)
    assert ws.load_item(story.id).status == "todo"


def test_completion_100_matches_rollup_during_full_loop(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    initiative = create_item(ws, "initiative", "top")
    first = create_item(ws, "story", "first", parent=initiative.id)
    second = create_item(ws, "story", "second", parent=initiative.id)
    create_item(ws, "action", "one", gate="true", parent=first.id)
    create_item(ws, "action", "two", gate="true", parent=first.id)
    create_item(ws, "action", "three", gate="true", parent=second.id)
    ws.write_progress(Progress(item=None))

    while True:
        items = load_items(ws)
        for container_id, value in completion(items).items():
            assert (value.percent == 100) == (items[container_id].status == "done")
        next_id = start_next(ws)
        if next_id is None:
            break
        assert complete(ws, next_id, cwd=tmp_path).passed is True
