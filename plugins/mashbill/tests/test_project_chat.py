"""Project conversation and turn-scope regressions (D-2026-10-15-P)."""

from __future__ import annotations

import json
from pathlib import Path

from mashbill.chat_store import (
    append_assistant,
    append_user,
    archive_current_conversation,
    list_conversations,
    read_conversation,
    read_conversation_by_id,
    read_recent_transcript,
    reopen_conversation,
)
from mashbill.project_io import create_project
from mashbill.workspace import resolve_plot_root


def _project(tmp_path: Path) -> Path:
    root = resolve_plot_root(str(tmp_path))
    create_project(root, "alpha", "Alpha")
    return root


def test_one_project_file_keeps_each_turn_scope(tmp_path: Path) -> None:
    root = _project(tmp_path)
    append_user(root, "alpha", "foundation", "codex", "u1", "Mission")
    append_assistant(root, "alpha", "foundation", "codex", "a1", "Agreed")
    append_user(root, "alpha", "entities", "codex", "u2", "Entities")
    append_assistant(root, "alpha", "entities", "codex", "a2", "", error="failed")

    doc = read_conversation(root, "alpha", "project")
    assert doc.schema_version == 2
    assert doc.scope == "project"
    assert [m.scope for m in doc.messages] == ["foundation", "foundation", "entities", "entities"]
    assert [p.name for p in (root / "chat").glob("*.json")] == ["project.json"]
    assert list_conversations(root, "alpha")[0]["legacy"] is False


def test_transcript_cross_scope_hard_cap_and_no_current_user(tmp_path: Path) -> None:
    root = _project(tmp_path)
    append_user(root, "alpha", "foundation", "codex", "u1", "old decision")
    append_assistant(root, "alpha", "foundation", "codex", "a1", "accepted")
    append_user(root, "alpha", "entities", "codex", "u2", "new decision " + "x" * 200)
    append_assistant(root, "alpha", "entities", "codex", "a2", "bad", error="failed")
    append_user(root, "alpha", "services", "codex", "u3", "current text")

    transcript = read_recent_transcript(
        root, "alpha", "services", max_chars=260, exclude_message_id="u3"
    )
    assert len(transcript) <= 260
    assert "[entities] user:" in transcript
    assert "current text" not in transcript
    assert "bad" not in transcript


def test_legacy_read_then_materialize_preserves_sources(tmp_path: Path) -> None:
    root = _project(tmp_path)
    chat = root / "chat"
    chat.mkdir()
    for scope, text in (("project", "project old"), ("foundation", "foundation old")):
        (chat / f"{scope}.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "scope": scope,
                    "conversation_id": scope,
                    "created": "2026-01-01T00:00:00Z",
                    "updated": "2026-01-01T00:00:00Z",
                    "messages": [
                        {"id": "same", "role": "user", "text": text, "ts": "2026-01-01T00:00:00Z"}
                    ],
                }
            ),
            encoding="utf-8",
        )
    original = (chat / "foundation.json").read_bytes()
    synthetic = read_conversation(root, "alpha", "project")
    assert synthetic.schema_version == 2
    assert [m.scope for m in synthetic.messages] == ["foundation", "project"]
    assert len({m.id for m in synthetic.messages}) == 2
    assert (chat / "project.json").read_text(encoding="utf-8").find('schema_version": 1') >= 0

    append_user(root, "alpha", "entities", "codex", "new", "new turn")
    doc = read_conversation(root, "alpha", "project")
    assert len(doc.messages) == 3
    assert (chat / "foundation.json").read_bytes() == original
    assert any(p.name.startswith("project__") for p in chat.glob("*.json"))
    assert len([r for r in list_conversations(root, "alpha") if r["legacy"]]) == 2


