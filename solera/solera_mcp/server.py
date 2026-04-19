"""Combined MCP (stdio) + HTTP (localhost) server for solera-map.

A single asyncio event loop hosts two transports side-by-side:

- FastMCP over stdio for Claude Code tool calls
- Starlette + uvicorn over http://127.0.0.1:{port} for the browser viewer

Both transports read the same ``Graph`` built by
:func:`solera_mcp.graph.build_graph` against a Solera root directory
supplied by the caller. The server holds no process-wide project state —
every request resolves its own ``project_path``.

This module used to own the whole server stack; at ~730 LOC it mixed
path-resolution, MCP tools, Starlette endpoints (graph / health / layout /
concept PATCH / propose-from-narrative), WebSocket broadcasting, and the
uvicorn entry points. The pieces are now split:

- :mod:`solera_mcp.workspace`        — ``resolve_solera_root`` / port helpers
- :mod:`solera_mcp.broadcast`        — ``BroadcastHub``
- :mod:`solera_mcp.api_endpoints`    — basic HTTP handlers
- :mod:`solera_mcp.concept_propose`  — ``POST /api/concept/propose-from-narrative``
- :mod:`solera_mcp.http_app`         — ``create_http_app``
- :mod:`solera_mcp.mcp_tools`        — FastMCP instance + tools

The public surface of ``solera_mcp.server`` — ``run``, ``run_http_only``,
``create_http_app``, ``BroadcastHub``, ``resolve_solera_root``, and the
legacy ``resolve_workspace`` alias — is preserved via re-exports so
``__main__.py`` and existing tests keep working unchanged.

Port selection:
- Default 5170; override via ``SOLERA_MAP_PORT``.
- If the port is in use, the HTTP server logs a warning and skips HTTP
  startup — the MCP transport remains usable so the plugin still works.
"""

from __future__ import annotations

import asyncio
import logging
import os

import uvicorn

from solera_mcp.broadcast import BroadcastHub
from solera_mcp.http_app import create_http_app
from solera_mcp.mcp_tools import get_map, mcp, open_map
from solera_mcp.workspace import (
    DEFAULT_HTTP_PORT,
    find_viewer_dist,
    port_is_free,
    resolve_solera_root,
    resolve_workspace,
    resolved_port,
)

__all__ = [
    # Entry points
    "run",
    "run_http_only",
    # Composition
    "create_http_app",
    "BroadcastHub",
    # Path resolution (backwards compat re-exports)
    "resolve_solera_root",
    "resolve_workspace",
    # Tools (imported for side-effect of FastMCP registration; re-exported
    # for tests/introspection)
    "mcp",
    "get_map",
    "open_map",
    # Port / dist helpers (rarely needed externally, but re-exported to
    # preserve every public name the old server.py exposed)
    "DEFAULT_HTTP_PORT",
    "find_viewer_dist",
    "port_is_free",
    "resolved_port",
]

_log = logging.getLogger(__name__)


async def _serve() -> None:
    hub = BroadcastHub()
    http_app = create_http_app(hub=hub)
    port = resolved_port()

    # `SOLERA_MAP_NO_MCP=1` skips the MCP stdio task. Set by the VSCode
    # extension's spawn helper, which only consumes the HTTP+WS interface and
    # would otherwise leak a stdio reader that has no client. Default behavior
    # (Claude Code plugin invocation) keeps stdio on.
    skip_mcp = os.environ.get("SOLERA_MAP_NO_MCP", "").lower() in ("1", "true", "yes")
    tasks: list[asyncio.Task[None]] = []
    if not skip_mcp:
        tasks.append(asyncio.create_task(mcp.run_stdio_async(), name="mcp-stdio"))
    else:
        _log.info("SOLERA_MAP_NO_MCP set; skipping MCP stdio transport")

    if port_is_free(port):
        http_config = uvicorn.Config(
            http_app,
            host="127.0.0.1",
            port=port,
            log_level="warning",
            access_log=False,
        )
        http_server = uvicorn.Server(http_config)
        tasks.append(asyncio.create_task(http_server.serve(), name="http"))
    else:
        _log.warning(
            "HTTP port %d in use; another solera-map instance may already serve the browser. "
            "MCP stdio transport remains available.",
            port,
        )

    if not tasks:
        # Defensive: skip_mcp + port busy → nothing to serve. Avoid hanging.
        _log.error("No transports to start (MCP skipped, HTTP port busy). Exiting.")
        return

    try:
        await asyncio.gather(*tasks)
    finally:
        await hub.shutdown()


def run() -> None:
    """Entry point invoked by ``python -m solera_mcp``."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    try:
        asyncio.run(_serve())
    except KeyboardInterrupt:
        pass


def run_http_only() -> None:
    """Run only the HTTP server — useful for ``npm run dev`` against an
    existing browser, or for manual end-to-end verification without an
    MCP client.
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    hub = BroadcastHub()
    app = create_http_app(hub=hub)
    port = resolved_port()
    try:
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
    except KeyboardInterrupt:
        pass
    finally:
        # Sync shutdown — acceptable since we own the loop.
        asyncio.run(hub.shutdown())
