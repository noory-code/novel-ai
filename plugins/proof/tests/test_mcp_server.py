"""The host-neutral MCP surface delegates to Proof's append-only log."""

from __future__ import annotations

import asyncio
from pathlib import Path

from proof import mcp_server


def test_tool_catalog_is_pinned() -> None:
    tools = asyncio.run(mcp_server.mcp.list_tools())
    assert {tool.name for tool in tools} == {
        "check_decision",
        "decisions_in_force",
        "list_decisions",
        "record_decision",
        "show_decision",
    }


def test_record_supersede_and_check(tmp_path: Path) -> None:
    root = str(tmp_path)
    first = mcp_server.record_decision(
        root,
        "Use SQLite",
        "Local durability is required.",
        about=["STORY-001"],
    )
    second = mcp_server.record_decision(
        root,
        "Use PostgreSQL",
        "Multi-user deployment is now required.",
        supersedes=first["id"],
        about=["STORY-001"],
    )

    assert [item["id"] for item in mcp_server.list_decisions(root)] == [
        first["id"],
        second["id"],
    ]
    assert [item["id"] for item in mcp_server.decisions_in_force(root)] == [second["id"]]
    assert mcp_server.show_decision(root, first["id"])["title"] == "Use SQLite"
    assert mcp_server.check_decision(root, "STORY-001")["satisfied"] is True
