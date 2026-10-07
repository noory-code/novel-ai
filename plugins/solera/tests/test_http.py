"""Public HTTP and WebSocket contract for the Solera engine."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import AbstractContextManager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from solera import __version__
from solera.broadcast import BroadcastHub
from solera.errors import WorkspaceLockTimeoutError
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


def test_movement_stamps_only_status_phase_note_and_judgments(tmp_path: Path) -> None:
    from solera.formats import Judgment, WorkItem

    now = datetime(2026, 10, 8, tzinfo=UTC)
    ws = Workspace(tmp_path, clock=lambda: now)
    item = WorkItem(id="W-1", level="story", status="todo", goal="Start")
    ws.write_item(item)
    assert ws.load_item("W-1").moved_at == ""
    for patch in (
        {"goal": "Changed"},
        {"realizes": ["feature/a"]},
        {"accept": "children"},
        {"children": ["W-2"]},
        {"after": ["W-3"]},
    ):
        ws.write_item(ws.load_item("W-1").model_copy(update=patch))
        assert ws.load_item("W-1").moved_at == ""
    movement_patches: list[dict[str, Any]] = [
        {"status": "doing"},
        {"phase": "exploring"},
        {"phase_note": "Waiting"},
        {"judgments": [Judgment(action="check", reason="", at=now.isoformat())]},
    ]
    for patch in movement_patches:
        ws.write_item(ws.load_item("W-1").model_copy(update=patch))
        assert ws.load_item("W-1").moved_at == now.isoformat()


def test_work_view_marks_only_active_items_stale_at_seven_days(
    client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from solera.formats import WorkItem

    now = datetime(2026, 10, 8, tzinfo=UTC)
    monkeypatch.setattr("solera.http_endpoints.utc_now", lambda: now)
    ws = _ws(tmp_path)
    for status, age, expected in (
        ("doing", 7, True),
        ("rework", 8, True),
        ("doing", 6, False),
        ("todo", 8, False),
        ("review", 8, False),
        ("done", 8, False),
        ("cancelled", 8, False),
        ("doing", None, False),
    ):
        item_id = f"W-{status}-{age}"
        moved_at = (now - timedelta(days=age)).isoformat() if age is not None else ""
        ws.write_item(
            WorkItem(id=item_id, level="story", status=status, goal="Work", moved_at=moved_at)
        )
    ws.write_item(
        WorkItem(
            id="W-cancelled-parent",
            level="story",
            status="cancelled",
            goal="Stopped",
            children=["W-frozen"],
            accept="children",
        )
    )
    ws.write_item(
        WorkItem(
            id="W-frozen",
            level="action",
            status="doing",
            goal="Frozen",
            moved_at=(now - timedelta(days=8)).isoformat(),
        )
    )
    response = client.get("/api/work", params=_query(tmp_path))
    assert response.status_code == 200
    items = {item["id"]: item for item in response.json()["items"]}
    assert items["W-frozen"]["needs_check"] is False
    for status, age, expected in (
        ("doing", 7, True),
        ("rework", 8, True),
        ("doing", 6, False),
        ("todo", 8, False),
        ("review", 8, False),
        ("done", 8, False),
        ("cancelled", 8, False),
        ("doing", None, False),
    ):
        item = items[f"W-{status}-{age}"]
        assert item["needs_check"] is expected
        assert item["moved_at"] == (
            (now - timedelta(days=age)).isoformat() if age is not None else ""
        )


def test_repeating_same_phase_answer_restarts_movement_clock(
    client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from solera.formats import WorkItem

    now = datetime(2026, 10, 8, tzinfo=UTC)
    monkeypatch.setattr("solera.workspace.utc_now", lambda: now)
    ws = _ws(tmp_path)
    ws.write_item(
        WorkItem(
            id="W-1",
            level="story",
            status="doing",
            goal="Work",
            phase="exploring",
            phase_note="Still exploring",
            moved_at=(now - timedelta(days=8)).isoformat(),
        )
    )
    response = client.patch(
        "/api/work/items/W-1",
        params=_query(tmp_path),
        json={"phase": "exploring", "phase_note": "Still exploring"},
    )
    assert response.status_code == 200
    assert response.json()["moved_at"] == now.isoformat()


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
    accept: str | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {"parent": parent, "goal": goal}
    for key, value in {
        "level": level,
        "gate": gate,
        "realizes": realizes,
        "after": after,
        "accept": accept if accept is not None else ("gate" if gate else "children"),
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
            "names_no_design_node": False,
        }
    ]
    assert body["current"] is None


def test_work_reports_design_connectedness_for_each_blocked_leaf(
    client: TestClient, tmp_path: Path
) -> None:
    ws = _ws(tmp_path)
    release = ws.spec_dir("auth")
    (release / "service").mkdir(parents=True)
    (release / "project").mkdir()
    (release / "service" / "manifest.json").write_text("{}")
    (release / "project" / "manifest.json").write_text("{}")
    predecessor = _create(client, tmp_path, goal="Predecessor", level="initiative")
    disconnected = _create(client, tmp_path, goal="Disconnected", gate="true")
    connected_parent = _create(
        client,
        tmp_path,
        goal="Connected",
        level="epic",
        realizes=["feature/login"],
    )
    connected = _create(
        client,
        tmp_path,
        parent=connected_parent["id"],
        goal="Connected but waiting",
        gate="true",
        after=[predecessor["id"]],
    )

    response = client.get("/api/work", params=_query(tmp_path))

    assert response.status_code == 200
    blocked = {entry["id"]: entry for entry in response.json()["blocked"]}
    assert blocked[disconnected["id"]]["names_no_design_node"] is True
    assert blocked[connected["id"]]["names_no_design_node"] is False


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
    assert response.json()["code"] == "project_path_not_absolute"


def test_project_routes_reject_missing_project_path(client: TestClient) -> None:
    response = client.get("/api/work")

    assert response.status_code == 400
    assert "project_path" in response.json()["error"]
    assert response.json()["code"] == "project_path_required"


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
    assert response.json()["code"] == "invalid_request"


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
        json={"parent": None, "goal": "   ", "accept": "children"},
    )
    missing = client.post(
        "/api/work/items",
        params=_query(tmp_path),
        json={"parent": "STORY-999", "goal": "Child", "accept": "children"},
    )

    assert invalid.status_code == 400
    assert "goal" in invalid.json()["error"]
    assert invalid.json()["code"] == "blank_goal"
    assert missing.status_code == 404
    assert missing.json() == {
        "error": "unknown work item: STORY-999",
        "code": "unknown_parent",
    }


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
    assert invalid.json()["code"] == "invalid_request"
    assert missing.status_code == 404
    assert missing.json() == {
        "error": "unknown work item: STORY-999",
        "code": "unknown_work_item",
    }


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
    assert invalid.json()["code"] == "root_index_not_supported"
    assert missing_item.status_code == 404
    assert missing_item.json()["code"] == "unknown_work_item"
    assert missing_parent.status_code == 404
    assert missing_parent.json() == {
        "error": "unknown work item: STORY-999",
        "code": "unknown_parent",
    }


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
    assert invalid.json()["code"] == "unknown_predecessor"
    assert missing_add.status_code == 404
    assert missing_add.json()["code"] == "unknown_work_item"
    assert missing_delete.status_code == 404
    assert missing_delete.json()["code"] == "unknown_work_item"


def test_create_rejection_codes_are_stable(client: TestClient, tmp_path: Path) -> None:
    leaf = _create(client, tmp_path, goal="Leaf", gate="true")

    cases = [
        (
            {"parent": None, "goal": "Goal", "realizes": [" "], "accept": "children"},
            "invalid_realizes_slug",
        ),
        (
            {
                "parent": None,
                "goal": "Goal",
                "realizes": ["feature/login", "feature/login"],
                "accept": "children",
            },
            "duplicate_realizes_slug",
        ),
        (
            {"parent": None, "goal": "Goal", "level": "../bad", "accept": "children"},
            "invalid_name",
        ),
        ({"parent": None, "goal": "Goal", "gate": "   ", "accept": "gate"}, "invalid_gate"),
        (
            {"parent": None, "goal": "Goal", "after": [""], "accept": "children"},
            "invalid_order_link",
        ),
        ({"parent": leaf["id"], "goal": "Child", "accept": "children"}, "parent_is_leaf"),
    ]

    for body, code in cases:
        response = client.post("/api/work/items", params=_query(tmp_path), json=body)
        assert response.status_code == 400, response.text
        assert response.json()["code"] == code


def test_malformed_json_and_workspace_format_have_codes(client: TestClient, tmp_path: Path) -> None:
    malformed_body = client.post(
        "/api/work/by-slugs",
        params=_query(tmp_path),
        content="{",
        headers={"content-type": "application/json"},
    )
    ws = _ws(tmp_path)
    ws.items_dir.mkdir(parents=True)
    ws.item_path("BROKEN").write_text("not frontmatter")
    malformed_workspace = client.get("/api/work", params=_query(tmp_path))

    assert malformed_body.status_code == 400
    assert malformed_body.json()["code"] == "invalid_request"
    assert malformed_workspace.status_code == 400
    assert malformed_workspace.json()["code"] == "invalid_format"


def test_order_link_problem_codes_are_stable(client: TestClient, tmp_path: Path) -> None:
    first = _create(client, tmp_path, goal="First")
    second = _create(client, tmp_path, goal="Second", level="epic")
    first_path = f"/api/work/items/{first['id']}/after"
    second_path = f"/api/work/items/{second['id']}/after"
    assert (
        client.post(
            first_path,
            params=_query(tmp_path),
            json={"predecessor": second["id"]},
        ).status_code
        == 200
    )

    cycle = client.post(
        second_path,
        params=_query(tmp_path),
        json={"predecessor": first["id"]},
    )
    parent = _create(client, tmp_path, goal="Parent", level="initiative")
    child = _create(client, tmp_path, parent=parent["id"], goal="Child", gate="true")
    ancestor = client.post(
        f"/api/work/items/{child['id']}/after",
        params=_query(tmp_path),
        json={"predecessor": parent["id"]},
    )
    descendant = client.post(
        f"/api/work/items/{parent['id']}/after",
        params=_query(tmp_path),
        json={"predecessor": child["id"]},
    )

    assert cycle.status_code == 400
    assert cycle.json()["code"] == "order_cycle"
    assert ancestor.status_code == 400
    assert ancestor.json()["code"] == "order_waits_on_ancestor"
    assert descendant.status_code == 400
    assert descendant.json()["code"] == "order_waits_on_descendant"


def test_move_rejection_codes_are_stable(client: TestClient, tmp_path: Path) -> None:
    root = _create(client, tmp_path, goal="Root", level="initiative")
    child = _create(client, tmp_path, parent=root["id"], goal="Child")
    leaf = _create(client, tmp_path, parent=child["id"], goal="Leaf", gate="true")
    sibling = _create(client, tmp_path, parent=root["id"], goal="Sibling", gate="true")
    move_path = f"/api/work/items/{root['id']}/move"

    cases = [
        ({"parent": root["id"], "index": None}, "move_under_self"),
        ({"parent": leaf["id"], "index": None}, "move_under_descendant"),
    ]
    for body, code in cases:
        response = client.post(move_path, params=_query(tmp_path), json=body)
        assert response.status_code == 400
        assert response.json()["code"] == code

    out_of_range = client.post(
        f"/api/work/items/{sibling['id']}/move",
        params=_query(tmp_path),
        json={"parent": root["id"], "index": 99},
    )
    assert out_of_range.status_code == 400
    assert out_of_range.json()["code"] == "index_out_of_range"

    other_parent = _create(client, tmp_path, goal="Other", level="epic")
    ws = _ws(tmp_path)
    ws.write_item(ws.load_item(other_parent["id"]).model_copy(update={"children": [sibling["id"]]}))
    multiple_parents = client.post(
        f"/api/work/items/{sibling['id']}/move",
        params=_query(tmp_path),
        json={"parent": child["id"], "index": None},
    )
    assert multiple_parents.status_code == 400
    assert multiple_parents.json()["code"] == "multiple_parents"


def test_workspace_lock_timeout_has_code(
    client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def time_out(_self: Workspace) -> AbstractContextManager[None]:
        raise WorkspaceLockTimeoutError("timed out acquiring workspace lock")

    monkeypatch.setattr(Workspace, "lock", time_out)

    response = client.post(
        "/api/work/items",
        params=_query(tmp_path),
        json={"parent": None, "goal": "Goal", "accept": "children"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "error": "timed out acquiring workspace lock",
        "code": "workspace_lock_timeout",
    }


def test_uncategorized_value_error_uses_invalid_code(
    client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def reject(*_args: object, **_kwargs: object) -> Any:
        raise ValueError("uncategorized rejection")

    monkeypatch.setattr("solera.http_endpoints.create_item", reject)

    response = client.post(
        "/api/work/items",
        params=_query(tmp_path),
        json={"parent": None, "goal": "Goal", "accept": "children"},
    )

    assert response.status_code == 400
    assert response.json() == {"error": "uncategorized rejection", "code": "invalid"}


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
    assert missing.json() == {"error": "auth token required", "code": "auth_required"}
    assert wrong.status_code == 401
    assert wrong.json() == {"error": "invalid auth token", "code": "invalid_auth_token"}
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
