"""Tests for the WebSocket broadcast hub and the workspace watcher integration.

The `WorkspaceWatcher` itself is not unit-tested here — filesystem events are
timing-sensitive and watchdog already tests them. We verify the hub contract
(subscribe / unsubscribe / notify / shutdown) and that the `/ws` endpoint wires
into that contract. End-to-end watcher behavior is covered by manual checks.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from solera_mcp.server import BroadcastHub, create_http_app


def _seed_workspace(workspace: Path) -> None:
    concepts = workspace / "concepts"
    concepts.mkdir(parents=True, exist_ok=True)
    (concepts / "auth.md").write_text(
        "---\nid: auth\nname: Auth\nstatus: active\n---\n\n# Intent\nseed.\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# BroadcastHub contract
# ---------------------------------------------------------------------------


class _FakeWebSocket:
    """Minimal stand-in — records `send_json` calls."""

    def __init__(self) -> None:
        self.sent: list[dict[str, object]] = []

    async def send_json(self, payload: dict[str, object]) -> None:
        self.sent.append(payload)


@pytest.mark.asyncio
async def test_hub_notify_delivers_to_all_subscribers(tmp_path: Path) -> None:
    hub = BroadcastHub(enable_watchers=False)
    ws1 = _FakeWebSocket()
    ws2 = _FakeWebSocket()

    await hub.subscribe(ws1, tmp_path)  # type: ignore[arg-type]
    await hub.subscribe(ws2, tmp_path)  # type: ignore[arg-type]
    await hub.notify(tmp_path)

    assert ws1.sent == [{"event": "graph_changed"}]
    assert ws2.sent == [{"event": "graph_changed"}]


@pytest.mark.asyncio
async def test_hub_unsubscribe_stops_receiving(tmp_path: Path) -> None:
    hub = BroadcastHub(enable_watchers=False)
    ws = _FakeWebSocket()

    await hub.subscribe(ws, tmp_path)  # type: ignore[arg-type]
    await hub.unsubscribe(ws, tmp_path)  # type: ignore[arg-type]
    await hub.notify(tmp_path)

    assert ws.sent == []
    assert hub.subscription_count(tmp_path) == 0


@pytest.mark.asyncio
async def test_hub_notify_with_no_subscribers_is_noop(tmp_path: Path) -> None:
    hub = BroadcastHub(enable_watchers=False)
    # Must not raise.
    await hub.notify(tmp_path)


@pytest.mark.asyncio
async def test_hub_notify_layout_kind_sends_layout_event(tmp_path: Path) -> None:
    """Layout-only changes emit `layout_changed` so viewers can skip graph re-fetch."""
    hub = BroadcastHub(enable_watchers=False)
    ws = _FakeWebSocket()

    await hub.subscribe(ws, tmp_path)  # type: ignore[arg-type]
    await hub.notify(tmp_path, kind="layout")

    assert ws.sent == [{"event": "layout_changed"}]


@pytest.mark.asyncio
async def test_hub_notify_unknown_kind_falls_back_to_graph(tmp_path: Path) -> None:
    """Unknown kind strings are treated as ``graph`` to avoid silently dropping
    relevant events — better to over-refresh than to miss a change."""
    hub = BroadcastHub(enable_watchers=False)
    ws = _FakeWebSocket()

    await hub.subscribe(ws, tmp_path)  # type: ignore[arg-type]
    await hub.notify(tmp_path, kind="something-else")

    assert ws.sent == [{"event": "graph_changed"}]


@pytest.mark.asyncio
async def test_hub_drops_failing_client_on_broadcast(tmp_path: Path) -> None:
    hub = BroadcastHub(enable_watchers=False)

    class _BrokenWS:
        async def send_json(self, _payload: dict[str, object]) -> None:
            raise RuntimeError("client gone")

    broken = _BrokenWS()
    healthy = _FakeWebSocket()
    await hub.subscribe(broken, tmp_path)  # type: ignore[arg-type]
    await hub.subscribe(healthy, tmp_path)  # type: ignore[arg-type]

    await hub.notify(tmp_path)

    assert healthy.sent == [{"event": "graph_changed"}]
    assert hub.subscription_count(tmp_path) == 1


# ---------------------------------------------------------------------------
# WebSocket route wiring
# ---------------------------------------------------------------------------


def test_ws_requires_project_path() -> None:
    app = create_http_app(hub=BroadcastHub(enable_watchers=False))
    client = TestClient(app)
    with client.websocket_connect("/ws") as ws:
        with pytest.raises(WebSocketDisconnect):
            ws.receive_text()


def test_ws_missing_workspace_closes() -> None:
    app = create_http_app(hub=BroadcastHub(enable_watchers=False))
    client = TestClient(app)
    with client.websocket_connect("/ws?project_path=/definitely/not/here") as ws:
        with pytest.raises(WebSocketDisconnect):
            ws.receive_text()


def test_ws_notify_reaches_connected_client(tmp_path: Path) -> None:
    _seed_workspace(tmp_path / ".solera")
    hub = BroadcastHub(enable_watchers=False)
    app = create_http_app(hub=hub)
    workspace_resolved = (tmp_path / ".solera").resolve()
    client = TestClient(app)

    with client.websocket_connect(f"/ws?project_path={tmp_path}") as ws:
        # Trigger a notify via the test hub.
        import asyncio

        asyncio.run(hub.notify(workspace_resolved))
        message = ws.receive_text()

    payload = json.loads(message)
    assert payload == {"event": "graph_changed"}
