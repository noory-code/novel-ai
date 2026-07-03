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


def test_module_main_dispatches_mcp_stdio_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    """B-11 (found by the Chrome-UI smoke): ``python -m mashbill --mcp-stdio``
    (the dev-checkout MCP entry) must run the stdio-only transport, never the
    full engine — the full engine also binds the default HTTP port whenever it
    is free, so every in-app coach turn could capture :5190."""
    import sys

    import mashbill.__main__ as entry

    called: dict[str, bool] = {}
    monkeypatch.setattr(entry, "run_mcp_stdio", lambda: called.setdefault("stdio", True))
    monkeypatch.setattr(entry, "run", lambda: called.setdefault("full", True))
    monkeypatch.setattr(sys, "argv", ["mashbill", "--mcp-stdio"])

    entry.main()

    assert called == {"stdio": True}
