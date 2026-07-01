"""Watcher for `.plot/**/*.json` → WebSocket notifications.

Only one kind of event (``project_changed``) is emitted — position is part
of the canvas JSON itself. Debounced so atomic rename-saves don't
double-fire.
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


def _is_watched_file(path: str) -> bool:
    """v0.9: watch canvas + project metadata.
    v0.13: also watch every ``.md`` file under ``foundation/`` directly,
    since per-node typed-text templates (``{kind}-{slug}.md``) live there.
    External Obsidian / VS Code edits propagate to any open viewer."""
    p = Path(path)
    if p.name in {"canvas.json", "detail.json", "project.json", "details.md"}:
        return True
    # v0.13 Phase 4: per-node MD templates under foundation/ — match any
    # .md file whose parent directory is named "foundation".
    if p.suffix == ".md" and p.parent.name == "foundation":
        return True
    return False


class WorkspaceWatcher:
    """Watches ``{plot_root}/`` recursively.

    ``on_change`` is awaited once per debounce window with the set of
    JSON file paths that changed during that window (useful for the
    broadcast layer to infer which project / canvas to report).
    """

    def __init__(
        self,
        plot_root: Path,
        on_change: Callable[[set[Path]], Awaitable[None]],
        loop: asyncio.AbstractEventLoop,
        debounce_ms: int = 200,
    ) -> None:
        self._plot_root = plot_root
        self._on_change = on_change
        self._loop = loop
        self._debounce = debounce_ms / 1000.0
        self._timer: asyncio.TimerHandle | None = None
        self._observer: BaseObserver | None = None
        self._changed: set[Path] = set()

    def start(self) -> None:
        if self._observer is not None:
            return
        handler = _Handler(self._record)
        observer = Observer()
        target = self._plot_root
        target.mkdir(exist_ok=True)
        observer.schedule(handler, str(target), recursive=True)
        observer.start()
        self._observer = observer
        _log.info("watcher started on %s", target)

    def stop(self) -> None:
        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=2)
            self._observer = None
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None
        self._changed.clear()

    def _record(self, path: Path) -> None:
        self._loop.call_soon_threadsafe(self._schedule_fire, path)

    def _schedule_fire(self, path: Path) -> None:
        self._changed.add(path)
        if self._timer is not None:
            self._timer.cancel()
        self._timer = self._loop.call_later(self._debounce, self._fire)

    def _fire(self) -> None:
        self._timer = None
        if not self._changed:
            return
        paths = self._changed
        self._changed = set()
        asyncio.create_task(self._safe_call(paths))  # noqa: RUF006

    async def _safe_call(self, paths: set[Path]) -> None:
        try:
            await self._on_change(paths)
        except Exception:
            _log.exception("watcher on_change callback failed")


class _Handler(FileSystemEventHandler):
    def __init__(self, notify: Callable[[Path], None]) -> None:
        self._notify = notify

    def on_any_event(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        src = str(event.src_path)
        dest = getattr(event, "dest_path", "") or ""
        for raw in (src, dest):
            if raw and _is_watched_file(raw):
                self._notify(Path(raw))
