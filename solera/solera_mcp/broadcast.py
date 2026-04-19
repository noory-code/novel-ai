"""WebSocket fan-out between workspace watchers and browser clients.

Isolated from the HTTP app so tests can exercise the hub directly without
standing up Starlette, and so the HTTP composition root stays small.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from starlette.websockets import WebSocket

from solera_mcp.watcher import WorkspaceWatcher


class BroadcastHub:
    """Fan-out between workspace watchers and connected WebSocket clients.

    One watcher per workspace, created on the first subscription and torn
    down when the last client for that workspace disconnects. Broadcasts
    are idempotent — ``notify(workspace)`` can be called directly (by tests
    or future MCP triggers) without a real filesystem event.

    Tests that don't want a real filesystem watcher may pass
    ``enable_watchers=False``; subscriptions still work and ``notify``
    remains the event source.
    """

    def __init__(self, *, enable_watchers: bool = True) -> None:
        self._subs: dict[Path, set[WebSocket]] = {}
        self._watchers: dict[Path, WorkspaceWatcher] = {}
        self._lock = asyncio.Lock()
        self._enable_watchers = enable_watchers

    async def subscribe(self, ws: WebSocket, workspace: Path) -> None:
        async with self._lock:
            if workspace not in self._subs:
                self._subs[workspace] = set()
                if self._enable_watchers:
                    self._watchers[workspace] = self._start_watcher(workspace)
            self._subs[workspace].add(ws)

    async def unsubscribe(self, ws: WebSocket, workspace: Path) -> None:
        async with self._lock:
            subs = self._subs.get(workspace)
            if subs is None:
                return
            subs.discard(ws)
            if not subs:
                self._subs.pop(workspace, None)
                watcher = self._watchers.pop(workspace, None)
                if watcher is not None:
                    watcher.stop()

    async def notify(self, workspace: Path, kind: str = "graph") -> None:
        """Broadcast a change event to all subscribers of workspace.

        ``kind`` is ``"graph"`` for content changes (any ``.md`` or
        ``concept-graph.json``) and ``"layout"`` for pure canvas-position
        saves (``map-layout.json``). Viewers interpret ``layout_changed`` as a
        cheap refresh that can skip graph re-fetch, preserving selection and
        panel state when the user drags a node.
        """
        event = "layout_changed" if kind == "layout" else "graph_changed"
        async with self._lock:
            targets = list(self._subs.get(workspace, ()))
        dead: list[WebSocket] = []
        for ws in targets:
            try:
                await ws.send_json({"event": event})
            except Exception:
                dead.append(ws)
        if dead:
            async with self._lock:
                subs = self._subs.get(workspace)
                if subs is not None:
                    for ws in dead:
                        subs.discard(ws)

    def subscription_count(self, workspace: Path) -> int:
        return len(self._subs.get(workspace, ()))

    def _start_watcher(self, workspace: Path) -> WorkspaceWatcher:
        loop = asyncio.get_running_loop()

        async def on_change(kind: str) -> None:
            await self.notify(workspace, kind=kind)

        watcher = WorkspaceWatcher(workspace, on_change=on_change, loop=loop)
        watcher.start()
        return watcher

    async def shutdown(self) -> None:
        async with self._lock:
            for watcher in self._watchers.values():
                watcher.stop()
            self._watchers.clear()
            self._subs.clear()
