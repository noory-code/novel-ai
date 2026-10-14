"""BroadcastHub subscribe ↔ watcher lifecycle.

The coach writes canvases from a separate MCP process, so the filesystem
watcher's ``project_changed`` broadcast is the only way those writes reach an
open viewer. A viewer can open its socket before the project folder exists
(the new-project screen); the room must still end up watched once the folder
appears, and a failed watcher start must not leave a room that is never
watched. Subscribing is a read, so it must not create the data folder
(D-2026-07-17-B).
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, cast

import pytest
from starlette.websockets import WebSocket

from mashbill.broadcast import BroadcastHub
from mashbill.project_io import create_project
from mashbill.workspace import resolve_plot_root


class _RecordingSocket:
    def __init__(self) -> None:
        self.sent: list[dict[str, Any]] = []

    async def send_json(self, body: dict[str, Any]) -> None:
        self.sent.append(body)


def _ws(sock: _RecordingSocket) -> WebSocket:
    return cast(WebSocket, sock)


async def _wait_for_canvas_event(sock: _RecordingSocket, kind: str, timeout: float = 8.0) -> None:
    deadline = asyncio.get_running_loop().time() + timeout
    while asyncio.get_running_loop().time() < deadline:
        if any(
            m.get("event") == "project_changed" and m.get("canvas_kind") == kind for m in sock.sent
        ):
            return
        await asyncio.sleep(0.05)
    raise AssertionError(f"no project_changed for {kind!r} within {timeout}s; got {sock.sent!r}")


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    # FSEvents reports real paths (/private/var/...), so the watched root must
    # be resolved the same way ``resolve_plot_root`` does in production.
    base = tmp_path.resolve() / "walk"
    base.mkdir()
    return base


async def test_socket_opened_before_project_exists_receives_later_coach_writes(
    workspace: Path,
) -> None:
    plot_root = resolve_plot_root(str(workspace), create=False)
    hub = BroadcastHub()
    sock = _RecordingSocket()
    try:
        await hub.subscribe(_ws(sock), plot_root)
        assert not (workspace / ".noory").exists(), "subscribing must not create the data folder"

        create_project(plot_root, "p1", "P1")
        await _wait_for_canvas_event(sock, "foundation")

        # A later write from another process (the coach) still propagates:
        # the room is watched recursively, not just seeded once.
        sock.sent.clear()
        canvas = plot_root / "foundation" / "canvas.json"
        canvas.write_text(canvas.read_text())
        await _wait_for_canvas_event(sock, "foundation")
    finally:
        await hub.shutdown()


async def test_subscribe_does_not_create_novel_under_an_existing_noory(workspace: Path) -> None:
    (workspace / ".noory").mkdir()
    plot_root = resolve_plot_root(str(workspace), create=False)
    hub = BroadcastHub()
    try:
        await hub.subscribe(_ws(_RecordingSocket()), plot_root)
        assert not plot_root.exists()
    finally:
        await hub.shutdown()


class _StubWatcher:
    def __init__(self) -> None:
        self.stopped = False

    def stop(self) -> None:
        self.stopped = True


async def test_failed_watcher_start_is_retried_on_next_subscribe(
    workspace: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plot_root = workspace / ".noory" / "novel"
    hub = BroadcastHub()
    stub = _StubWatcher()
    attempts: list[Path] = []

    def flaky_start(root: Path) -> _StubWatcher:
        attempts.append(root)
        if len(attempts) == 1:
            raise OSError("inotify watch limit reached")
        return stub

    monkeypatch.setattr(hub, "_start_watcher", flaky_start)

    first = _RecordingSocket()
    await hub.subscribe(_ws(first), plot_root)
    assert hub.subscription_count(plot_root) == 1, "the socket still joins the room"
    assert plot_root not in hub._watchers

    await hub.subscribe(_ws(_RecordingSocket()), plot_root)
    assert cast(object, hub._watchers.get(plot_root)) is stub, (
        "the next subscribe starts the missing watcher"
    )
    assert len(attempts) == 2

    await hub.shutdown()
    assert stub.stopped
