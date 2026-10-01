"""Public HTTP and WebSocket contract for the Solera engine."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast

import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from solera import __version__
from solera.broadcast import BroadcastHub
from solera.http_app import create_http_app
from solera.workspace import Workspace


@pytest.fixture
def hub() -> BroadcastHub:
    return BroadcastHub(enable_watchers=False)


@pytest.fixture
def client(hub: BroadcastHub) -> Iterator[TestClient]:
    with TestClient(create_http_app(hub=hub)) as test_client:
        yield test_client


def _query(root: Path) -> dict[str, str]:
    return {"project_path": str(root)}


def _ws(root: Path) -> Workspace:
    return Workspace(root / ".noory" / "solera")


def _create(
    client: TestClient,
    root: Path,
    *,
    parent: str | None = None,
    goal: str = "Goal",
    level: str | None = None,
    gate: str | None = None,
    realizes: list[str] | None = None,
    after: list[str] | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {"parent": parent, "goal": goal}
    for key, value in {
        "level": level,
        "gate": gate,
        "realizes": realizes,
        "after": after,
    }.items():
        if value is not None:
            body[key] = value
    response = client.post("/api/work/items", params=_query(root), json=body)
    assert response.status_code == 201, response.text
    return cast(dict[str, Any], response.json())


def test_health_is_open_and_reports_engine_version(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SOLERA_AUTH_TOKEN", "secret")

    response = client.get("/api/health")
    wrong_method = client.post("/api/health")

    assert response.status_code == 200
    assert response.json() == {"ok": True, "engine": "solera", "version": __version__}
    assert wrong_method.status_code == 401


def test_work_returns_empty_state_without_creating_a_workspace(
    client: TestClient, tmp_path: Path
) -> None:
    response = client.get("/api/work", params=_query(tmp_path))

    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "progress": {},
        "ready": [],
        "blocked": [],
        "current": None,
    }
    assert not (tmp_path / ".noory").exists()


def test_work_returns_items_progress_readiness_and_pointer(
    client: TestClient, tmp_path: Path
) -> None:
    predecessor = _create(client, tmp_path, goal="First", level="initiative")
    story = _create(client, tmp_path, goal="Story")
    ready = _create(client, tmp_path, parent=story["id"], gate="true", goal="Ready")
    blocked = _create(
        client,
        tmp_path,
        parent=story["id"],
        gate="true",
        goal="Blocked",
        after=[predecessor["id"]],
    )
    ws = _ws(tmp_path)
    ws.write_item(ws.load_item(ready["id"]).model_copy(update={"status": "done"}))

    response = client.get("/api/work", params=_query(tmp_path))

    assert response.status_code == 200
    body = response.json()
    expected_ids = {predecessor["id"], blocked["id"], ready["id"], story["id"]}
    assert [item["id"] for item in body["items"]] == sorted(expected_ids)
    assert body["progress"][story["id"]] == {"done": 1, "total": 2, "percent": 50}
    assert body["ready"] == []
    assert body["blocked"] == [
        {
            "id": blocked["id"],
            "waiting_on": [predecessor["id"]],
            "reasons": [f"{blocked['id']} waits for {predecessor['id']}"],
        }
    ]
    assert body["current"] is None


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("GET", "/api/work", None),
        ("POST", "/api/work/by-slugs", {"slugs": []}),
        ("POST", "/api/work/items", {"parent": None, "goal": "Goal"}),
        ("PATCH", "/api/work/items/STORY-001", {"goal": "Goal"}),
        (
            "POST",
            "/api/work/items/STORY-001/move",
            {"parent": None, "index": None},
        ),
        (
            "POST",
            "/api/work/items/STORY-001/after",
            {"predecessor": "STORY-002"},
        ),
        ("DELETE", "/api/work/items/STORY-001/after/STORY-002", None),
    ],
)
def test_every_project_route_rejects_relative_project_path(
    client: TestClient,
    method: str,
    path: str,
    body: dict[str, Any] | None,
) -> None:
    response = client.request(
        method,
        path,
        params={"project_path": "relative/project"},
        json=body,
    )

    assert response.status_code == 400
    assert "project_path" in response.json()["error"]


def test_project_routes_reject_missing_project_path(client: TestClient) -> None:
    response = client.get("/api/work")

    assert response.status_code == 400
    assert "project_path" in response.json()["error"]


def test_by_slugs_returns_every_requested_slug_and_mcp_order(
    client: TestClient, tmp_path: Path
) -> None:
    first = _create(
        client,
        tmp_path,
        goal="First",
        realizes=["feature/login", "entity/account"],
    )
    second = _create(client, tmp_path, goal="Second", realizes=["feature/login"])

    response = client.post(
        "/api/work/by-slugs",
        params=_query(tmp_path),
        json={"slugs": ["feature/login", "feature/missing", "entity/account"]},
    )

    assert response.status_code == 200
    assert response.json() == {
        "by_slug": {
            "feature/login": [first["id"], second["id"]],
            "feature/missing": [],
            "entity/account": [first["id"]],
        }
    }


@pytest.mark.parametrize("body", [{}, {"slugs": "feature/login"}, {"slugs": [1]}])
def test_by_slugs_rejects_invalid_json_shape(
    client: TestClient, tmp_path: Path, body: dict[str, Any]
) -> None:
    response = client.post("/api/work/by-slugs", params=_query(tmp_path), json=body)

    assert response.status_code == 400
    assert "error" in response.json()


def test_create_root_and_child_use_core_defaults(client: TestClient, tmp_path: Path) -> None:
    root = _create(client, tmp_path, goal="Root")
    child = _create(client, tmp_path, parent=root["id"], goal="Child", gate="pytest -q")

    assert root["level"] == "story"
    assert child["level"] == "action"
    assert child["gate"] == "pytest -q"
    assert _ws(tmp_path).load_item(root["id"]).children == [child["id"]]


def test_create_maps_validation_to_400_and_unknown_parent_to_404(
    client: TestClient, tmp_path: Path
) -> None:
    invalid = client.post(
        "/api/work/items",
        params=_query(tmp_path),
        json={"parent": None, "goal": "   "},
    )
    missing = client.post(
        "/api/work/items",
        params=_query(tmp_path),
        json={"parent": "STORY-999", "goal": "Child"},
    )

    assert invalid.status_code == 400
    assert "goal" in invalid.json()["error"]
    assert missing.status_code == 404
    assert missing.json() == {"error": "unknown work item: STORY-999"}


def test_patch_updates_goal_and_realizes(client: TestClient, tmp_path: Path) -> None:
    item = _create(client, tmp_path)

    response = client.patch(
        f"/api/work/items/{item['id']}",
        params=_query(tmp_path),
        json={"goal": "Updated", "realizes": ["feature/login"]},
    )

    assert response.status_code == 200
    assert response.json()["goal"] == "Updated"
    assert response.json()["realizes"] == ["feature/login"]


def test_patch_rejects_empty_patch_and_maps_unknown_item(
    client: TestClient, tmp_path: Path
) -> None:
    item = _create(client, tmp_path)

    invalid = client.patch(f"/api/work/items/{item['id']}", params=_query(tmp_path), json={})
    missing = client.patch(
        "/api/work/items/STORY-999", params=_query(tmp_path), json={"goal": "New"}
    )

    assert invalid.status_code == 400
    assert "at least one" in invalid.json()["error"]
    assert missing.status_code == 404
    assert missing.json() == {"error": "unknown work item: STORY-999"}


def test_move_returns_every_rewritten_item(client: TestClient, tmp_path: Path) -> None:
    old_parent = _create(client, tmp_path, goal="Old")
    new_parent = _create(client, tmp_path, goal="New", level="epic")
    moved = _create(client, tmp_path, parent=old_parent["id"], gate="true")

    response = client.post(
        f"/api/work/items/{moved['id']}/move",
        params=_query(tmp_path),
        json={"parent": new_parent["id"], "index": 0},
    )

    assert response.status_code == 200
    assert {item["id"] for item in response.json()["items"]} == {
        old_parent["id"],
        new_parent["id"],
    }
    assert _ws(tmp_path).load_item(new_parent["id"]).children == [moved["id"]]


def test_move_maps_rule_error_to_400_and_unknown_ids_to_404(
    client: TestClient, tmp_path: Path
) -> None:
    item = _create(client, tmp_path)

    invalid = client.post(
        f"/api/work/items/{item['id']}/move",
        params=_query(tmp_path),
        json={"parent": None, "index": 0},
    )
    missing_item = client.post(
        "/api/work/items/STORY-999/move",
        params=_query(tmp_path),
        json={"parent": None, "index": None},
    )
    missing_parent = client.post(
        f"/api/work/items/{item['id']}/move",
        params=_query(tmp_path),
        json={"parent": "STORY-999", "index": None},
    )

    assert invalid.status_code == 400
    assert missing_item.status_code == 404
    assert missing_parent.status_code == 404
    assert missing_parent.json() == {"error": "unknown work item: STORY-999"}


def test_add_and_remove_after_are_idempotent_over_http(client: TestClient, tmp_path: Path) -> None:
    predecessor = _create(client, tmp_path, goal="First")
    item = _create(client, tmp_path, goal="Second")
    path = f"/api/work/items/{item['id']}/after"

    first = client.post(path, params=_query(tmp_path), json={"predecessor": predecessor["id"]})
    repeated = client.post(path, params=_query(tmp_path), json={"predecessor": predecessor["id"]})
    removed = client.delete(f"{path}/{predecessor['id']}", params=_query(tmp_path))
    repeated_remove = client.delete(f"{path}/{predecessor['id']}", params=_query(tmp_path))

    assert first.json()["after"] == [predecessor["id"]]
    assert repeated.json()["after"] == [predecessor["id"]]
    assert removed.json()["after"] == []
    assert repeated_remove.json()["after"] == []


def test_after_routes_map_order_error_to_400_and_unknown_item_to_404(
    client: TestClient, tmp_path: Path
) -> None:
    item = _create(client, tmp_path)

    invalid = client.post(
        f"/api/work/items/{item['id']}/after",
        params=_query(tmp_path),
        json={"predecessor": "STORY-999"},
    )
    missing_add = client.post(
        "/api/work/items/STORY-999/after",
        params=_query(tmp_path),
        json={"predecessor": item["id"]},
    )
    missing_delete = client.delete(
        f"/api/work/items/STORY-999/after/{item['id']}", params=_query(tmp_path)
    )

    assert invalid.status_code == 400
    assert "does not exist" in invalid.json()["error"]
    assert missing_add.status_code == 404
    assert missing_delete.status_code == 404


def test_auth_is_dynamic_and_cors_is_present(
    client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    open_response = client.get(
        "/api/work", params=_query(tmp_path), headers={"Origin": "tauri://localhost"}
    )
    monkeypatch.setenv("SOLERA_AUTH_TOKEN", "secret")
    missing = client.get("/api/work", params=_query(tmp_path))
    wrong = client.get(
        "/api/work", params=_query(tmp_path), headers={"Authorization": "Bearer wrong"}
    )
    allowed = client.get(
        "/api/work", params=_query(tmp_path), headers={"Authorization": "bEaReR secret"}
    )

    assert open_response.status_code == 200
    assert open_response.headers["access-control-allow-origin"] == "*"
    assert missing.status_code == 401
    assert missing.json() == {"error": "auth token required"}
    assert wrong.status_code == 401
    assert wrong.json() == {"error": "invalid auth token"}
    assert allowed.status_code == 200


@pytest.mark.parametrize("auth", [None, "wrong"])
def test_websocket_rejects_missing_or_bad_token_with_1008(
    client: TestClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    auth: str | None,
) -> None:
    monkeypatch.setenv("SOLERA_AUTH_TOKEN", "secret")
    suffix = "" if auth is None else f"&auth={auth}"

    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(f"/ws?project_path={tmp_path}{suffix}") as socket:
            socket.receive_json()

    assert exc_info.value.code == 1008


def test_websocket_pushes_work_changed_after_http_write(client: TestClient, tmp_path: Path) -> None:
    with client.websocket_connect(f"/ws?project_path={tmp_path}") as socket:
        _create(client, tmp_path, goal="Changed")

        assert socket.receive_json() == {"event": "work_changed"}
