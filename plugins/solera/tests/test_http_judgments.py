from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import pytest
from starlette.testclient import TestClient

from solera.broadcast import BroadcastHub
from solera.formats import Progress
from solera.http_app import create_http_app
from solera.workspace import Workspace


@pytest.fixture
def client() -> Iterator[TestClient]:
    hub = BroadcastHub(enable_watchers=False)
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
    accept: str,
    parent: str | None = None,
    gate: str = "",
) -> dict[str, Any]:
    response = client.post(
        "/api/work/items",
        params=_query(root),
        json={
            "parent": parent,
            "goal": "Goal",
            "accept": accept,
            "gate": gate,
        },
    )
    assert response.status_code == 201, response.text
    return cast(dict[str, Any], response.json())


def _judge(
    client: TestClient,
    root: Path,
    item_id: str,
    action: str,
    reason: str | None = None,
) -> Any:
    return client.post(
        f"/api/work/items/{item_id}/{action}",
        params=_query(root),
        json={} if reason is None else {"reason": reason},
    )


def test_create_requires_accept_without_a_gate_and_defaults_gated_items(
    client: TestClient, tmp_path: Path
) -> None:
    missing = client.post(
        "/api/work/items",
        params=_query(tmp_path),
        json={"parent": None, "goal": "Ambiguous"},
    )
    gated = client.post(
        "/api/work/items",
        params=_query(tmp_path),
        json={"parent": None, "goal": "Automated", "gate": "true"},
    )

    assert missing.status_code == 400
    assert missing.json()["code"] == "accept_required"
    assert gated.status_code == 201
    assert gated.json()["accept"] == "gate"


def test_person_judgment_lifecycle_records_append_only_utc_entries(
    client: TestClient, tmp_path: Path
) -> None:
    item = _create(client, tmp_path, accept="person")
    ws = _ws(tmp_path)
    ws.write_item(ws.load_item(item["id"]).model_copy(update={"status": "review"}))

    rejected = _judge(client, tmp_path, item["id"], "reject", "Needs another pass")
    ws.write_item(ws.load_item(item["id"]).model_copy(update={"status": "review"}))
    accepted = _judge(client, tmp_path, item["id"], "accept")
    reopened = _judge(client, tmp_path, item["id"], "reopen", "Never met the condition")
    cancelled = _judge(client, tmp_path, item["id"], "cancel", "Superseded")

    assert rejected.status_code == 200
    assert accepted.status_code == 200
    assert reopened.status_code == 200
    assert cancelled.status_code == 200
    final = cancelled.json()["item"]
    assert final["status"] == "cancelled"
    assert [entry["action"] for entry in final["judgments"]] == [
        "reject",
        "accept",
        "reopen",
        "cancel",
    ]
    assert [entry["reason"] for entry in final["judgments"]] == [
        "Needs another pass",
        "",
        "Never met the condition",
        "Superseded",
    ]
    for entry in final["judgments"]:
        assert datetime.fromisoformat(entry["at"].replace("Z", "+00:00")).tzinfo is not None


@pytest.mark.parametrize(
    ("action", "status", "accept", "reason", "code"),
    [
        ("accept", "todo", "person", None, "not_in_review"),
        ("reject", "review", "gate", "No", "not_person"),
        ("reject", "review", "person", " ", "blank_reason"),
        ("reopen", "done", "gate", "No", "reopen_not_person"),
        ("reopen", "review", "person", "No", "reopen_not_done"),
        ("cancel", "done", "person", "No", "cancel_finished"),
        ("cancel", "todo", "person", " ", "blank_reason"),
    ],
)
def test_judgment_error_codes(
    client: TestClient,
    tmp_path: Path,
    action: str,
    status: str,
    accept: str,
    reason: str | None,
    code: str,
) -> None:
    gate = "true" if accept == "gate" else ""
    item = _create(client, tmp_path, accept=accept, gate=gate)
    ws = _ws(tmp_path)
    ws.write_item(ws.load_item(item["id"]).model_copy(update={"status": status}))

    response = _judge(client, tmp_path, item["id"], action, reason)

    assert response.status_code == 400
    assert response.json()["code"] == code


def test_cancel_clears_a_pointer_to_a_descendant(client: TestClient, tmp_path: Path) -> None:
    parent = _create(client, tmp_path, accept="person")
    child = _create(client, tmp_path, accept="gate", parent=parent["id"], gate="true")
    ws = _ws(tmp_path)
    ws.write_item(ws.load_item(child["id"]).model_copy(update={"status": "doing"}))
    ws.write_progress(Progress(item=child["id"]))

    response = _judge(client, tmp_path, parent["id"], "cancel", "Stop the branch")

    assert response.status_code == 200
    assert ws.load_progress().item is None
    frozen_check = client.post(f"/api/work/items/{child['id']}/check", params=_query(tmp_path))
    assert frozen_check.json()["code"] == "check_cancelled"


