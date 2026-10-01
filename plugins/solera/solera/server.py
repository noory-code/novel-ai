"""Standalone localhost runner for Solera's HTTP and WebSocket engine."""

from __future__ import annotations

import logging
import os

DEFAULT_HTTP_PORT = 5191


def resolved_port() -> int:
    """Return ``SOLERA_PORT`` when valid, otherwise the fixed default."""
    try:
        port = int(os.environ.get("SOLERA_PORT", str(DEFAULT_HTTP_PORT)))
    except ValueError:
        return DEFAULT_HTTP_PORT
    return port if 1 <= port <= 65535 else DEFAULT_HTTP_PORT


def run_http_only() -> None:
    """Run the HTTP/WS engine on loopback only."""
    import uvicorn

    from .http_app import create_http_app

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    uvicorn.run(
        create_http_app(),
        host="127.0.0.1",
        port=resolved_port(),
        log_level="info",
    )
