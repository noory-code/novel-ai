"""Server entrypoints — D-2026-06-14-A.

``run_mcp_stdio`` is the entry the bundled .app binary uses when an external
CLI launches Novel as a registered MCP server. It must drive ONLY the stdio
MCP transport — starting another HTTP server would collide with the already
running sidecar on :5190 and is pointless for a stdio client.

The transport coroutine is faked so the test stays hermetic (no real stdin
loop, no socket).
"""

from __future__ import annotations

import pytest

import mashbill.server as server


def test_run_mcp_stdio_drives_only_the_stdio_transport(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _coro() -> None:
        return None

    made = _coro()
    monkeypatch.setattr(server.mcp, "run_stdio_async", lambda: made)

    ran: dict[str, object] = {}

    def fake_run(coro: object) -> None:
        ran["arg"] = coro
        # Close the coroutine so pytest doesn't warn it was never awaited.
        getattr(coro, "close", lambda: None)()

    monkeypatch.setattr(server.asyncio, "run", fake_run)

    def boom(*_a: object, **_k: object) -> object:
        raise AssertionError("HTTP server must not start in stdio-only mode")

    monkeypatch.setattr(server, "create_http_app", boom)
    monkeypatch.setattr(server.uvicorn, "run", boom)

    server.run_mcp_stdio()

    assert ran["arg"] is made
