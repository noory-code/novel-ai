"""File-lock based concurrency control for Distill hooks.

Prevents multiple hook instances from running simultaneously,
avoiding process stacking when PreCompact and SessionEnd fire in rapid succession.
"""

from __future__ import annotations

import fcntl
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import IO

LOCK_PATH = Path.home() / ".distill" / "hook.lock"
STATUS_PATH = Path.home() / ".distill" / "hook-status.json"


def acquire_hook_lock() -> IO[str] | None:
    """Acquire an exclusive file lock for hook execution.

    Returns:
        File handle if lock acquired (caller must keep reference alive),
        None if another hook instance is already running.
    """
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    fh = open(LOCK_PATH, "w")  # noqa: SIM115
    try:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fh
    except (BlockingIOError, OSError):
        fh.close()
        return None


def write_status_started(session_id: str, event: str) -> None:
    """Write hook-status.json when a hook starts running."""
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    status = {
        "pid": os.getpid(),
        "started_at": datetime.now(UTC).isoformat(),
        "session_id": session_id,
        "event": event,
    }
    STATUS_PATH.write_text(json.dumps(status, indent=2), encoding="utf-8")


def write_status_finished(
    session_id: str,
    event: str,
    result: str,
    duration_s: float,
    error: str | None = None,
) -> None:
    """Update hook-status.json when a hook finishes."""
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    status = {
        "last_run": datetime.now(UTC).isoformat(),
        "session_id": session_id,
        "event": event,
        "result": result,
        "duration_s": round(duration_s, 2),
    }
    if error:
        status["error"] = error
    STATUS_PATH.write_text(json.dumps(status, indent=2), encoding="utf-8")
