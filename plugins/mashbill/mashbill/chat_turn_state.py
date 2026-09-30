"""Process-local tracking for chat turns that are still streaming."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

_TurnKey = tuple[Path, str]
_active_turns: Counter[_TurnKey] = Counter()


def _key(plot_root: Path, scope: str) -> _TurnKey:
    return plot_root.resolve(), scope


def start_turn(plot_root: Path, scope: str) -> None:
    """Mark one more live turn for a workspace scope."""
    _active_turns[_key(plot_root, scope)] += 1


def finish_turn(plot_root: Path, scope: str) -> None:
    """Release one live turn without clearing an overlapping turn."""
    key = _key(plot_root, scope)
    remaining = _active_turns[key] - 1
    if remaining > 0:
        _active_turns[key] = remaining
    else:
        _active_turns.pop(key, None)


def turn_in_progress(plot_root: Path, scope: str) -> bool:
    """Return whether the workspace scope currently has a streaming turn."""
    return _active_turns[_key(plot_root, scope)] > 0
