"""Process-local tracking for chat turns that are still streaming."""

from __future__ import annotations

from pathlib import Path

_active_turns: set[Path] = set()


def _key(plot_root: Path, scope: str) -> Path:
    return plot_root.resolve()


def try_start_turn(plot_root: Path, scope: str) -> bool:
    """Reserve the project before any send mutation or scheduling."""
    key = _key(plot_root, scope)
    if key in _active_turns:
        return False
    _active_turns.add(key)
    return True


def start_turn(plot_root: Path, scope: str) -> None:
    """Mark a directly invoked stream turn as active."""
    _active_turns.add(_key(plot_root, scope))


def finish_turn(plot_root: Path, scope: str) -> None:
    """Release the project's live turn."""
    _active_turns.discard(_key(plot_root, scope))


def turn_in_progress(plot_root: Path, scope: str) -> bool:
    """Return whether the project has any streaming turn."""
    return _key(plot_root, scope) in _active_turns
