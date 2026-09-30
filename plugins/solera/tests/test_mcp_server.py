"""The host-neutral MCP surface delegates to Solera's existing core."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from pathlib import Path

import pytest

from solera import mcp_server
from solera.errors import FormatError


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
        "workspace_status",
        "write_feedback",
        "write_retrospective",
    }


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
