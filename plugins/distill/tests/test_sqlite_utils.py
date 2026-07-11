"""Shared SQLite initialization behavior."""

from __future__ import annotations

import sqlite3
from typing import Any, cast

import pytest

from distill.store.sqlite_utils import _enable_wal


class _WalConnection:
    def __init__(self, set_errors: list[sqlite3.OperationalError]) -> None:
        self.set_errors = set_errors
        self.set_attempts = 0
        self._last_sql = ""

    def execute(self, sql: str) -> _WalConnection:
        self._last_sql = sql
        if "=" in sql:
            self.set_attempts += 1
            if self.set_errors:
                raise self.set_errors.pop(0)
        return self

    def fetchone(self) -> tuple[str]:
        return ("delete",)


def test_enable_wal_retries_a_transient_first_connection_lock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("distill.store.sqlite_utils._WAL_RETRY_INTERVAL_SECONDS", 0)
    connection = _WalConnection([sqlite3.OperationalError("database is locked")])

    _enable_wal(cast(Any, connection))

    assert connection.set_attempts == 2


def test_enable_wal_does_not_hide_other_operational_errors() -> None:
    connection = _WalConnection([sqlite3.OperationalError("disk I/O error")])

    with pytest.raises(sqlite3.OperationalError, match="disk I/O error"):
        _enable_wal(cast(Any, connection))
