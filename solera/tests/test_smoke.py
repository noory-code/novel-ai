"""Smoke tests for the package scaffold."""

from __future__ import annotations

import solera_mcp


def test_version_present() -> None:
    assert solera_mcp.__version__ == "0.0.1"


def test_server_module_importable() -> None:
    from solera_mcp import server

    assert callable(server.run)
