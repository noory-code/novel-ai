"""Combined MCP (stdio) + HTTP (localhost) server for Novel."""

from __future__ import annotations

import asyncio
import logging
import os

import uvicorn

from mashbill.broadcast import BroadcastHub
from mashbill.http_app import create_http_app
from mashbill.mcp_tools import mcp
from mashbill.workspace import (
    DEFAULT_HTTP_PORT,
    find_viewer_dist,
    port_is_free,
    resolve_plot_root,
    resolved_port,
)

__all__ = [
    "run",
    "run_mcp_stdio",
    "run_http_only",
    "create_http_app",
    "BroadcastHub",
    "resolve_plot_root",
    "mcp",
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

    # ``MASHBILL_NO_MCP=1`` skips the MCP stdio transport (used by the VSCode
    # extension in v0.2+, where only HTTP+WS is consumed).
    skip_mcp = os.environ.get("MASHBILL_NO_MCP", "").lower() in ("1", "true", "yes")
    tasks: list[asyncio.Task[None]] = []
    if not skip_mcp:
        tasks.append(asyncio.create_task(mcp.run_stdio_async(), name="mcp-stdio"))
    else:
        _log.info("MASHBILL_NO_MCP set; skipping MCP stdio transport")

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
            "HTTP port %d in use; another Novel instance may already serve the browser. "
            "MCP stdio transport remains available.",
            port,
        )

    if not tasks:
        _log.error("No transports to start (MCP skipped, HTTP port busy). Exiting.")
        return

    try:
        await asyncio.gather(*tasks)
    finally:
        await hub.shutdown()


def run() -> None:
    """Entry point invoked by ``python -m mashbill``."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    try:
        asyncio.run(_serve())
    except KeyboardInterrupt:
        pass


def run_mcp_stdio() -> None:
    """Run ONLY the stdio MCP transport — no HTTP server.

    This is the entry the bundled ``.app`` binary uses when an external CLI
    (codex / gemini / claude) launches it as a registered MCP server
    (D-2026-06-14-A: ``mashbill --mcp-stdio``). The HTTP sidecar already runs
    separately on :5190, so starting another HTTP server here would collide on
    the port and is unnecessary for a stdio client.
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    try:
        asyncio.run(mcp.run_stdio_async())
    except KeyboardInterrupt:
        pass


def run_http_only() -> None:
    """Run only the HTTP server — useful for ``npm run dev`` against an
    existing browser, or for manual verification without an MCP client.
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
        asyncio.run(hub.shutdown())
