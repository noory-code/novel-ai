"""Debounced filesystem watcher for one ``.noory/solera`` workspace."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer
from watchdog.observers.api import BaseObserver

_log = logging.getLogger(__name__)


class WorkspaceWatcher:
    """Watch all files under a workspace and debounce atomic-save event bursts."""

    def __init__(
        self,
        workspace_root: Path,
        on_change: Callable[[], Awaitable[None]],
        loop: asyncio.AbstractEventLoop,
        debounce_ms: int = 200,
    ) -> None:
        self._workspace_root = workspace_root
        self._on_change = on_change
        self._loop = loop
        self._debounce = debounce_ms / 1000.0
        self._timer: asyncio.TimerHandle | None = None
        self._observer: BaseObserver | None = None

    def start(self) -> None:
        if self._observer is not None:
            return
        project_root = self._workspace_root.parent.parent
        if not project_root.is_dir():
            _log.warning("cannot watch missing project directory %s", project_root)
            return
        observer = Observer()
        observer.schedule(
            _Handler(self._workspace_root, self._record),
            str(project_root),
            recursive=True,
        )
        observer.start()
        self._observer = observer
        _log.info("watcher started for %s", self._workspace_root)

    def stop(self) -> None:
        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=2)
            self._observer = None
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None

    def _record(self) -> None:
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
            _log.exception("watcher callback failed")


class _Handler(FileSystemEventHandler):
    def __init__(self, workspace_root: Path, notify: Callable[[], None]) -> None:
        self._workspace_root = workspace_root
        self._notify = notify

    def on_any_event(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        for raw_path in (str(event.src_path), str(getattr(event, "dest_path", "") or "")):
            if not raw_path:
                continue
            try:
                relative = Path(raw_path).relative_to(self._workspace_root)
            except ValueError:
                continue
            if relative == Path(".lock"):
                continue
            self._notify()
            return
