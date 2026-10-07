"""Criteria records keep current project guidance separate from general recall."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest

from distill.store.criteria import CriteriaError, CriteriaStore


def _origin(*, actor: str = "user", message: str = "msg-1") -> dict[str, Any]:
    return {
        "kind": "user_statement",
        "source_ref": f"session:codex/test/{message}",
        "quote": "Keep project criteria explicit.",
        "actor": actor,
        "recorded_by": {"host": "codex", "session_id": "test", "via": "cli"},
    }


def _record_payload(
    *,
    project: str = "test/app",
    confirmation: str = "user_stated",
    exceptions: list[dict[str, Any]] | None = None,
    notes: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "project": project,
        "statement": "Raise ConfigError for invalid input.",
        "applies_when": [{"kind": "path", "any": ["app/"]}],
        "exceptions": exceptions or [],
        "notes": notes or [],
        "overrides": [],
        "confirmation": confirmation,
        "ai_confidence": 0.99 if confirmation == "none" else None,
        "origin": _origin(actor="ai" if confirmation == "none" else "user"),
    }


def _record(store: CriteriaStore, **overrides: Any) -> dict[str, Any]:
    payload = _record_payload()
    payload.update(overrides)
    return store.record(payload, idempotency_key=f"record:{uuid4().hex}")


def test_revise_keeps_only_the_new_version_current_and_preserves_history(tmp_path: Path) -> None:
    store = CriteriaStore(tmp_path / "criteria.db")
    recorded = _record(store)
    criterion_id = recorded["ref"].split(":", 1)[1].split("@", 1)[0]

    revised = store.revise(
        criterion_id,
        {
            "base_version": 1,
            "statement": "Return None for invalid input.",
            "origin": _origin(message="msg-2"),
            "reason": "The caller now handles absence.",
        },
        idempotency_key="revise:1",
    )

    snapshot = store.current("test/app")
    assert [item["ref"] for item in snapshot["criteria"]] == [revised["ref"]]
    assert snapshot["retired"] == [
        {"ref": recorded["ref"], "status": "superseded", "by": revised["ref"]}
    ]
    assert store.check("test/app", [recorded["ref"]])["results"] == [
        {"ref": recorded["ref"], "status": "superseded", "current": revised["ref"]}
    ]

    history = store.history(criterion_id)
    assert [version["ref"] for version in history["versions"]] == [
        recorded["ref"],
        revised["ref"],
    ]
    assert [event["generation"] for event in history["events"]] == [1, 2]
    assert history["versions"][0]["origin"]["quote_sha256"]
    assert history["versions"][1]["reason"] == "The caller now handles absence."


def test_idempotency_covers_all_meaningful_fields(tmp_path: Path) -> None:
    store = CriteriaStore(tmp_path / "criteria.db")
    payload = _record_payload()
    first = store.record(payload, idempotency_key="codex:S1:1")
    replay = store.record(payload, idempotency_key="codex:S1:1")
    assert first["replayed"] is False
    assert replay == {**first, "replayed": True}

    changed = _record_payload()
    changed["origin"]["recorded_by"]["session_id"] = "other"
    with pytest.raises(CriteriaError, match="E_IDEMPOTENCY_CONFLICT"):
        store.record(changed, idempotency_key="codex:S1:1")

    changed = _record_payload(notes=["Only for public parsing."])
    with pytest.raises(CriteriaError, match="E_IDEMPOTENCY_CONFLICT"):
        store.record(changed, idempotency_key="codex:S1:1")


def test_check_excludes_unconfirmed_other_project_and_unknown_versions(tmp_path: Path) -> None:
    store = CriteriaStore(tmp_path / "criteria.db")
    unconfirmed = _record(store, **_record_payload(confirmation="none"))
    other = _record(store, **_record_payload(project="test/other"))
    missing_version = unconfirmed["ref"].rsplit("@", 1)[0] + "@99"

    assert store.current("test/app")["criteria"] == []
    assert store.check("test/app", [unconfirmed["ref"], other["ref"], missing_version])[
        "results"
    ] == [
        {"ref": unconfirmed["ref"], "status": "unconfirmed"},
        {"ref": other["ref"], "status": "scope_mismatch"},
        {"ref": missing_version, "status": "unknown"},
    ]


def test_duplicate_identity_includes_conditions_and_revocation_does_not_revive_id(
    tmp_path: Path,
) -> None:
    store = CriteriaStore(tmp_path / "criteria.db")
    first = _record(store)
    different = _record(
        store,
        **_record_payload(exceptions=[{"kind": "path", "any": ["app/vendor/"]}]),
    )
    assert first["ref"].split("@", 1)[0] != different["ref"].split("@", 1)[0]

    with pytest.raises(CriteriaError, match="E_DUPLICATE_CRITERION"):
        store.record(_record_payload(), idempotency_key="duplicate")

    criterion_id = first["ref"].split(":", 1)[1].split("@", 1)[0]
    store.revoke(
        criterion_id,
        {"base_version": 1, "origin": _origin(message="msg-3"), "reason": "No longer used."},
        idempotency_key="revoke:1",
    )
    replacement = store.record(_record_payload(), idempotency_key="replacement")
    assert first["ref"].split("@", 1)[0] != replacement["ref"].split("@", 1)[0]
    assert store.check("test/app", [first["ref"]])["results"] == [
        {"ref": first["ref"], "status": "revoked"}
    ]


def test_revision_conflict_and_revoked_criterion_fail_without_writing(tmp_path: Path) -> None:
    store = CriteriaStore(tmp_path / "criteria.db")
    first = _record(store)
    criterion_id = first["ref"].split(":", 1)[1].split("@", 1)[0]
    revision = {
        "base_version": 1,
        "statement": "Return None for invalid input.",
        "origin": _origin(message="msg-2"),
        "reason": "Updated contract.",
    }
    store.revise(criterion_id, revision, idempotency_key="revise:1")

    with pytest.raises(CriteriaError, match="E_VERSION_CONFLICT"):
        store.revise(criterion_id, revision, idempotency_key="revise:2")

    store.revoke(
        criterion_id,
        {"base_version": 2, "origin": _origin(message="msg-3"), "reason": "Retired."},
        idempotency_key="revoke:1",
    )
    with pytest.raises(CriteriaError, match="E_REVOKED"):
        store.revise(
            criterion_id,
            {**revision, "base_version": 2},
            idempotency_key="revise:after-revoke",
        )


def test_cli_uses_json_contract_and_store_failures_exit_three(tmp_path: Path) -> None:
    missing_db = tmp_path / "missing.db"
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
            str(missing_db),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["store"] == "absent"

    unreadable_db = tmp_path / "directory.db"
    unreadable_db.mkdir()
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
            str(unreadable_db),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 3
    assert json.loads(result.stdout)["error"] == "E_STORE_UNAVAILABLE"


def test_criteria_import_does_not_load_fastembed() -> None:
    script = "import sys; import distill.store.criteria; print('fastembed' in sys.modules)"
    result = subprocess.run(
        [sys.executable, "-c", script], check=True, capture_output=True, text=True
    )
    assert result.stdout.strip() == "False"


@pytest.mark.parametrize("field", ["project", "statement"])
def test_blank_required_text_cannot_create_a_criterion(tmp_path: Path, field: str) -> None:
    store = CriteriaStore(tmp_path / "criteria.db")
    payload = _record_payload()
    payload[field] = " \t "
    with pytest.raises(CriteriaError):
        store.record(payload, idempotency_key="blank")
    assert store.current("test/app")["generation"] == 0


@pytest.mark.parametrize("path", ["C:/outside/file.py", "C:relative.py", "../outside", "/root"])
def test_conditions_reject_paths_outside_the_repository(tmp_path: Path, path: str) -> None:
    store = CriteriaStore(tmp_path / "criteria.db")
    payload = _record_payload()
    payload["applies_when"] = [{"kind": "path", "any": [path]}]
    with pytest.raises(CriteriaError):
        store.record(payload, idempotency_key="outside")
    assert store.current("test/app")["generation"] == 0


@pytest.mark.parametrize("action", ["revise", "revoke"])
def test_changes_require_a_nonblank_reason(tmp_path: Path, action: str) -> None:
    store = CriteriaStore(tmp_path / "criteria.db")
    first = _record(store)
    criterion_id = first["ref"].split(":", 1)[1].split("@", 1)[0]
    with pytest.raises(CriteriaError):
        getattr(store, action)(
            criterion_id,
            {"base_version": 1, "origin": _origin(), "reason": "  "},
            idempotency_key="blank-reason",
        )
    assert store.current("test/app")["generation"] == 1
