"""Pin the public Distill MCP catalog used by host allow-lists."""

from __future__ import annotations

import asyncio

from distill.server import mcp


def test_mcp_tool_catalog_is_pinned() -> None:
    tools = asyncio.run(mcp.get_tools())
    assert set(tools) == {
        "digest",
        "criteria_check",
        "criteria_current",
        "criteria_history",
        "criteria_record",
        "criteria_revise",
        "criteria_revoke",
        "ingest",
        "init",
        "learn",
        "manage_entry",
        "memory",
        "profile",
        "recall",
        "store",
    }
