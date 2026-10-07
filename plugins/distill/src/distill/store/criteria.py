"""SQLite persistence and lifecycle rules for project criteria."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from pathlib import Path
from typing import Any, NoReturn
from uuid import uuid4

from pydantic import ValidationError

from distill.store.criteria_models import (
    CriterionFields,
    RecordRequest,
    ReviseRequest,
    RevokeRequest,
    utc_now,
)
from distill.store.criteria_queries import _row_to_version
from distill.store.criteria_schema import install_schema

JsonObject = dict[str, Any]
_REF_PATTERN = re.compile(r"^distill:(CR-[0-9a-f]{12})@([1-9][0-9]*)$")
_VERSION_FIELDS = (
    "statement",
    "applies_when",
    "exceptions",
    "notes",
    "overrides",
    "confirmation",
    "ai_confidence",
    "origin",
)


class CriteriaError(Exception):
    """A stable public criteria error."""

    def __init__(self, code: str, message: str, *, store_error: bool = False) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.store_error = store_error

    def as_dict(self) -> dict[str, str]:
        """Return the public JSON error contract."""
        return {"error": self.code, "message": self.message}


def default_criteria_db() -> Path:
    """Return the global Distill database used by MCP criteria tools."""
    return Path.home() / ".distill" / "knowledge" / "metadata.db"


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _json_load(value: str) -> Any:
    return json.loads(value)


def _ref(criterion_id: str, version: int) -> str:
    return f"distill:{criterion_id}@{version}"


def _request_data(validated: JsonObject, supplied: JsonObject) -> JsonObject:
    """Remove producer-derived origin fields unless the caller supplied them."""
    request: JsonObject = json.loads(_canonical_json(validated))
    supplied_origin = supplied.get("origin")
    if isinstance(supplied_origin, dict) and isinstance(request.get("origin"), dict):
        if "captured_at" not in supplied_origin:
            request["origin"].pop("captured_at", None)
        if "quote_sha256" not in supplied_origin:
            request["origin"].pop("quote_sha256", None)
    return request


class CriteriaStore:
    """Own the criteria tables without coupling them to general knowledge records."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path is not None else default_criteria_db()

    def _connect(self, *, create: bool) -> sqlite3.Connection | None:
        if not self.db_path.exists() and not create:
            return None
        connection = None
        try:
            if create:
                self.db_path.parent.mkdir(parents=True, exist_ok=True)
            if create:
                connection = sqlite3.connect(self.db_path, timeout=30)
            else:
                connection = sqlite3.connect(
                    self.db_path.resolve().as_uri() + "?mode=ro", uri=True, timeout=30
                )
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA busy_timeout = 30000")
            if create:
                install_schema(connection)
            else:
                connection.execute("BEGIN")
                if (
                    connection.execute(
                        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='criteria_meta'"
                    ).fetchone()
                    is None
                ):
                    connection.close()
                    return None
            return connection
        except (OSError, sqlite3.Error) as error:
            if connection is not None:
                connection.close()
            raise CriteriaError(
                "E_STORE_UNAVAILABLE", f"Cannot open criteria store: {error}", store_error=True
            ) from error

    @staticmethod
    def _generation(connection: sqlite3.Connection) -> int:
        row = connection.execute(
            "SELECT value FROM criteria_meta WHERE key = 'generation'"
        ).fetchone()
        return int(row["value"]) if row is not None else 0

    @classmethod
    def _next_generation(cls, connection: sqlite3.Connection) -> int:
        generation = cls._generation(connection) + 1
        connection.execute(
            "UPDATE criteria_meta SET value = ? WHERE key = 'generation'", (generation,)
        )
        return generation

    @staticmethod
    def _validation_error(error: ValidationError) -> NoReturn:
        locations = {str(item) for detail in error.errors() for item in detail["loc"]}
        if any(detail["type"] == "string_too_long" for detail in error.errors()):
            code = "E_TOO_LONG"
        elif "project" in locations:
            code = "E_SCOPE_REQUIRED"
        elif "origin" in locations or any("source" in detail["msg"] for detail in error.errors()):
            code = "E_QUOTE_REQUIRED"
        elif {"applies_when", "exceptions", "kind", "any"} & locations:
            code = "E_INVALID_CONDITION"
        else:
            code = "E_INVALID_REQUEST"
        raise CriteriaError(code, error.errors()[0]["msg"]) from error

    @staticmethod
    def _require_key(idempotency_key: str) -> str:
        key = idempotency_key.strip()
        if not key:
            raise CriteriaError("E_INVALID_REQUEST", "idempotency_key is required")
        return key

    @staticmethod
    def _replay(
        connection: sqlite3.Connection, idempotency_key: str, payload_digest: str
    ) -> JsonObject | None:
        row = connection.execute(
            "SELECT payload_digest, response FROM criteria_requests WHERE idempotency_key = ?",
            (idempotency_key,),
        ).fetchone()
        if row is None:
            return None
        if row["payload_digest"] != payload_digest:
            raise CriteriaError(
                "E_IDEMPOTENCY_CONFLICT", "The idempotency key was used for another request"
            )
        response = dict(_json_load(row["response"]))
        response["replayed"] = True
        return response

    @staticmethod
    def _save_request(
        connection: sqlite3.Connection,
        idempotency_key: str,
        payload_digest: str,
        response: JsonObject,
    ) -> None:
        connection.execute(
            "INSERT INTO criteria_requests VALUES (?, ?, ?)",
            (idempotency_key, payload_digest, _canonical_json(response)),
        )

    @staticmethod
    def _identity(data: JsonObject) -> str:
        statement = " ".join(str(data["statement"]).split())

        def sorted_json_list(values: list[JsonObject]) -> list[str]:
            return sorted(
                _canonical_json({**value, "any": sorted(set(value["any"]))}) for value in values
            )

        return _digest(
            {
                "project": data["project"],
                "statement": statement,
                "applies_when": sorted_json_list(data["applies_when"]),
                "exceptions": sorted_json_list(data["exceptions"]),
                "notes": sorted(data["notes"]),
            }
        )

    @staticmethod
    def _new_id(connection: sqlite3.Connection) -> str:
        while True:
            criterion_id = f"CR-{uuid4().hex[:12]}"
            exists = connection.execute(
                "SELECT 1 FROM criteria WHERE id = ?", (criterion_id,)
            ).fetchone()
            if exists is None:
                return criterion_id

    @staticmethod
    def _version_values(data: JsonObject) -> tuple[object, ...]:
        return (
            data["statement"],
            _canonical_json(data["applies_when"]),
            _canonical_json(data["exceptions"]),
            _canonical_json(data["notes"]),
            _canonical_json(data["overrides"]),
            data["confirmation"],
            data["ai_confidence"],
            _canonical_json(data["origin"]),
        )

    def record(self, payload: JsonObject, *, idempotency_key: str) -> JsonObject:
        """Create version one after validating identity and source evidence."""
        try:
            request = RecordRequest.model_validate(payload)
        except ValidationError as error:
            self._validation_error(error)
        data = request.model_dump(mode="json")
        key = self._require_key(idempotency_key)
        request_digest = _digest({"action": "record", "payload": _request_data(data, payload)})
        connection = self._connect(create=True)
        assert connection is not None
        try:
            connection.execute("BEGIN IMMEDIATE")
            replay = self._replay(connection, key, request_digest)
            if replay is not None:
                connection.commit()
                return replay
            identity = self._identity(data)
            duplicate = connection.execute(
                "SELECT id, current_version FROM criteria "
                "WHERE identity_digest = ? AND revoked = 0",
                (identity,),
            ).fetchone()
            if duplicate is not None:
                raise CriteriaError(
                    "E_DUPLICATE_CRITERION",
                    f"An equivalent current criterion exists: "
                    f"{_ref(duplicate['id'], duplicate['current_version'])}",
                )
            criterion_id = self._new_id(connection)
            generation = self._next_generation(connection)
            recorded_at = utc_now()
            connection.execute(
                "INSERT INTO criteria VALUES (?, ?, 1, 0, ?, ?)",
                (criterion_id, data["project"], identity, recorded_at),
            )
            connection.execute(
                "INSERT INTO criterion_versions VALUES "
                "(?, 1, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, 'current')",
                (criterion_id, *self._version_values(data), recorded_at),
            )
            connection.execute(
                "INSERT INTO criterion_events "
                "(criterion_id, event, version, generation, reason, origin, recorded_at) "
                "VALUES (?, 'recorded', 1, ?, NULL, ?, ?)",
                (criterion_id, generation, _canonical_json(data["origin"]), recorded_at),
            )
            response: JsonObject = {
                "ref": _ref(criterion_id, 1),
                "generation": generation,
                "replayed": False,
            }
            self._save_request(connection, key, request_digest, response)
            connection.commit()
            return response
        except CriteriaError:
            connection.rollback()
            raise
        except sqlite3.Error as error:
            connection.rollback()
            raise CriteriaError(
                "E_STORE_UNAVAILABLE", f"Cannot write criteria store: {error}", store_error=True
            ) from error
        finally:
            connection.close()

    def revise(self, criterion_id: str, payload: JsonObject, *, idempotency_key: str) -> JsonObject:
        """Create the next immutable version using optimistic concurrency."""
        try:
            request = ReviseRequest.model_validate(payload)
        except ValidationError as error:
            self._validation_error(error)
        if request.origin.actor != "user":
            raise CriteriaError("E_QUOTE_REQUIRED", "Revision requires a user source")
        key = self._require_key(idempotency_key)
        request_data = request.model_dump(mode="json", exclude_unset=True)
        request_digest = _digest(
            {
                "action": "revise",
                "criterion_id": criterion_id,
                "payload": _request_data(request_data, payload),
            }
        )
        connection = self._connect(create=True)
        assert connection is not None
        try:
            connection.execute("BEGIN IMMEDIATE")
            replay = self._replay(connection, key, request_digest)
            if replay is not None:
                connection.commit()
                return replay
            criterion = connection.execute(
                "SELECT * FROM criteria WHERE id = ?", (criterion_id,)
            ).fetchone()
            if criterion is None:
                raise CriteriaError("E_NOT_FOUND", f"Criterion not found: {criterion_id}")
            if criterion["revoked"]:
                raise CriteriaError("E_REVOKED", f"Criterion is revoked: {criterion_id}")
            if request.project is not None and request.project != criterion["project"]:
                raise CriteriaError("E_SCOPE_IMMUTABLE", "A criterion project cannot be changed")
            if request.base_version != criterion["current_version"]:
                raise CriteriaError(
                    "E_VERSION_CONFLICT",
                    f"Expected version {criterion['current_version']}, got {request.base_version}",
                )
            old = connection.execute(
                "SELECT * FROM criterion_versions WHERE criterion_id = ? AND version = ?",
                (criterion_id, criterion["current_version"]),
            ).fetchone()
            assert old is not None
            old_data = _row_to_version(old)
            inherited: list[str] = []
            merged: JsonObject = {}
            for field in _VERSION_FIELDS:
                if field in request_data:
                    merged[field] = request_data[field]
                else:
                    merged[field] = old_data[field]
                    inherited.append(field)
            try:
                validated = CriterionFields.model_validate(merged).model_dump(mode="json")
            except ValidationError as error:
                self._validation_error(error)
            merged.update(validated)
            merged["project"] = criterion["project"]
            new_version = int(criterion["current_version"]) + 1
            generation = self._next_generation(connection)
            recorded_at = utc_now()
            connection.execute(
                "UPDATE criterion_versions SET status = 'superseded' "
                "WHERE criterion_id = ? AND version = ?",
                (criterion_id, criterion["current_version"]),
            )
            connection.execute(
                "INSERT INTO criterion_versions VALUES "
                "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'current')",
                (
                    criterion_id,
                    new_version,
                    *self._version_values(merged),
                    request.reason,
                    _ref(criterion_id, int(criterion["current_version"])),
                    recorded_at,
                ),
            )
            identity = self._identity(merged)
            duplicate = connection.execute(
                "SELECT id, current_version FROM criteria "
                "WHERE identity_digest = ? AND revoked = 0 AND id != ?",
                (identity, criterion_id),
            ).fetchone()
            if duplicate is not None:
                raise CriteriaError(
                    "E_DUPLICATE_CRITERION",
                    f"An equivalent current criterion exists: "
                    f"{_ref(duplicate['id'], duplicate['current_version'])}",
                )
            connection.execute(
                "UPDATE criteria SET current_version = ?, identity_digest = ? WHERE id = ?",
                (new_version, identity, criterion_id),
            )
            connection.execute(
                "INSERT INTO criterion_events "
                "(criterion_id, event, version, generation, reason, origin, recorded_at) "
                "VALUES (?, 'revised', ?, ?, ?, ?, ?)",
                (
                    criterion_id,
                    new_version,
                    generation,
                    request.reason,
                    _canonical_json(merged["origin"]),
                    recorded_at,
                ),
            )
            response = {
                "ref": _ref(criterion_id, new_version),
                "generation": generation,
                "inherited": inherited,
                "replayed": False,
            }
            self._save_request(connection, key, request_digest, response)
            connection.commit()
            return response
        except CriteriaError:
            connection.rollback()
            raise
        except sqlite3.Error as error:
            connection.rollback()
            raise CriteriaError(
                "E_STORE_UNAVAILABLE", f"Cannot write criteria store: {error}", store_error=True
            ) from error
        finally:
            connection.close()

    def revoke(self, criterion_id: str, payload: JsonObject, *, idempotency_key: str) -> JsonObject:
        """Retire the current version while preserving its complete history."""
        try:
            request = RevokeRequest.model_validate(payload)
        except ValidationError as error:
            self._validation_error(error)
        if request.origin.actor != "user":
            raise CriteriaError("E_QUOTE_REQUIRED", "Revocation requires a user source")
        key = self._require_key(idempotency_key)
        request_data = request.model_dump(mode="json")
        request_digest = _digest(
            {
                "action": "revoke",
                "criterion_id": criterion_id,
                "payload": _request_data(request_data, payload),
            }
        )
        connection = self._connect(create=True)
        assert connection is not None
        try:
            connection.execute("BEGIN IMMEDIATE")
            replay = self._replay(connection, key, request_digest)
            if replay is not None:
                connection.commit()
                return replay
            criterion = connection.execute(
                "SELECT * FROM criteria WHERE id = ?", (criterion_id,)
            ).fetchone()
            if criterion is None:
                raise CriteriaError("E_NOT_FOUND", f"Criterion not found: {criterion_id}")
            if criterion["revoked"]:
                raise CriteriaError("E_REVOKED", f"Criterion is revoked: {criterion_id}")
            if request.base_version != criterion["current_version"]:
                raise CriteriaError(
                    "E_VERSION_CONFLICT",
                    f"Expected version {criterion['current_version']}, got {request.base_version}",
                )
            generation = self._next_generation(connection)
            recorded_at = utc_now()
            connection.execute("UPDATE criteria SET revoked = 1 WHERE id = ?", (criterion_id,))
            connection.execute(
                "UPDATE criterion_versions SET status = 'revoked' "
                "WHERE criterion_id = ? AND version = ?",
                (criterion_id, criterion["current_version"]),
            )
            connection.execute(
                "INSERT INTO criterion_events "
                "(criterion_id, event, version, generation, reason, origin, recorded_at) "
                "VALUES (?, 'revoked', ?, ?, ?, ?, ?)",
                (
                    criterion_id,
                    criterion["current_version"],
                    generation,
                    request.reason,
                    _canonical_json(request_data["origin"]),
                    recorded_at,
                ),
            )
            response: JsonObject = {
                "ref": _ref(criterion_id, int(criterion["current_version"])),
                "generation": generation,
                "status": "revoked",
                "replayed": False,
            }
            self._save_request(connection, key, request_digest, response)
            connection.commit()
            return response
        except CriteriaError:
            connection.rollback()
            raise
        except sqlite3.Error as error:
            connection.rollback()
            raise CriteriaError(
                "E_STORE_UNAVAILABLE", f"Cannot write criteria store: {error}", store_error=True
            ) from error
        finally:
            connection.close()

    def current(self, project: str) -> JsonObject:
        """Return only confirmed current versions for one explicit project key."""
        from distill.store.criteria_queries import current_criteria

        return current_criteria(self, project)

    def check(self, project: str, refs: list[str]) -> JsonObject:
        """Resolve supplied immutable references against current store state."""
        from distill.store.criteria_queries import check_criteria

        return check_criteria(self, project, refs)

    def history(self, criterion_id: str) -> JsonObject:
        """Return all immutable versions and generation-stamped lifecycle events."""
        from distill.store.criteria_queries import criteria_history

        return criteria_history(self, criterion_id)
