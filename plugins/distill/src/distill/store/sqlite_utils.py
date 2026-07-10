"""Shared SQLite connection setup for Distill stores."""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path

BUSY_TIMEOUT_SECONDS = 30.0
_WAL_RETRY_INTERVAL_SECONDS = 0.01


def _is_busy_error(exc: sqlite3.OperationalError) -> bool:
    message = str(exc).lower()
    return "database is locked" in message or "database is busy" in message


def _enable_wal(connection: sqlite3.Connection) -> None:
    """Enable WAL, retrying the first-connection race until the busy deadline."""
    deadline = time.monotonic() + BUSY_TIMEOUT_SECONDS
    while True:
        try:
            row = connection.execute("PRAGMA journal_mode").fetchone()
            if row and str(row[0]).lower() == "wal":
                return
            connection.execute("PRAGMA journal_mode = WAL")
            return
        except sqlite3.OperationalError as exc:
            if not _is_busy_error(exc) or time.monotonic() >= deadline:
                raise
            time.sleep(_WAL_RETRY_INTERVAL_SECONDS)


def connect_wal(db_path: str | Path) -> sqlite3.Connection:
    """Open a cross-thread SQLite connection configured for concurrent stores."""
    connection = sqlite3.connect(
        str(db_path), timeout=BUSY_TIMEOUT_SECONDS, check_same_thread=False
    )
    connection.row_factory = sqlite3.Row
    connection.execute(f"PRAGMA busy_timeout = {int(BUSY_TIMEOUT_SECONDS * 1000)}")
    try:
        _enable_wal(connection)
    except BaseException:
        connection.close()
        raise
    return connection