def test_patch_accept_phase_and_protected_edit_rules(client: TestClient, tmp_path: Path) -> None:
    item = _create(client, tmp_path, accept="children")
    box = _create(client, tmp_path, accept="children")
    patched = client.patch(
        f"/api/work/items/{item['id']}",
        params=_query(tmp_path),
        json={"accept": "person", "phase": "exploring", "phase_note": "Unknown API"},
    )
    assert patched.status_code == 200
    assert patched.json()["accept"] == "person"
    assert patched.json()["phase"] == "exploring"

    ws = _ws(tmp_path)
    ws.write_item(ws.load_item(item["id"]).model_copy(update={"status": "review"}))
    protected = client.patch(
        f"/api/work/items/{item['id']}",
        params=_query(tmp_path),
        json={"goal": "Changed"},
    )
    rejected = _judge(client, tmp_path, item["id"], "reject", "Change it")
    editable = client.patch(
        f"/api/work/items/{item['id']}",
        params=_query(tmp_path),
        json={"goal": "Changed"},
    )
    movable = client.post(
        f"/api/work/items/{item['id']}/move",
        params=_query(tmp_path),
        json={"parent": box["id"], "index": None},
    )

    assert protected.json()["code"] == "item_protected"
    assert rejected.status_code == 200
    assert editable.status_code == 200
    assert editable.json()["goal"] == "Changed"
    assert movable.status_code == 200


def test_check_and_uncheck_append_judgments(client: TestClient, tmp_path: Path) -> None:
    item = _create(client, tmp_path, accept="person")

    checked = client.post(f"/api/work/items/{item['id']}/check", params=_query(tmp_path))
    unchecked = client.delete(f"/api/work/items/{item['id']}/check", params=_query(tmp_path))

    assert checked.status_code == 200
    assert unchecked.status_code == 200
    assert [entry["action"] for entry in unchecked.json()["item"]["judgments"]] == [
        "check",
        "uncheck",
    ]


def test_check_already_done_is_unchanged(client: TestClient, tmp_path: Path) -> None:
    item = _create(client, tmp_path, accept="person")
    ws = _ws(tmp_path)
    ws.write_item(ws.load_item(item["id"]).model_copy(update={"status": "done"}))

    response = client.post(f"/api/work/items/{item['id']}/check", params=_query(tmp_path))

    assert response.status_code == 200
    assert response.json()["item"] == item | {"status": "done"}


def test_uncheck_already_todo_is_unchanged(client: TestClient, tmp_path: Path) -> None:
    item = _create(client, tmp_path, accept="person")

    response = client.delete(f"/api/work/items/{item['id']}/check", params=_query(tmp_path))

    assert response.status_code == 200
    assert response.json()["item"] == item


def test_accept_change_is_locked_after_review(client: TestClient, tmp_path: Path) -> None:
    item = _create(client, tmp_path, accept="person")
    ws = _ws(tmp_path)
    ws.write_item(ws.load_item(item["id"]).model_copy(update={"status": "review"}))

    response = client.patch(
        f"/api/work/items/{item['id']}",
        params=_query(tmp_path),
        json={"accept": "children"},
    )

    assert response.status_code == 400
    assert response.json()["code"] == "accept_locked"


def test_invalid_accept_and_phase_have_specific_codes(client: TestClient, tmp_path: Path) -> None:
    invalid_create = client.post(
        "/api/work/items",
        params=_query(tmp_path),
        json={"parent": None, "goal": "Bad", "accept": "gate"},
    )
    item = _create(client, tmp_path, accept="children")
    invalid_accept = client.patch(
        f"/api/work/items/{item['id']}",
        params=_query(tmp_path),
        json={"accept": "gate"},
    )
    invalid_phase = client.patch(
        f"/api/work/items/{item['id']}",
        params=_query(tmp_path),
        json={"phase": "guessing"},
    )

    assert invalid_create.json()["code"] == "invalid_accept"
    assert invalid_accept.json()["code"] == "invalid_accept"
    assert invalid_phase.json()["code"] == "invalid_phase"


def test_check_refuses_cancelled_and_children_accepted_items(
    client: TestClient, tmp_path: Path
) -> None:
    cancelled = _create(client, tmp_path, accept="person")
    children = _create(client, tmp_path, accept="children")
    _judge(client, tmp_path, cancelled["id"], "cancel", "Stop")

    cancelled_check = client.post(
        f"/api/work/items/{cancelled['id']}/check", params=_query(tmp_path)
    )
    children_check = client.post(f"/api/work/items/{children['id']}/check", params=_query(tmp_path))

    assert cancelled_check.json()["code"] == "check_cancelled"
    assert children_check.json()["code"] == "check_container"