def test_legacy_corrupt_archive_and_retry_do_not_duplicate_messages(tmp_path: Path) -> None:
    root = _project(tmp_path)
    chat = root / "chat"
    chat.mkdir()
    source = {
        "schema_version": 1,
        "scope": "project",
        "conversation_id": "old-id",
        "created": "2026-01-01",
        "updated": "2026-01-01",
        "messages": [{"id": "u1", "role": "user", "text": "old", "ts": "2026-01-01"}],
    }
    (chat / "project.json").write_text(json.dumps(source), encoding="utf-8")
    (chat / "entities.json").write_text("{broken", encoding="utf-8")
    (chat / "actors__20260101T000000Z.json").write_text(
        json.dumps({**source, "scope": "actors"}), encoding="utf-8"
    )
    # Simulate a previous attempt that copied the source before the v2 write.
    (chat / "project__20260101T000000Z.json").write_bytes((chat / "project.json").read_bytes())
    append_user(root, "alpha", "entities", "codex", "u2", "new")
    append_user(root, "alpha", "actors", "codex", "u3", "next")

    doc = read_conversation(root, "alpha", "project")
    assert [m.text for m in doc.messages] == ["old", "new", "next"]
    assert len(list(chat.glob("project__*.json"))) == 1
    assert (
        read_conversation_by_id(root, "alpha", "actors__20260101T000000Z.json").messages[0].scope
        == "actors"
    )
    assert len([r for r in list_conversations(root, "alpha") if r["legacy"]]) == 2


def test_reopen_legacy_imports_copy_and_keeps_source(tmp_path: Path) -> None:
    root = _project(tmp_path)
    chat = root / "chat"
    chat.mkdir()
    source = chat / "foundation.json"
    source.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "scope": "foundation",
                "conversation_id": "legacy-id",
                "created": "2026-01-01",
                "updated": "2026-01-01",
                "title": "past",
                "messages": [{"id": "u1", "role": "user", "text": "past", "ts": "2026-01-01"}],
            }
        ),
        encoding="utf-8",
    )
    original = source.read_bytes()
    append_user(root, "alpha", "entities", "codex", "u2", "active")
    reopened = reopen_conversation(root, "alpha", "foundation.json")

    assert reopened.conversation_id not in ("legacy-id", None)
    assert reopened.messages[0].scope == "foundation"
    assert source.read_bytes() == original
    assert read_conversation_by_id(root, "alpha", "foundation.json").conversation_id == "legacy-id"
    assert read_conversation(root, "alpha", "project").title == "past"
    assert any(
        row["ended"]
        and row["legacy"] is False
        and "active" in [m.text for m in read_conversation_by_id(root, "alpha", row["id"]).messages]
        for row in list_conversations(root, "alpha")
    )


def test_corrupt_old_project_is_preserved_before_first_send(tmp_path: Path) -> None:
    root = _project(tmp_path)
    chat = root / "chat"
    chat.mkdir()
    (chat / "project.json").write_text("{broken", encoding="utf-8")
    append_user(root, "alpha", "foundation", "codex", "u1", "new")

    assert read_conversation(root, "alpha", "project").messages[0].scope == "foundation"
    assert any(p.read_text(encoding="utf-8") == "{broken" for p in chat.glob("project__*.json"))


def test_reset_does_not_resynthesize_legacy_current_files(tmp_path: Path) -> None:
    root = _project(tmp_path)
    chat = root / "chat"
    chat.mkdir()
    (chat / "foundation.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "scope": "foundation",
                "created": "2026-01-01",
                "updated": "2026-01-01",
                "messages": [{"id": "u1", "role": "user", "text": "legacy", "ts": "2026-01-01"}],
            }
        ),
        encoding="utf-8",
    )
    append_user(root, "alpha", "entities", "codex", "u2", "new")
    ended_id = archive_current_conversation(root, "alpha", "project")
    assert ended_id is not None

    try:
        read_conversation(root, "alpha", "project")
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("reset must leave no current conversation")
    assert archive_current_conversation(root, "alpha", "project") is None
    assert not (chat / "project.json").exists()
    assert len(list(chat.glob("project__*.json"))) == 1
