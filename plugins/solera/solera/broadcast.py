"""Per-workspace WebSocket subscriptions and watcher lifecycle."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Protocol

from starlette.websockets import WebSocket


class _Stoppable(Protocol):
    def stop(self) -> None: ...


class BroadcastHub:
    """Fan out work changes, with one watcher from first to last subscriber."""

    def __init__(self, *, enable_watchers: bool = True, debounce_ms: int = 200) -> None:
        self._subs: dict[Path, set[WebSocket]] = {}
        self._watchers: dict[Path, _Stoppable] = {}
        self._lock = asyncio.Lock()
        self._enable_watchers = enable_watchers
        self._debounce_ms = debounce_ms

    async def subscribe(self, socket: WebSocket, workspace_root: Path) -> None:
        async with self._lock:
            if workspace_root not in self._subs:
                self._subs[workspace_root] = set()
                if self._enable_watchers:
                    self._watchers[workspace_root] = self._start_watcher(workspace_root)
            self._subs[workspace_root].add(socket)

    async def unsubscribe(self, socket: WebSocket, workspace_root: Path) -> None:
        async with self._lock:
            subscribers = self._subs.get(workspace_root)
            if subscribers is None:
                return
            subscribers.discard(socket)
            if subscribers:
                return
            self._subs.pop(workspace_root, None)
            watcher = self._watchers.pop(workspace_root, None)
            if watcher is not None:
                watcher.stop()

    async def notify(self, workspace_root: Path) -> None:
        """Send one canonical work-change event to current subscribers."""
        async with self._lock:
            targets = list(self._subs.get(workspace_root, ()))
        dead: list[WebSocket] = []
        for socket in targets:
            try:
                await socket.send_json({"event": "work_changed"})
            except Exception:
                dead.append(socket)
        if dead:
            async with self._lock:
                subscribers = self._subs.get(workspace_root)
                if subscribers is not None:
                    for socket in dead:
                        subscribers.discard(socket)

    async def notify_write(self, workspace_root: Path) -> None:
        """Notify injected hubs; production writes are reported by the watcher.

        This keeps HTTP+watchdog from emitting the same change twice while
        allowing deterministic endpoint tests to disable OS watchers.
        """
        if not self._enable_watchers:
            await self.notify(workspace_root)

    def _start_watcher(self, workspace_root: Path) -> _Stoppable:
        from .watcher import WorkspaceWatcher

        loop = asyncio.get_running_loop()

        async def on_change() -> None:
            await self.notify(workspace_root)

        watcher = WorkspaceWatcher(
            workspace_root,
            on_change=on_change,
            loop=loop,
            debounce_ms=self._debounce_ms,
        )
        watcher.start()
        return watcher

    async def shutdown(self) -> None:
        async with self._lock:
            for watcher in self._watchers.values():
                watcher.stop()
            self._watchers.clear()
            self._subs.clear()
