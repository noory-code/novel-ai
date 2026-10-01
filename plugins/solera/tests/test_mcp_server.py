"""The host-neutral MCP surface delegates to Solera's existing core."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from pathlib import Path

import pytest
from fastmcp.exceptions import ValidationError as FastMCPValidationError

from solera import mcp_server
from solera.errors import FormatError, OrderError
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
        "apply_spec_repin",
        "complete_current",
        "import_spec",
        "next_work_item",
        "plan_work",
        "propose_spec_repin",
        "ready_work_items",
        "set_work_item_after",
        "workspace_status",
        "write_feedback",
        "write_retrospective",
    }


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
    planned = mcp_server.plan_work(root, "Ship the feature")
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
    predecessor = mcp_server.plan_work(root, "First", level="initiative")
    planned = mcp_server.plan_work(root, "Second", level="story", after=[predecessor["id"]])
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
    story = mcp_server.plan_work(root, "Story")
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


def test_ready_work_items_returns_ready_and_blocked(tmp_path: Path) -> None:
    root = str(tmp_path)
    predecessor = mcp_server.plan_work(root, "Not split", level="initiative")
    parent = mcp_server.plan_work(root, "Story")
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
    parent = mcp_server.plan_work(root, "Story")
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
    first_parent = mcp_server.plan_work(root, "First")
    second_parent = mcp_server.plan_work(root, "Second")
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
def test_tools_reject_path_like_names_before_writing(
    tmp_path: Path, operation: Callable[..., object], arguments: tuple[str, str]
) -> None:
    with pytest.raises(FormatError, match="name"):
        operation(str(tmp_path), *arguments)

    assert not (tmp_path / ".noory").exists()
