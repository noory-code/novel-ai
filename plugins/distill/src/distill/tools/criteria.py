"""Shared criteria operations used by MCP and the command-line interface."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from distill.store.criteria import CriteriaError, CriteriaStore

JsonObject = dict[str, Any]


def _call(operation: Callable[[], JsonObject]) -> JsonObject:
    try:
        return operation()
    except CriteriaError as error:
        return error.as_dict()


def criteria_record(
    payload: JsonObject, idempotency_key: str, *, db_path: str | Path | None = None
) -> JsonObject:
    """Record a project criterion with immutable source evidence."""
    store = CriteriaStore(db_path)
    return _call(lambda: store.record(payload, idempotency_key=idempotency_key))


def criteria_revise(
    criterion_id: str,
    payload: JsonObject,
    idempotency_key: str,
    *,
    db_path: str | Path | None = None,
) -> JsonObject:
    """Create a new criterion version using an expected base version."""
    store = CriteriaStore(db_path)
    return _call(lambda: store.revise(criterion_id, payload, idempotency_key=idempotency_key))


def criteria_revoke(
    criterion_id: str,
    payload: JsonObject,
    idempotency_key: str,
    *,
    db_path: str | Path | None = None,
) -> JsonObject:
    """Revoke a criterion while retaining its versions and events."""
    store = CriteriaStore(db_path)
    return _call(lambda: store.revoke(criterion_id, payload, idempotency_key=idempotency_key))


def criteria_current(project: str, *, db_path: str | Path | None = None) -> JsonObject:
    """Return confirmed current criteria for one project key."""
    store = CriteriaStore(db_path)
    return _call(lambda: store.current(project))


def criteria_check(
    project: str, refs: list[str], *, db_path: str | Path | None = None
) -> JsonObject:
    """Check immutable references immediately before a criterion-dependent choice."""
    store = CriteriaStore(db_path)
    return _call(lambda: store.check(project, refs))


def criteria_history(criterion_id: str, *, db_path: str | Path | None = None) -> JsonObject:
    """Return every version, source, reason, and generation-stamped event."""
    store = CriteriaStore(db_path)
    return _call(lambda: store.history(criterion_id))
