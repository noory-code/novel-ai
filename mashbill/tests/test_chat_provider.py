"""Workspace-scoped chat provider selection store (D-2026-06-11-E, Phase B step B3).

The user's chat-CLI choice lives in ``<workspace>/.noory/novel/chat-provider``
(JSON ``{"provider": "claude-code" | "codex" | "gemini" | null}``). The HTTP
surface exposes GET + PUT so the viewer can read the persisted choice on
open and write the user's pick. Pinned here:

  - Fresh workspace → GET returns ``{"provider": null}`` (no file, no 404).
  - PUT a known provider → file lands; subsequent GET reflects it.
  - PUT ``{"provider": null}`` → file is reset (selection cleared).
  - PUT with an unknown provider value → 422 (pydantic rejects).
  - PUT/GET without ``project_path`` → 400.
  - The file is workspace-scoped: a second workspace keeps its own choice.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from mashbill.broadcast import BroadcastHub
from mashbill.http_app import create_http_app


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "ws"
    ws.mkdir()
    return ws


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_http_app(hub=BroadcastHub(enable_watchers=False)))


def test_get_chat_provider_returns_null_on_fresh_workspace(
    workspace: Path, client: TestClient
) -> None:
    resp = client.get("/api/chat/provider", params={"project_path": str(workspace)})
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"provider": None, "model": None}


def test_put_chat_provider_persists_and_returns_value(
    workspace: Path, client: TestClient
) -> None:
    resp = client.put(
        "/api/chat/provider",
        params={"project_path": str(workspace)},
        json={"provider": "claude-code"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"provider": "claude-code", "model": None}

    on_disk = (workspace / ".noory" / "novel" / "chat-provider").read_text(encoding="utf-8")
    assert json.loads(on_disk) == {"provider": "claude-code", "model": None}

    # Round-trip: GET reads it back.
    again = client.get("/api/chat/provider", params={"project_path": str(workspace)})
    assert again.json() == {"provider": "claude-code", "model": None}


def test_put_chat_provider_null_clears_selection(
    workspace: Path, client: TestClient
) -> None:
    client.put(
        "/api/chat/provider",
        params={"project_path": str(workspace)},
        json={"provider": "codex"},
    )
    resp = client.put(
        "/api/chat/provider",
        params={"project_path": str(workspace)},
        json={"provider": None},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"provider": None, "model": None}
    after = client.get("/api/chat/provider", params={"project_path": str(workspace)})
    assert after.json() == {"provider": None, "model": None}


def test_put_chat_provider_unknown_name_is_422(
    workspace: Path, client: TestClient
) -> None:
    resp = client.put(
        "/api/chat/provider",
        params={"project_path": str(workspace)},
        json={"provider": "notarealcli"},
    )
    assert resp.status_code == 422, resp.text


def test_get_chat_provider_without_project_path_is_400(client: TestClient) -> None:
    resp = client.get("/api/chat/provider")
    assert resp.status_code == 400


def test_put_chat_provider_without_project_path_is_400(client: TestClient) -> None:
    resp = client.put("/api/chat/provider", json={"provider": "claude-code"})
    assert resp.status_code == 400


def test_chat_provider_is_workspace_scoped(
    tmp_path: Path, client: TestClient
) -> None:
    ws_a = tmp_path / "ws_a"
    ws_b = tmp_path / "ws_b"
    ws_a.mkdir()
    ws_b.mkdir()
    client.put(
        "/api/chat/provider",
        params={"project_path": str(ws_a)},
        json={"provider": "claude-code"},
    )
    # ws_b stays empty.
    assert client.get(
        "/api/chat/provider", params={"project_path": str(ws_b)}
    ).json() == {"provider": None, "model": None}
    assert client.get(
        "/api/chat/provider", params={"project_path": str(ws_a)}
    ).json() == {"provider": "claude-code", "model": None}
