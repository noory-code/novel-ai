"""Solera-root file watcher that notifies the asyncio event loop of changes.

A `WorkspaceWatcher` wraps a `watchdog.Observer` on the Solera root directory
(typically `<project>/.solera/` in v4 or `<project>/workspace/` in the
deprecated v3 fallback) and fires a user-supplied coroutine whenever a tracked
file mutates. Rapid bursts (e.g., atomic saves from editors that
write-then-rename) are collapsed via a debounce window.

Tracked files:
- `*.md`                 (Identity / Persona / Journey / Narrative / Concept /
                          Milestone / Story / ACT)
- `concept-graph.json`   (Concept↔Concept edges)
- `map-layout.json`      (visual metadata)
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer
from watchdog.observers.api import BaseObserver

_log = logging.getLogger(__name__)

_TRACKED_SUFFIXES = (".md",)
_TRACKED_FILENAMES = ("concept-graph.json", "map-layout.json")


def _is_tracked(path: str) -> bool:
    p = Path(path)
    if p.suffix in _TRACKED_SUFFIXES:
        return True
    return p.name in _TRACKED_FILENAMES


class WorkspaceWatcher:
    """Watches the Solera root recursively and invokes `on_change` on edits.

    `on_change` is an async callable with no arguments. It is scheduled on
    the event loop passed to `__init__`, not on watchdog's internal thread.
    """

    def __init__(
        self,
        workspace: Path,
        on_change: Callable[[], Awaitable[None]],
        loop: asyncio.AbstractEventLoop,
        debounce_ms: int = 200,
    ) -> None:
        self._workspace = workspace
        self._on_change = on_change
        self._loop = loop
        self._debounce = debounce_ms / 1000.0
        self._timer: asyncio.TimerHandle | None = None
        self._observer: BaseObserver | None = None

    def start(self) -> None:
        if self._observer is not None:
            return
        handler = _Handler(self._notify)
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

    # --- internal ---------------------------------------------------------

    def _notify(self) -> None:
        """Called from the watchdog thread — schedule onto our loop."""
        self._loop.call_soon_threadsafe(self._schedule_fire)

    def _schedule_fire(self) -> None:
        if self._timer is not None:
            self._timer.cancel()
        self._timer = self._loop.call_later(self._debounce, self._fire)

    def _fire(self) -> None:
        self._timer = None
        asyncio.create_task(self._safe_call())  # noqa: RUF006

    async def _safe_call(self) -> None:
        try:
            await self._on_change()
        except Exception:
            _log.exception("watcher on_change callback failed")


class _Handler(FileSystemEventHandler):
    def __init__(self, notify: Callable[[], None]) -> None:
        self._notify = notify

    def on_any_event(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        src = str(event.src_path)
        dest = getattr(event, "dest_path", "") or ""
        if _is_tracked(src) or (dest and _is_tracked(str(dest))):
            self._notify()
