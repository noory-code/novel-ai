"""Counterexamples found during independent review."""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from distill.store.criteria import CriteriaError, CriteriaStore
from distill.tools import criteria as tools
from tests.test_criteria import _origin, _record, _record_payload


def test_ai_revision_cannot_replace_a_user_criterion(tmp_path: Path) -> None:
    store = CriteriaStore(tmp_path / "db")
    first = _record(store)
    identifier = first["ref"].split(":")[1].split("@")[0]
    with pytest.raises(CriteriaError, match="E_QUOTE_REQUIRED"):
        store.revise(
            identifier,
            {
                "base_version": 1,
                "confirmation": "none",
                "origin": _origin(actor="ai"),
                "reason": "AI inference.",
            },
            idempotency_key="ai-revision",
        )
    assert [v["ref"] for v in store.current("test/app")["criteria"]] == [first["ref"]]


@pytest.mark.parametrize("field", ["quote", "source_ref", "host", "session_id", "via"])
def test_blank_source_fields_are_not_user_evidence(tmp_path: Path, field: str) -> None:
    store = CriteriaStore(tmp_path / "db")
    payload = _record_payload()
    target = (
        payload["origin"] if field in {"quote", "source_ref"} else payload["origin"]["recorded_by"]
    )
    target[field] = " \t "
    with pytest.raises(CriteriaError, match="E_QUOTE_REQUIRED"):
        store.record(payload, idempotency_key="blank-source")


def test_condition_alternative_order_does_not_create_a_duplicate(tmp_path: Path) -> None:
    store = CriteriaStore(tmp_path / "db")
    conditions = [{"kind": "path", "any": ["app/", "tests/"]}]
    _record(store, applies_when=conditions)
    conditions[0]["any"].reverse()
    with pytest.raises(CriteriaError, match="E_DUPLICATE_CRITERION"):
        _record(store, applies_when=conditions)


@pytest.mark.parametrize("method", ["current", "check", "history"])
def test_concurrent_revision_does_not_mix_query_generations(
    tmp_path: Path, monkeypatch: Any, method: str
) -> None:
    path = tmp_path / "db"
    store = CriteriaStore(path)
    first = _record(store)
    identifier = first["ref"].split(":")[1].split("@")[0]
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA journal_mode=WAL")
    original_connect = store._connect
    trigger = {
        "current": "SELECT v.*, c.current_version",
        "check": "SELECT * FROM criterion_versions",
        "history": "SELECT * FROM criterion_events",
    }[method]
    writer = CriteriaStore(path)

    class InterleavedConnection:
        def __init__(self, connection: Any) -> None:
            self.connection = connection
            self.fired = False

        def execute(self, sql: str, *args: Any) -> Any:
            if sql.startswith(trigger) and not self.fired:
                self.fired = True
                writer.revise(
                    identifier,
                    {
                        "base_version": 1,
                        "statement": "Return None.",
                        "origin": _origin(),
                        "reason": "Changed contract.",
                    },
                    idempotency_key="concurrent",
                )
            return self.connection.execute(sql, *args)

        def close(self) -> None:
            self.connection.close()

    monkeypatch.setattr(
        store, "_connect", lambda **kwargs: InterleavedConnection(original_connect(**kwargs))
    )
    if method == "current":
        result = store.current("test/app")
        assert [v["ref"] for v in result["criteria"]] == [first["ref"]]
        assert result["retired"] == []
    elif method == "check":
        result = store.check("test/app", [first["ref"]])
        assert result["results"] == [{"ref": first["ref"], "status": "eligible_current"}]
    else:
        result = store.history(identifier)
        assert len(result["versions"]) == len(result["events"]) == 1
    assert result["generation"] == 1
    assert writer.current("test/app")["generation"] == 2


def test_reading_existing_knowledge_does_not_install_criteria_tables(tmp_path: Path) -> None:
    path = tmp_path / "db"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE knowledge (id TEXT)")
    before = path.read_bytes()
    result = CriteriaStore(path).current("test/app")
    assert result["criteria"] == []
    assert path.read_bytes() == before


@pytest.mark.parametrize(
    "field,value,code",
    [
        ("statement", " ", "E_INVALID_REQUEST"),
        ("statement", "x" * 2001, "E_TOO_LONG"),
        ("quote", "x" * 2001, "E_TOO_LONG"),
    ],
)
def test_invalid_input_returns_the_specific_error(
    tmp_path: Path, field: str, value: str, code: str
) -> None:
    payload = _record_payload()
    target = payload["origin"] if field == "quote" else payload
    target[field] = value
    with pytest.raises(CriteriaError, match=code):
        CriteriaStore(tmp_path / "db").record(payload, idempotency_key="invalid")


def test_cli_and_mcp_wrappers_return_the_same_snapshot_and_errors(tmp_path: Path) -> None:
    path = tmp_path / "db"
    response = tools.criteria_record(_record_payload(), "record", db_path=path)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "distill",
            "criteria",
            "current",
            "--project",
            "test/app",
            "--db",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    cli = json.loads(result.stdout)
    mcp = tools.criteria_current("test/app", db_path=path)
    cli.pop("checked_at")
    mcp.pop("checked_at")
    assert cli == mcp
    identifier = response["ref"].split(":")[1].split("@")[0]
    error = tools.criteria_revise(
        identifier,
        {"base_version": 1, "origin": _origin(actor="ai"), "reason": "AI inference."},
        "invalid",
        db_path=path,
    )
    assert error["error"] == "E_QUOTE_REQUIRED"


@pytest.mark.parametrize("args", [["--unexpected", "value"], ["--db"], ["unexpected-positional"]])
def test_cli_rejects_unknown_or_incomplete_arguments(tmp_path: Path, args: list[str]) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "distill",
            "criteria",
            "current",
            "--project",
            "test/app",
            "--db",
            str(tmp_path / "db"),
            *args,
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert json.loads(result.stdout)["error"] == "E_INVALID_REQUEST"


def test_changed_revision_base_is_an_idempotency_conflict(tmp_path: Path) -> None:
    store = CriteriaStore(tmp_path / "db")
    first = _record(store)
    identifier = first["ref"].split(":")[1].split("@")[0]
    payload = {
        "base_version": 1,
        "statement": "Return None.",
        "origin": _origin(),
        "reason": "User change.",
    }
    store.revise(identifier, payload, idempotency_key="revise")
    with pytest.raises(CriteriaError, match="E_IDEMPOTENCY_CONFLICT"):
        store.revise(identifier, {**payload, "base_version": 2}, idempotency_key="revise")


def test_cli_check_reports_store_failure(tmp_path: Path) -> None:
    path = tmp_path / "directory.db"
    path.mkdir()
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "distill",
            "criteria",
            "check",
            "--project",
            "test/app",
            "--refs",
            "distill:CR-aaaaaaaaaaaa@1",
            "--db",
            str(path),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 3
    assert json.loads(result.stdout)["error"] == "E_STORE_UNAVAILABLE"


def test_cli_korean_json_uses_utf8_through_ascii_pipe(tmp_path: Path) -> None:
    import os

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "distill",
            "criteria",
            "current",
            "--project",
            "시험/프로젝트",
            "--db",
            str(tmp_path / "absent.db"),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "ascii"},
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["scope"]["key"] == "시험/프로젝트"
