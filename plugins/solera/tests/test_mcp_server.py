"""The host-neutral MCP surface delegates to Solera's existing core."""

from __future__ import annotations

import asyncio
import importlib
import sys
from collections.abc import Callable
from pathlib import Path

import pytest
from fastmcp.exceptions import ValidationError as FastMCPValidationError

from solera import mcp_server
from solera.errors import FormatError, OrderError, PlanningError
from solera.formats import WorkItem
from solera.workspace import Workspace


def _mark_imported_design(root: Path) -> None:
    release = root / ".noory" / "solera" / "specs" / "auth"
    (release / "service").mkdir(parents=True)
    (release / "project").mkdir()
    (release / "service" / "manifest.json").write_text("{}")
    (release / "project" / "manifest.json").write_text("{}")


def test_tool_catalog_is_pinned() -> None:
    tools = asyncio.run(mcp_server.mcp.list_tools())
    assert {tool.name for tool in tools} == {
        "add_work_item",
        "add_work_item_after",
        "apply_spec_repin",
        "complete_current",
        "import_spec",
        "move_work_item",
        "next_work_item",
        "plan_work",
        "propose_spec_repin",
        "ready_work_items",
        "remove_work_item_after",
        "set_work_item_after",
        "set_work_item_goal",
        "set_work_item_phase",
        "set_work_item_realizes",
        "workspace_status",
        "work_items_by_slugs",
        "write_feedback",
        "write_retrospective",
    }


