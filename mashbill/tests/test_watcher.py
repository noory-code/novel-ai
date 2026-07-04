"""Tests for the filesystem watcher → WS-notification layer.

The watcher is the single propagation path that turns an external file edit
(Obsidian / VS Code / the in-app coach's MCP write) into a viewer refresh.
A silent break in its *filter* (`_is_watched_file`) or its *debounce* stops
propagation with no error — exactly the regression class behind
``D-2026-06-28-A``. These tests pin the filter, the event handler, and the
debounce so such a break fails loudly.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from watchdog.events import (
    DirModifiedEvent,
    FileCreatedEvent,
    FileMovedEvent,
)

from mashbill.watcher import WorkspaceWatcher, _Handler, _is_watched_file

# --- _is_watched_file: the propagation filter --------------------------------


def test_is_watched_file_accepts_canonical_json_and_md() -> None:
    for name in ("canvas.json", "detail.json", "project.json", "details.md"):
        assert _is_watched_file(f"/ws/.noory/plot/foundation/{name}") is True


def test_is_watched_file_accepts_per_node_md_under_foundation() -> None:
    # v0.13 Phase 4: every .md directly under a `foundation/` dir propagates,
    # so external edits to a typed-text template reach the viewer.
    assert _is_watched_file("/ws/.noory/plot/foundation/mission-abc.md") is True
    assert _is_watched_file("/ws/.noory/plot/foundation/core_value-x.md") is True


def test_is_watched_file_rejects_md_outside_foundation() -> None:
    # An .md somewhere else must NOT propagate — the parent-dir name is the gate.
    assert _is_watched_file("/ws/.noory/plot/actors/note.md") is False
    assert _is_watched_file("/ws/README.md") is False


def test_is_watched_file_rejects_unrelated_files() -> None:
    for path in (
        "/ws/.noory/plot/foundation/canvas.json.tmp",  # not an exact name
        "/ws/.noory/plot/foundation/state.txt",
        "/ws/.noory/plot/foundation/canvas.JSON",  # case-sensitive on purpose
        "/ws/.git/index",
    ):
        assert _is_watched_file(path) is False


# --- _Handler: directory skip + src/dest filtering ---------------------------


def _collect_handler() -> tuple[_Handler, list[Path]]:
    seen: list[Path] = []
    return _Handler(seen.append), seen


def test_handler_ignores_directory_events() -> None:
    handler, seen = _collect_handler()
    handler.on_any_event(DirModifiedEvent("/ws/.noory/plot/foundation"))
    assert seen == []


def test_handler_notifies_on_watched_file_create() -> None:
    handler, seen = _collect_handler()
    handler.on_any_event(FileCreatedEvent("/ws/.noory/plot/foundation/canvas.json"))
    assert seen == [Path("/ws/.noory/plot/foundation/canvas.json")]


def test_handler_ignores_unwatched_file() -> None:
    handler, seen = _collect_handler()
    handler.on_any_event(FileCreatedEvent("/ws/.noory/plot/foundation/scratch.txt"))
    assert seen == []


def test_handler_follows_move_dest_path() -> None:
    # Atomic save = write tmp then rename → a moved event whose DEST is the real
    # canonical file. The handler must notify on the dest, not just the src.
    handler, seen = _collect_handler()
    handler.on_any_event(
        FileMovedEvent(
            "/ws/.noory/plot/foundation/.canvas.json.tmp",
            "/ws/.noory/plot/foundation/canvas.json",
        )
    )
    assert Path("/ws/.noory/plot/foundation/canvas.json") in seen


# --- WorkspaceWatcher: debounce + safe-call ----------------------------------


async def test_debounce_coalesces_burst_into_one_call() -> None:
    calls: list[set[Path]] = []

    async def on_change(paths: set[Path]) -> None:
        calls.append(set(paths))

    w = WorkspaceWatcher(
        Path("/ws/.noory/plot"),
        on_change,
        asyncio.get_running_loop(),
        debounce_ms=20,
    )
    a = Path("/ws/.noory/plot/foundation/canvas.json")
    b = Path("/ws/.noory/plot/actors/canvas.json")
    w._schedule_fire(a)
    w._schedule_fire(b)
    w._schedule_fire(a)  # duplicate within the window

    await asyncio.sleep(0.06)

    assert len(calls) == 1, "a rapid burst must fire on_change exactly once"
    assert calls[0] == {a, b}, "the one call carries the accumulated path set"


async def test_debounce_separate_windows_fire_separately() -> None:
    calls: list[set[Path]] = []

    async def on_change(paths: set[Path]) -> None:
        calls.append(set(paths))

    w = WorkspaceWatcher(
        Path("/ws/.noory/plot"), on_change, asyncio.get_running_loop(), debounce_ms=20
    )
    p = Path("/ws/.noory/plot/foundation/canvas.json")
    w._schedule_fire(p)
    await asyncio.sleep(0.06)
    w._schedule_fire(p)
    await asyncio.sleep(0.06)

    assert len(calls) == 2


async def test_safe_call_swallows_callback_errors() -> None:
    async def boom(_paths: set[Path]) -> None:
        raise RuntimeError("downstream broadcast failed")

    w = WorkspaceWatcher(Path("/ws/.noory/plot"), boom, asyncio.get_running_loop(), debounce_ms=10)
    # Must not raise — a failing broadcast can't take the watcher down.
    await w._safe_call({Path("/ws/.noory/plot/foundation/canvas.json")})


# --- start / stop lifecycle --------------------------------------------------


def test_start_creates_root_and_observer_then_stop_clears(tmp_path: Path) -> None:
    root = tmp_path / "plot"
    loop = asyncio.new_event_loop()
    try:
        w = WorkspaceWatcher(root, _noop_on_change, loop, debounce_ms=10)
        assert w._observer is None
        w.start()
        assert root.exists(), "start() creates the watched root if missing"
        assert w._observer is not None
        # idempotent: a second start() is a no-op.
        existing = w._observer
        w.start()
        assert w._observer is existing
        w.stop()
        assert w._observer is None
    finally:
        loop.close()


async def _noop_on_change(_paths: set[Path]) -> None:
    return None
