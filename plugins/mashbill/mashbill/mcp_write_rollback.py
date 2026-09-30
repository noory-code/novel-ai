"""Rollback support for MCP writes that must be paired with a draft."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

_WriteResult = TypeVar("_WriteResult")
_DraftResult = TypeVar("_DraftResult")


def with_draft_or_rollback(
    write: Callable[[], _WriteResult],
    record_draft: Callable[[_WriteResult], _DraftResult],
    rollback: Callable[[], object],
) -> tuple[_WriteResult, _DraftResult]:
    """Run a write and restore its prior state if writing or draft persistence fails."""
    try:
        written = write()
    except Exception as write_error:
        try:
            rollback()
        except Exception as rollback_error:
            write_error.add_note(f"rollback after write failure failed: {rollback_error!r}")
        raise
    try:
        draft_result = record_draft(written)
    except Exception as draft_error:
        try:
            rollback()
        except Exception as rollback_error:
            draft_error.add_note(
                f"rollback after draft persistence failure failed: {rollback_error!r}"
            )
        raise
    return written, draft_result