def test_mcp_import_does_not_require_starlette(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delitem(sys.modules, "solera.mcp_server")
    monkeypatch.setitem(sys.modules, "starlette", None)

    imported = importlib.import_module("solera.mcp_server")

    assert imported.__name__ == "solera.mcp_server"


def test_work_items_by_slugs_returns_all_requested_keys(tmp_path: Path) -> None:
    root = str(tmp_path)
    first = mcp_server.plan_work(root, "First", accept="children")
    second = mcp_server.plan_work(root, "Second", accept="children")
    mcp_server.set_work_item_realizes(root, first["id"], ["feature/login"])
    mcp_server.set_work_item_realizes(root, second["id"], ["feature/login", "entity/account"])

    assert mcp_server.work_items_by_slugs(
        root, ["feature/login", "feature/missing", "entity/account"]
    ) == {
        "by_slug": {
            "feature/login": [first["id"], second["id"]],
            "feature/missing": [],
            "entity/account": [second["id"]],
        }
    }


def test_set_work_item_phase_records_phase_without_changing_status(tmp_path: Path) -> None:
    root = str(tmp_path)
    item = mcp_server.plan_work(root, "Explore", accept="children")

    updated = mcp_server.set_work_item_phase(root, item["id"], "exploring", "Unknown API")

    assert updated["phase"] == "exploring"
    assert updated["phase_note"] == "Unknown API"
    assert updated["status"] == "todo"


def test_mcp_creation_requires_accept_without_a_gate(tmp_path: Path) -> None:
    with pytest.raises(PlanningError) as caught:
        mcp_server.plan_work(str(tmp_path), "Ambiguous")

    assert caught.value.code == "accept_required"


def test_mcp_cannot_edit_or_move_a_protected_item(tmp_path: Path) -> None:
    root = str(tmp_path)
    ws = Workspace(tmp_path / ".noory" / "solera")
    ws.write_item(
        WorkItem(
            id="RESULT-001",
            level="result",
            status="done",
            goal="Protected",
            accept="person",
        )
    )
    box = mcp_server.plan_work(root, "Box", accept="children")

    with pytest.raises(PlanningError) as edit:
        mcp_server.set_work_item_goal(root, "RESULT-001", "Changed")
    with pytest.raises(PlanningError) as move:
        mcp_server.move_work_item(root, "RESULT-001", box["id"])

    assert edit.value.code == "item_protected"
    assert move.value.code == "item_protected"


def test_edit_tools_delegate_to_core_and_return_items(tmp_path: Path) -> None:
    root = str(tmp_path)
    first = mcp_server.plan_work(root, "First", accept="children")
    second = mcp_server.plan_work(root, "Second", level="epic", accept="children")
    child = mcp_server.add_work_item(root, first["id"], "Child", gate="true")

    assert mcp_server.set_work_item_goal(root, child["id"], "Updated")["goal"] == "Updated"
    assert mcp_server.set_work_item_realizes(root, child["id"], ["feature/login"])["realizes"] == [
        "feature/login"
    ]
    assert mcp_server.move_work_item(root, child["id"], second["id"], 0)["id"] == child["id"]
    assert mcp_server.add_work_item_after(root, child["id"], first["id"])["after"] == [first["id"]]
    assert mcp_server.remove_work_item_after(root, child["id"], first["id"])["after"] == []


def test_edit_tools_propagate_rejections(tmp_path: Path) -> None:
    root = str(tmp_path)
    item = mcp_server.plan_work(root, "Keep", accept="children")

    with pytest.raises(ValueError, match="goal"):
        mcp_server.set_work_item_goal(root, item["id"], "  ")
    with pytest.raises(PlanningError, match="root order|index"):
        mcp_server.move_work_item(root, item["id"], None, 0)


def test_apply_spec_repin_requires_proposal_id(tmp_path: Path) -> None:
    with pytest.raises(FastMCPValidationError, match="proposal_id"):
        asyncio.run(
            mcp_server.mcp.call_tool(
                "apply_spec_repin",
                {
                    "project_root": str(tmp_path),
                    "old_label": "old",
                    "new_label": "new",
                },
            )
        )


def test_plan_next_and_notes_round_trip(tmp_path: Path) -> None:
    root = str(tmp_path)
    planned = mcp_server.plan_work(root, "Ship the feature", accept="children")
    leaf = mcp_server.add_work_item(
        root,
        planned["id"],
        "Implement the behavior",
        gate="python -m pytest",
        realizes=["feature/login"],
    )

    nxt = mcp_server.next_work_item(root)
    assert nxt["item"]["id"] == leaf["id"]
    assert "python -m pytest" in nxt["instruction"]
    assert mcp_server.workspace_status(root)["current"] == leaf["id"]

    retro = mcp_server.write_retrospective(root, leaf["id"], "Learned X.")
    feedback = mcp_server.write_feedback(root, "FB-001", "Need a decision.")
    assert retro["id"] == leaf["id"]
    assert feedback["id"] == "FB-001"


def test_plan_and_add_accept_after(tmp_path: Path) -> None:
    root = str(tmp_path)
    predecessor = mcp_server.plan_work(root, "First", level="initiative", accept="children")
    planned = mcp_server.plan_work(
        root,
        "Second",
        level="story",
        after=[predecessor["id"]],
        accept="children",
    )
    leaf = mcp_server.add_work_item(
        root,
        planned["id"],
        "Step",
        gate="true",
        after=[predecessor["id"]],
    )

    assert planned["after"] == [predecessor["id"]]
    assert leaf["after"] == [predecessor["id"]]


def test_workspace_status_includes_container_progress(tmp_path: Path) -> None:
    root = str(tmp_path)
    story = mcp_server.plan_work(root, "Story", accept="children")
    first = mcp_server.add_work_item(root, story["id"], "One", gate="true")
    mcp_server.add_work_item(root, story["id"], "Two", gate="true")
    ws = Workspace(tmp_path / ".noory" / "solera")
    ws.write_item(ws.load_item(first["id"]).model_copy(update={"status": "done"}))

    status = mcp_server.workspace_status(root)

    assert status["progress"][story["id"]] == {
        "done": 1,
        "total": 2,
        "percent": 50,
    }


def test_workspace_status_reports_legacy_descendant_order_problem(tmp_path: Path) -> None:
    root = str(tmp_path)
    parent = mcp_server.plan_work(root, "Parent", accept="children")
    child = mcp_server.add_work_item(root, parent["id"], "Not split", accept="children")
    ws = Workspace(tmp_path / ".noory" / "solera")
    parent_item = ws.load_item(parent["id"])
    ws.write_item(parent_item.model_copy(update={"after": [child["id"]]}))

    status = mcp_server.workspace_status(root)

    assert any(
        problem["kind"] == "order_waits_on_descendant"
        and parent["id"] in problem["detail"]
        and child["id"] in problem["detail"]
        for problem in status["problems"]
    )


def test_ready_work_items_returns_ready_and_blocked(tmp_path: Path) -> None:
    root = str(tmp_path)
    predecessor = mcp_server.plan_work(root, "Not split", level="initiative", accept="children")
    parent = mcp_server.plan_work(root, "Story", accept="children")
    blocked = mcp_server.add_work_item(
        root,
        parent["id"],
        "Blocked",
        gate="true",
        after=[predecessor["id"]],
    )
    ready = mcp_server.add_work_item(root, parent["id"], "Ready", gate="true")

    result = mcp_server.ready_work_items(root)

    assert result == {
        "ready": [ready["id"]],
        "blocked": [
            {
                "id": blocked["id"],
                "waiting_on": [predecessor["id"]],
                "reasons": [f"{blocked['id']} waits for {predecessor['id']}"],
            }
        ],
    }


def test_ready_and_next_tools_explain_missing_design_node(tmp_path: Path) -> None:
    _mark_imported_design(tmp_path)
    root = str(tmp_path)
    parent = mcp_server.plan_work(root, "Story", accept="children")
    leaf = mcp_server.add_work_item(root, parent["id"], "Disconnected", gate="true")

    result = mcp_server.ready_work_items(root)

    assert result["ready"] == []
    assert result["blocked"][0]["id"] == leaf["id"]
    assert result["blocked"][0]["waiting_on"] == []
    assert result["blocked"][0]["reasons"] == [
        f"leaf {leaf['id']} and its ancestors realize no design slug; name the node "
        "it serves with `realizes` (for example, `feature/login`)"
    ]
    with pytest.raises(OrderError, match="realize no design slug"):
        mcp_server.next_work_item(root)


def test_set_work_item_after_propagates_cycle_error(tmp_path: Path) -> None:
    root = str(tmp_path)
    first_parent = mcp_server.plan_work(root, "First", accept="children")
    second_parent = mcp_server.plan_work(root, "Second", accept="children")
    first = mcp_server.add_work_item(root, first_parent["id"], "One", gate="true")
    second = mcp_server.add_work_item(root, second_parent["id"], "Two", gate="true")
    mcp_server.set_work_item_after(root, first["id"], [second["id"]])

    with pytest.raises(OrderError, match="order links form a cycle"):
        mcp_server.set_work_item_after(root, second["id"], [first["id"]])


@pytest.mark.parametrize(
    ("operation", "arguments"),
    [
        (mcp_server.write_retrospective, ("../outside", "body")),
        (mcp_server.write_feedback, ("../outside", "body")),
        (mcp_server.add_work_item, ("../outside", "goal")),
        (mcp_server.plan_work, ("goal", "../outside")),
    ],
)
def test_tools_reject_path_like_names_without_workspace_data(
    tmp_path: Path, operation: Callable[..., object], arguments: tuple[str, str]
) -> None:
    with pytest.raises(FormatError, match="name"):
        if operation in {mcp_server.add_work_item, mcp_server.plan_work}:
            operation(str(tmp_path), *arguments, accept="children")
        else:
            operation(str(tmp_path), *arguments)

    workspace_root = tmp_path / ".noory" / "solera"
    assert workspace_root.joinpath(".lock").is_file()
    assert set(workspace_root.iterdir()) == {workspace_root / ".lock"}
