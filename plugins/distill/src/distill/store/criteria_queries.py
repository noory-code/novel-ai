"""Read-only criteria queries separated from lifecycle writes."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING, Any

from distill import __version__
from distill.store.criteria_models import utc_now

if TYPE_CHECKING:
    from distill.store.criteria import CriteriaStore

JsonObject = dict[str, Any]


def _ref(criterion_id: str, version: int) -> str:
    return f"distill:{criterion_id}@{version}"


def _json_load(value: str) -> Any:
    import json

    return json.loads(value)


def _row_to_version(row: sqlite3.Row) -> JsonObject:
    return {
        "ref": _ref(row["criterion_id"], int(row["version"])),
        "statement": row["statement"],
        "applies_when": _json_load(row["applies_when"]),
        "exceptions": _json_load(row["exceptions"]),
        "notes": _json_load(row["notes"]),
        "overrides": _json_load(row["overrides"]),
        "confirmation": row["confirmation"],
        "ai_confidence": row["ai_confidence"],
        "origin": _json_load(row["origin"]),
        "reason": row["reason"],
        "supersedes": row["supersedes"],
        "recorded_at": row["recorded_at"],
    }


def current_criteria(store: CriteriaStore, project: str) -> JsonObject:
    """Return only confirmed current versions for one explicit project key."""
    from distill.store.criteria import CriteriaError

    project = project.strip()
    if not project:
        raise CriteriaError("E_SCOPE_REQUIRED", "project is required")
    connection = store._connect(create=False)
    checked_at = utc_now()
    if connection is None:
        return {
            "schema": "criteria-snapshot/1",
            "producer": "distill",
            "producer_version": __version__,
            "generation": 0,
            "checked_at": checked_at,
            "scope": {"kind": "project", "key": project},
            "criteria": [],
            "retired": [],
            "store": "absent",
        }
    try:
        rows = connection.execute(
            "SELECT v.* FROM criteria c JOIN criterion_versions v "
            "ON v.criterion_id = c.id AND v.version = c.current_version "
            "WHERE c.project = ? AND c.revoked = 0 "
            "AND v.confirmation IN ('user_stated', 'user_confirmed') "
            "ORDER BY v.recorded_at, v.criterion_id",
            (project,),
        ).fetchall()
        retired_rows = connection.execute(
            "SELECT v.*, c.current_version, c.revoked FROM criteria c "
            "JOIN criterion_versions v ON v.criterion_id = c.id "
            "WHERE c.project = ? AND v.status IN ('superseded', 'revoked') "
            "ORDER BY v.recorded_at, v.criterion_id, v.version",
            (project,),
        ).fetchall()
        retired: list[JsonObject] = []
        for row in retired_rows:
            item: JsonObject = {"ref": _ref(row["criterion_id"], int(row["version"]))}
            item["status"] = row["status"]
            if row["status"] == "superseded" and not row["revoked"]:
                item["by"] = _ref(row["criterion_id"], int(row["current_version"]))
            retired.append(item)
        return {
            "schema": "criteria-snapshot/1",
            "producer": "distill",
            "producer_version": __version__,
            "generation": store._generation(connection),
            "checked_at": checked_at,
            "scope": {"kind": "project", "key": project},
            "criteria": [_row_to_version(row) for row in rows],
            "retired": retired,
        }
    except sqlite3.Error as error:
        raise CriteriaError(
            "E_STORE_UNAVAILABLE", f"Cannot read criteria store: {error}", store_error=True
        ) from error
    finally:
        connection.close()


def check_criteria(store: CriteriaStore, project: str, refs: list[str]) -> JsonObject:
    """Resolve supplied immutable references against current store state."""
    from distill.store.criteria import _REF_PATTERN, CriteriaError

    project = project.strip()
    if not project:
        raise CriteriaError("E_SCOPE_REQUIRED", "project is required")
    connection = store._connect(create=False)
    checked_at = utc_now()
    if connection is None:
        return {
            "generation": 0,
            "checked_at": checked_at,
            "results": [{"ref": reference, "status": "unknown"} for reference in refs],
            "store": "absent",
        }
    try:
        results: list[JsonObject] = []
        for reference in refs:
            match = _REF_PATTERN.fullmatch(reference)
            if match is None:
                results.append({"ref": reference, "status": "unknown"})
                continue
            criterion_id, version_text = match.groups()
            criterion = connection.execute(
                "SELECT * FROM criteria WHERE id = ?", (criterion_id,)
            ).fetchone()
            if criterion is None:
                results.append({"ref": reference, "status": "unknown"})
                continue
            if criterion["project"] != project:
                results.append({"ref": reference, "status": "scope_mismatch"})
                continue
            version = connection.execute(
                "SELECT * FROM criterion_versions WHERE criterion_id = ? AND version = ?",
                (criterion_id, int(version_text)),
            ).fetchone()
            if version is None:
                results.append({"ref": reference, "status": "unknown"})
            elif version["status"] == "revoked":
                results.append({"ref": reference, "status": "revoked"})
            elif version["status"] == "superseded":
                result: JsonObject = {"ref": reference, "status": "superseded"}
                if not criterion["revoked"]:
                    result["current"] = _ref(criterion_id, int(criterion["current_version"]))
                results.append(result)
            elif version["confirmation"] == "none":
                results.append({"ref": reference, "status": "unconfirmed"})
            else:
                results.append({"ref": reference, "status": "eligible_current"})
        return {
            "generation": store._generation(connection),
            "checked_at": checked_at,
            "results": results,
        }
    except sqlite3.Error as error:
        raise CriteriaError(
            "E_STORE_UNAVAILABLE", f"Cannot read criteria store: {error}", store_error=True
        ) from error
    finally:
        connection.close()


def criteria_history(store: CriteriaStore, criterion_id: str) -> JsonObject:
    """Return all immutable versions and generation-stamped lifecycle events."""
    from distill.store.criteria import CriteriaError

    connection = store._connect(create=False)
    if connection is None:
        raise CriteriaError("E_NOT_FOUND", f"Criterion not found: {criterion_id}")
    try:
        criterion = connection.execute(
            "SELECT * FROM criteria WHERE id = ?", (criterion_id,)
        ).fetchone()
        if criterion is None:
            raise CriteriaError("E_NOT_FOUND", f"Criterion not found: {criterion_id}")
        versions = connection.execute(
            "SELECT * FROM criterion_versions WHERE criterion_id = ? ORDER BY version",
            (criterion_id,),
        ).fetchall()
        events = connection.execute(
            "SELECT * FROM criterion_events WHERE criterion_id = ? ORDER BY sequence",
            (criterion_id,),
        ).fetchall()
        return {
            "schema": "criteria-history/1",
            "producer": "distill",
            "producer_version": __version__,
            "generation": store._generation(connection),
            "id": criterion_id,
            "project": criterion["project"],
            "versions": [{**_row_to_version(row), "status": row["status"]} for row in versions],
            "events": [
                {
                    "event": row["event"],
                    "ref": _ref(criterion_id, int(row["version"])),
                    "generation": row["generation"],
                    "reason": row["reason"],
                    "origin": _json_load(row["origin"]),
                    "recorded_at": row["recorded_at"],
                }
                for row in events
            ],
        }
    except sqlite3.Error as error:
        raise CriteriaError(
            "E_STORE_UNAVAILABLE", f"Cannot read criteria store: {error}", store_error=True
        ) from error
    finally:
        connection.close()
