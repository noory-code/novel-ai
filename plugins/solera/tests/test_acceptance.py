from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from solera.errors import SoleraError
from solera.formats import Progress, WorkItem
from solera.graph import completion
from solera.planning import create_item, move_item, set_accept, set_goal, set_phase, set_realizes
from solera.supervisor import (
    cancel_item,
    complete,
    find_next_open,
    ready_leaves,
    reject_item,
    reopen_item,
    rollup_item_and_ancestors,
    set_item_status,
)
from solera.workspace import Workspace


def _ws(tmp_path: Path) -> Workspace:
    return Workspace(tmp_path / ".noory" / "solera")


def _write(
    ws: Workspace,
    item_id: str,
    *,
    status: str = "todo",
    gate: str = "",
    children: list[str] | None = None,
    accept: str = "person",
) -> WorkItem:
    item = WorkItem(
        id=item_id,
        level="work",
        status=status,
        gate=gate,
        children=children or [],
        realizes=[],
        after=[],
        goal=item_id,
        accept=accept,
    )
    ws.write_item(item)
    return item


def test_move_bypass_stops_a_person_container_at_review(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    _write(ws, "RESULT-001", accept="person")
    _write(ws, "WORK-001", status="done", gate="true", accept="gate")

    move_item(ws, "WORK-001", "RESULT-001", None)

    assert ws.load_item("RESULT-001").status == "review"


def test_children_rollup_accepts_cancelled_but_not_an_all_cancelled_set(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    _write(
        ws,
        "RESULT-001",
        children=["WORK-001", "WORK-002"],
        accept="children",
    )
    _write(ws, "WORK-001", status="done", gate="true", accept="gate")
    _write(ws, "WORK-002", status="cancelled", accept="person")

    rollup_item_and_ancestors(ws, "RESULT-001")
    assert ws.load_item("RESULT-001").status == "done"

    ws.write_item(ws.load_item("WORK-001").model_copy(update={"status": "cancelled"}))
    ws.write_item(ws.load_item("RESULT-001").model_copy(update={"status": "todo"}))
    rollup_item_and_ancestors(ws, "RESULT-001")
    assert ws.load_item("RESULT-001").status == "todo"


def test_rework_container_waits_for_a_child_to_finish_after_rejection(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    _write(
        ws,
        "RESULT-001",
        status="review",
        children=["WORK-001", "WORK-002"],
        accept="person",
    )
    _write(ws, "WORK-001", status="done", gate="true", accept="gate")
    _write(ws, "WORK-002", status="done", gate="true", accept="gate")

    reject_item(ws, "RESULT-001", "The result is incomplete")
    rollup_item_and_ancestors(ws, "RESULT-001")
    assert ws.load_item("RESULT-001").status == "rework"

    ws.write_item(ws.load_item("WORK-002").model_copy(update={"status": "doing"}))
    ws.write_progress(Progress(item="WORK-002"))
    result = complete(ws, "WORK-002", cwd=tmp_path)

    assert result.passed is True
    assert ws.load_item("RESULT-001").status == "review"


def test_cancel_active_leaf_clears_pointer_and_complete_then_changes_nothing(
    tmp_path: Path,
) -> None:
    ws = _ws(tmp_path)
    _write(ws, "WORK-001", status="doing", gate="true", accept="gate")
    ws.write_progress(Progress(item="WORK-001"))

    cancel_item(ws, "WORK-001", "No longer needed")
    result = complete(ws, "WORK-001", cwd=tmp_path)

    assert ws.load_progress().item is None
    assert ws.load_item("WORK-001").status == "cancelled"
    assert result.passed is False
    assert "pointer" in result.stderr


def test_completion_excludes_cancelled_items_and_frozen_subtrees(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    _write(
        ws,
        "ROOT-001",
        children=["DONE-001", "CANCELLED-001"],
        accept="children",
    )
    _write(ws, "DONE-001", status="done", gate="true", accept="gate")
    _write(
        ws,
        "CANCELLED-001",
        status="cancelled",
        children=["OPEN-001"],
        accept="children",
    )
    _write(ws, "OPEN-001", gate="true", accept="gate")

    progress = completion({item_id: ws.load_item(item_id) for item_id in ws.list_items()})

    assert progress["ROOT-001"].done == 1
    assert progress["ROOT-001"].total == 1
    assert "CANCELLED-001" not in progress


@pytest.mark.parametrize("status", ["review", "done"])
def test_agent_planning_paths_refuse_protected_items(tmp_path: Path, status: str) -> None:
    ws = _ws(tmp_path)
    _write(
        ws,
        "RESULT-001",
        status=status,
        children=["CHILD-001"],
        accept="person",
    )
    _write(ws, "CHILD-001", gate="true", accept="gate")
    _write(ws, "OTHER-001", accept="children")

    operations: list[Callable[[], object]] = [
        lambda: set_goal(ws, "RESULT-001", "Changed"),
        lambda: set_realizes(ws, "RESULT-001", ["feature/x"]),
        lambda: set_phase(ws, "RESULT-001", "executing", "Changed"),
        lambda: set_accept(ws, "RESULT-001", "children"),
        lambda: create_item(
            ws,
            "work",
            "Child",
            parent="RESULT-001",
            gate="true",
            accept="gate",
        ),
        lambda: move_item(ws, "RESULT-001", "OTHER-001", None),
        lambda: move_item(ws, "CHILD-001", "OTHER-001", None),
        lambda: set_item_status(ws, "RESULT-001", "todo"),
    ]

    for operation in operations:
        with pytest.raises(SoleraError) as caught:
            operation()
        assert caught.value.code == "item_protected"


def test_cancelled_items_refuse_phase_changes(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    _write(ws, "WORK-001", status="cancelled", accept="person")

    with pytest.raises(SoleraError) as caught:
        set_phase(ws, "WORK-001", "exploring", "Unknown")

    assert caught.value.code == "check_cancelled"


def test_rework_is_startable_and_cancelled_subtrees_are_not(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    _write(ws, "REWORK-001", status="rework", gate="true", accept="gate")
    _write(
        ws,
        "CANCELLED-001",
        status="cancelled",
        children=["HIDDEN-001"],
        accept="children",
    )
    _write(ws, "HIDDEN-001", gate="true", accept="gate")

    ready, blocked = ready_leaves(ws)

    assert ready == ["REWORK-001"]
    assert blocked == []
    assert find_next_open(ws) == "REWORK-001"


def test_agent_complete_stops_a_person_gated_leaf_at_review(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    _write(ws, "RESULT-001", status="doing", gate="true", accept="person")
    ws.write_progress(Progress(item="RESULT-001"))

    result = complete(ws, "RESULT-001", cwd=tmp_path)

    item = ws.load_item("RESULT-001")
    assert result.passed is True
    assert item.status == "review"
    assert item.gate_passed is True


def test_agent_rollup_never_reopens_a_protected_done_person_ancestor(
    tmp_path: Path,
) -> None:
    ws = _ws(tmp_path)
    _write(
        ws,
        "RESULT-001",
        status="done",
        children=["WORK-001"],
        accept="person",
    )
    _write(ws, "WORK-001", status="doing", gate="true", accept="gate")
    ws.write_progress(Progress(item="WORK-001"))

    assert complete(ws, "WORK-001", cwd=tmp_path).passed is True
    assert ws.load_item("RESULT-001").status == "done"


def test_reopening_a_child_keeps_a_protected_done_person_ancestor(
    tmp_path: Path,
) -> None:
    ws = _ws(tmp_path)
    _write(
        ws,
        "RESULT-001",
        status="done",
        children=["WORK-001"],
        accept="person",
    )
    _write(ws, "WORK-001", status="done", accept="person")

    reopen_item(ws, "WORK-001", "It never met the condition")

    assert ws.load_item("WORK-001").status == "rework"
    assert ws.load_item("RESULT-001").status == "done"
