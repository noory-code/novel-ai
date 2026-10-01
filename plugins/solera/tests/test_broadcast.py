"""Watcher lifecycle behind the WebSocket broadcast hub."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from solera.broadcast import BroadcastHub


class _Socket:
    def __init__(self) -> None:
        self.messages: list[dict[str, Any]] = []

    async def send_json(self, body: dict[str, Any]) -> None:
        self.messages.append(body)


class _Watcher:
    def __init__(self) -> None:
        self.stopped = False

    def stop(self) -> None:
        self.stopped = True


def test_hub_starts_one_watcher_on_first_subscriber_and_stops_on_last(tmp_path: Path) -> None:
    async def scenario() -> None:
        hub = BroadcastHub()
        watcher = _Watcher()
        starts: list[Path] = []

        def start(root: Path) -> _Watcher:
            starts.append(root)
            return watcher

        hub._start_watcher = start  # type: ignore[assignment]
        first = _Socket()
        second = _Socket()

        await hub.subscribe(first, tmp_path)  # type: ignore[arg-type]
        await hub.subscribe(second, tmp_path)  # type: ignore[arg-type]
        assert starts == [tmp_path]

        await hub.notify_write(tmp_path)
        assert first.messages == []
        assert second.messages == []

        await hub.notify(tmp_path)
        assert first.messages == [{"event": "work_changed"}]
        assert second.messages == [{"event": "work_changed"}]

        await hub.unsubscribe(first, tmp_path)  # type: ignore[arg-type]
        assert not watcher.stopped
        await hub.unsubscribe(second, tmp_path)  # type: ignore[arg-type]
        assert watcher.stopped

    asyncio.run(scenario())
