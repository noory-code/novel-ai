"""HTTP layer for Track 2.5 / D-2026-06-11-E — mashbill MCP registration in
external CLI configs.

Each test isolates ``$HOME`` so the real user configs are never touched.
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from mashbill.broadcast import BroadcastHub
from mashbill.http_app import create_http_app


@pytest.fixture
def fake_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    return tmp_path


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_http_app(hub=BroadcastHub(enable_watchers=False)))


def test_providers_endpoint_lists_all(fake_home: Path, client: TestClient) -> None:
    resp = client.get("/api/mcp/providers")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    names = [p["name"] for p in body["providers"]]
    assert sorted(names) == ["claude-code", "codex"]


def test_providers_endpoint_reports_unregistered_on_fresh_home(
    fake_home: Path, client: TestClient
) -> None:
    body = client.get("/api/mcp/providers").json()
    for p in body["providers"]:
        assert p["registered"] is False


def test_register_endpoint_writes_claude_code_config(fake_home: Path, client: TestClient) -> None:
    resp = client.post("/api/mcp/providers/claude-code/register")
    assert resp.status_code == 201, resp.text
    cfg = json.loads((fake_home / ".claude.json").read_text(encoding="utf-8"))
    assert "mashbill" in cfg["mcpServers"]


def test_register_endpoint_writes_codex_config(fake_home: Path, client: TestClient) -> None:
    resp = client.post("/api/mcp/providers/codex/register")
    assert resp.status_code == 201, resp.text
    cfg = tomllib.loads((fake_home / ".codex" / "config.toml").read_text(encoding="utf-8"))
    assert "mashbill" in cfg["mcp_servers"]


def test_unregister_endpoint_removes_entry(fake_home: Path, client: TestClient) -> None:
    client.post("/api/mcp/providers/claude-code/register")
    resp = client.post("/api/mcp/providers/claude-code/unregister")
    assert resp.status_code == 200, resp.text
    cfg = json.loads((fake_home / ".claude.json").read_text(encoding="utf-8"))
    assert "mashbill" not in cfg["mcpServers"]


def test_unknown_provider_returns_404(fake_home: Path, client: TestClient) -> None:
    resp = client.post("/api/mcp/providers/notarealcli/register")
    assert resp.status_code == 404


def test_register_then_providers_reports_registered(fake_home: Path, client: TestClient) -> None:
    client.post("/api/mcp/providers/codex/register")
    body = client.get("/api/mcp/providers").json()
    codex = next(p for p in body["providers"] if p["name"] == "codex")
    assert codex["registered"] is True
    # The others stay unregistered — register is per-provider.
    others = [p for p in body["providers"] if p["name"] != "codex"]
    for p in others:
        assert p["registered"] is False
