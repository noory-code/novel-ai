"""Production watcher path from filesystem writes to WebSocket subscribers."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from threading import Event
from time import monotonic
from typing import Any, cast

import pytest
from anyio import WouldBlock
from starlette.testclient import TestClient, WebSocketTestSession
from watchdog.events import FileCreatedEvent
from watchdog.observers.polling import PollingObserver

from solera import watcher as watcher_module
from solera.broadcast import BroadcastHub
from solera.http_app import create_http_app
from solera.planning import create_item, set_goal
from solera.workspace import Workspace

_MAX_WAIT_SECONDS = 3.0
_POLL_SECONDS = 0.01
_waiter = Event()


@pytest.fixture
def watched_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    # Native FSEvents cannot start inside the macOS test sandbox. PollingObserver
    # is still a real watchdog observer and exercises the same production path.
    monkeypatch.setattr(watcher_module, "Observer", lambda: PollingObserver(timeout=0.02))
    hub = BroadcastHub(debounce_ms=50)
    with TestClient(create_http_app(hub=hub)) as test_client:
        yield test_client


def _query(root: Path) -> dict[str, str]:
    return {"project_path": str(root)}


def _workspace(root: Path) -> Workspace:
    return Workspace(root / ".noory" / "solera")


def _receive_nowait(socket: WebSocketTestSession) -> dict[str, str] | None:
    session = cast(Any, socket)
    try:
        message = session.portal.call(session._send_rx.receive_nowait)
    except WouldBlock:
        return None
    session._raise_on_close(message)
    raw = message.get("text")
    if raw is None:
        raw = message["bytes"].decode("utf-8")
    return cast(dict[str, str], json.loads(raw))


def _receive_by(socket: WebSocketTestSession, deadline: float) -> dict[str, str]:
    while True:
        message = _receive_nowait(socket)
        if message is not None:
            return message
        remaining = deadline - monotonic()
        if remaining <= 0:
            pytest.fail("timed out waiting for WebSocket event")
        _waiter.wait(min(_POLL_SECONDS, remaining))


def _collect_until(socket: WebSocketTestSession, deadline: float) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    while True:
        message = _receive_nowait(socket)
        if message is not None:
            messages.append(message)
            continue
        remaining = deadline - monotonic()
        if remaining <= 0:
            return messages
        _waiter.wait(min(_POLL_SECONDS, remaining))


def test_watcher_ignores_workspace_lock_file(tmp_path: Path) -> None:
    workspace_root = _workspace(tmp_path).root
    notifications: list[None] = []
    handler = watcher_module._Handler(workspace_root, lambda: notifications.append(None))

    handler.on_any_event(FileCreatedEvent(str(workspace_root / ".lock")))

    assert notifications == []


@pytest.mark.parametrize("route", ["create", "patch", "move", "add_after", "delete_after"])
def test_real_watcher_broadcasts_each_http_write_route(
    watched_client: TestClient,
    tmp_path: Path,
    route: str,
) -> None:
    ws = _workspace(tmp_path)
    item = None
    predecessor = None
    new_parent = None
    if route == "patch":
        item = create_item(ws, "story", "Before")
    elif route == "move":
        old_parent = create_item(ws, "story", "Old parent")
        new_parent = create_item(ws, "epic", "New parent")
        item = create_item(ws, "action", "Move me", gate="true", parent=old_parent.id)
    elif route in {"add_after", "delete_after"}:
        predecessor = create_item(ws, "story", "First")
        item = create_item(
            ws,
            "story",
            "Second",
            after=[predecessor.id] if route == "delete_after" else None,
        )

    with watched_client.websocket_connect(f"/ws?project_path={tmp_path}") as socket:
        deadline = monotonic() + _MAX_WAIT_SECONDS
        if route == "create":
            response = watched_client.post(
                "/api/work/items",
                params=_query(tmp_path),
                json={"parent": None, "goal": "Created"},
            )
            assert response.status_code == 201
        elif route == "patch":
            assert item is not None
            response = watched_client.patch(
                f"/api/work/items/{item.id}",
                params=_query(tmp_path),
                json={"goal": "After"},
            )
            assert response.status_code == 200
        elif route == "move":
            assert item is not None and new_parent is not None
            response = watched_client.post(
                f"/api/work/items/{item.id}/move",
                params=_query(tmp_path),
                json={"parent": new_parent.id, "index": 0},
            )
            assert response.status_code == 200
        elif route == "add_after":
            assert item is not None and predecessor is not None
            response = watched_client.post(
                f"/api/work/items/{item.id}/after",
                params=_query(tmp_path),
                json={"predecessor": predecessor.id},
            )
            assert response.status_code == 200
        else:
            assert item is not None and predecessor is not None
            response = watched_client.delete(
                f"/api/work/items/{item.id}/after/{predecessor.id}",
                params=_query(tmp_path),
            )
            assert response.status_code == 200

        assert _receive_by(socket, deadline) == {"event": "work_changed"}


def test_real_watcher_broadcasts_direct_core_write(
    watched_client: TestClient, tmp_path: Path
) -> None:
    ws = _workspace(tmp_path)
    item = create_item(ws, "story", "Before")

    with watched_client.websocket_connect(f"/ws?project_path={tmp_path}") as socket:
        deadline = monotonic() + _MAX_WAIT_SECONDS
        set_goal(ws, item.id, "Written outside HTTP")

        assert _receive_by(socket, deadline) == {"event": "work_changed"}


def test_real_watcher_debounces_a_burst_of_writes(
    watched_client: TestClient, tmp_path: Path
) -> None:
    ws = _workspace(tmp_path)
    item = create_item(ws, "story", "Before")

    with watched_client.websocket_connect(f"/ws?project_path={tmp_path}") as socket:
        final_deadline = monotonic() + _MAX_WAIT_SECONDS
        for index in range(8):
            set_goal(ws, item.id, f"Burst {index}")

        messages = [_receive_by(socket, final_deadline)]
        quiet_deadline = min(final_deadline, monotonic() + 0.3)
        messages.extend(_collect_until(socket, quiet_deadline))

        assert messages == [{"event": "work_changed"}]
