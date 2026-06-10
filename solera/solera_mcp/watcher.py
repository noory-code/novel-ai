"""Solera-root file watcher that notifies the asyncio event loop of changes.

A `WorkspaceWatcher` wraps a `watchdog.Observer` on the Solera root directory
(typically `<project>/.noory/solera/` under R9, with auto-migration from a
legacy `<project>/.solera/` or the deprecated v3 `<project>/workspace/`
fallback) and fires a user-supplied coroutine whenever a tracked
file mutates. Rapid bursts (e.g., atomic saves from editors that
write-then-rename) are collapsed via a debounce window.

Tracked files:
- `*.md`                 (Identity / Persona / Journey / Narrative / Concept /
                          Milestone / Story / ACT)                  → ``graph``
- `concept-graph.json`   (Concept↔Concept edges)                    → ``graph``
- `map-layout.json`      (visual metadata — pure canvas positioning) → ``layout``

The callback receives the *highest-impact* kind seen during the debounce
window (``graph`` > ``layout``) so the server can decide whether a full graph
re-fetch is needed or a cheap layout-only refresh suffices.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Literal

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer
from watchdog.observers.api import BaseObserver

_log = logging.getLogger(__name__)

ChangeKind = Literal["graph", "layout"]

_LAYOUT_FILENAMES = ("map-layout.json",)
_GRAPH_FILENAMES = ("concept-graph.json",)
_GRAPH_SUFFIXES = (".md",)


def _classify(path: str) -> ChangeKind | None:
    p = Path(path)
    if p.name in _LAYOUT_FILENAMES:
        return "layout"
    if p.suffix in _GRAPH_SUFFIXES:
        return "graph"
    if p.name in _GRAPH_FILENAMES:
        return "graph"
    return None


class WorkspaceWatcher:
    """Watches the Solera root recursively and invokes `on_change` on edits.

    ``on_change`` is an async callable taking the :data:`ChangeKind` seen
    during the debounce window. It is scheduled on the event loop passed to
    ``__init__``, not on watchdog's internal thread.
    """

    def __init__(
        self,
        workspace: Path,
        on_change: Callable[[ChangeKind], Awaitable[None]],
        loop: asyncio.AbstractEventLoop,
        debounce_ms: int = 200,
    ) -> None:
        self._workspace = workspace
        self._on_change = on_change
        self._loop = loop
        self._debounce = debounce_ms / 1000.0
        self._timer: asyncio.TimerHandle | None = None
        self._observer: BaseObserver | None = None
        self._pending: set[ChangeKind] = set()

    def start(self) -> None:
        if self._observer is not None:
            return
        handler = _Handler(self._record)
        observer = Observer()
        observer.schedule(handler, str(self._workspace), recursive=True)
        observer.start()
        self._observer = observer
        _log.info("watcher started on %s", self._workspace)

    def stop(self) -> None:
        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=2)
            self._observer = None
            _log.info("watcher stopped on %s", self._workspace)
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None
        self._pending.clear()

    # --- internal ---------------------------------------------------------

    def _record(self, kind: ChangeKind) -> None:
        """Called from the watchdog thread — record kind and schedule flush."""
        self._loop.call_soon_threadsafe(self._schedule_fire, kind)

    def _schedule_fire(self, kind: ChangeKind) -> None:
        self._pending.add(kind)
        if self._timer is not None:
            self._timer.cancel()
        self._timer = self._loop.call_later(self._debounce, self._fire)

    def _fire(self) -> None:
        self._timer = None
        # ``graph`` always wins: any .md/concept-graph.json change forces a
        # full re-fetch even if a layout change happened in the same window.
        kind: ChangeKind = "graph" if "graph" in self._pending else "layout"
        self._pending.clear()
        asyncio.create_task(self._safe_call(kind))  # noqa: RUF006

    async def _safe_call(self, kind: ChangeKind) -> None:
        try:
            await self._on_change(kind)
        except Exception:
            _log.exception("watcher on_change callback failed")


class _Handler(FileSystemEventHandler):
    def __init__(self, notify: Callable[[ChangeKind], None]) -> None:
        self._notify = notify

    def on_any_event(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        src = str(event.src_path)
        dest = getattr(event, "dest_path", "") or ""
        kind = _classify(src) or (_classify(str(dest)) if dest else None)
        if kind is not None:
            self._notify(kind)
