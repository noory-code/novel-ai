"""Chat conversation persistence (D-2026-06-26-B).

In-memory chat died on an app restart and the user lost real work. Conversations
now persist to ``.noory/plot/chat/<scope>.json`` — one append-only log per scope,
engine-side — so they survive a restart and travel with the project.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mashbill import chat_store
from mashbill.chat_store import (
    append_assistant,
    append_assistant_to_conversation,
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


def _project(tmp_path: Path) -> tuple[Path, str]:
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    return plot_root, "alpha"


def test_append_user_creates_file_with_title(tmp_path: Path) -> None:
    plot_root, pid = _project(tmp_path)
    append_user(plot_root, pid, "foundation", "claude-code", "user_1", "Define the mission")
    doc = read_conversation(plot_root, pid, "foundation")
    assert doc.scope == "foundation"
    assert doc.provider == "claude-code"
    assert doc.title == "Define the mission"  # first user message
    assert doc.conversation_id is not None
    assert doc.created == doc.updated
    assert [(m.role, m.text) for m in doc.messages] == [("user", "Define the mission")]


def test_recent_transcript_empty_when_no_conversation(tmp_path: Path) -> None:
    # A brand-new thread genuinely starts from scratch — no history block.
    plot_root, pid = _project(tmp_path)
    assert read_recent_transcript(plot_root, pid, "foundation") == ""


def test_recent_transcript_carries_decided_value_and_roles(tmp_path: Path) -> None:
    # D-2026-06-26-F: a fresh session must see what was already settled so it
    # doesn't re-ask (the user's repeated "I already wrote it above" complaint).
    plot_root, pid = _project(tmp_path)
    append_user(
        plot_root, pid, "foundation", "claude-code", "u1", "미션은 '혼자 만드는 사람을 돕는다'"
    )
    append_assistant(plot_root, pid, "foundation", "claude-code", "a1", "좋아요, 그렇게 잡을게요")
    out = read_recent_transcript(plot_root, pid, "foundation")
    assert "혼자 만드는 사람을 돕는다" in out  # the settled value survives
    assert "user:" in out and "assistant:" in out
    assert "do not re-ask" in out  # the header instructs continuation


def test_recent_transcript_keeps_newest_under_budget(tmp_path: Path) -> None:
    plot_root, pid = _project(tmp_path)
    for i in range(50):
        append_user(
            plot_root, pid, "foundation", "claude-code", f"u{i}", f"message number {i} " + "x" * 200
        )
    out = read_recent_transcript(plot_root, pid, "foundation", max_chars=1000)
    assert len(out) < 2000  # bounded
    assert "message number 49" in out  # newest kept
    assert "message number 0" not in out  # oldest dropped


def test_append_assistant_appends_and_bumps_updated(tmp_path: Path) -> None:
    plot_root, pid = _project(tmp_path)
    append_user(plot_root, pid, "foundation", "claude-code", "user_1", "Hi")
    created = read_conversation(plot_root, pid, "foundation").created
    append_assistant(plot_root, pid, "foundation", "claude-code", "turn_1", "Hello back")
    doc = read_conversation(plot_root, pid, "foundation")
    assert [m.role for m in doc.messages] == ["user", "assistant"]
    assert doc.created == created  # unchanged
    assert doc.updated >= created  # advanced (or equal at worst)
    assert doc.title == "Hi"  # never overwritten


def test_append_assistant_to_unknown_conversation_falls_back_to_current(
    tmp_path: Path,
) -> None:
    plot_root, pid = _project(tmp_path)
    append_user(plot_root, pid, "foundation", "codex", "user_1", "Hi")

    append_assistant_to_conversation(
        plot_root,
        pid,
        "foundation",
        "codex",
        "turn_1",
        "Hello back",
        "unknown-conversation-id",
    )

    doc = read_conversation(plot_root, pid, "foundation")
    assert [(message.role, message.text) for message in doc.messages] == [
        ("user", "Hi"),
        ("assistant", "Hello back"),
    ]


def test_parametric_scope_filename_and_roundtrip(tmp_path: Path) -> None:
    plot_root, pid = _project(tmp_path)
    append_user(plot_root, pid, "service:abc123", "codex", "user_1", "Refund flow")
    # ':' is sanitised to '__' on disk, fs-safe
    assert (plot_root / "chat" / "service__abc123.json").exists()
    # round-trips back through read + list
    assert read_conversation(plot_root, pid, "service:abc123").scope == "service:abc123"
    scopes = [c["scope"] for c in list_conversations(plot_root, pid)]
    assert "service:abc123" in scopes


def test_traversal_in_scope_id_is_rejected(tmp_path: Path) -> None:
    plot_root, pid = _project(tmp_path)
    with pytest.raises(ValueError):
        append_user(plot_root, pid, "service:../../evil", "codex", "user_1", "x")


def test_empty_conversation_not_written(tmp_path: Path) -> None:
    plot_root, pid = _project(tmp_path)
    # No turn ran — clicking into a scope writes nothing.
    assert list_conversations(plot_root, pid) == []
    assert not (plot_root / "chat").exists()


def test_list_sorted_by_updated_desc(tmp_path: Path) -> None:
    plot_root, pid = _project(tmp_path)
    append_user(plot_root, pid, "foundation", "claude-code", "user_1", "first")
    append_user(plot_root, pid, "actors", "claude-code", "user_2", "second")
    scopes = [c["scope"] for c in list_conversations(plot_root, pid)]
    assert scopes == ["actors", "foundation"]  # newest-updated first


def test_read_missing_conversation_raises(tmp_path: Path) -> None:
    plot_root, pid = _project(tmp_path)
    with pytest.raises(FileNotFoundError):
        read_conversation(plot_root, pid, "entities")


def test_survives_simulated_restart(tmp_path: Path) -> None:
    """The regression for the actual bug: write, then read from a fresh root
    handle (process-equivalent) — the transcript is still there."""
    plot_root, pid = _project(tmp_path)
    append_user(plot_root, pid, "project", "claude-code", "user_1", "the mission")
    append_assistant(plot_root, pid, "project", "claude-code", "turn_1", "pinned it")
    fresh_root = resolve_plot_root(str(tmp_path))  # as if a new engine process opened it
    doc = read_conversation(fresh_root, pid, "project")
    assert [m.text for m in doc.messages] == ["the mission", "pinned it"]


def test_archive_current_moves_messages_and_clears_recent_transcript(tmp_path: Path) -> None:
    plot_root, pid = _project(tmp_path)
    append_user(plot_root, pid, "foundation", "codex", "u1", "the old mission")

    ended_id = archive_current_conversation(plot_root, pid, "foundation")

    assert ended_id is not None
    assert ended_id.startswith("foundation__")
    assert ended_id.endswith("Z.json")
    assert not (plot_root / "chat" / "foundation.json").exists()
    assert read_recent_transcript(plot_root, pid, "foundation") == ""
    assert read_conversation_by_id(plot_root, pid, ended_id).messages[0].text == "the old mission"


def test_list_includes_current_and_ended_with_ids_newest_first(tmp_path: Path) -> None:
    plot_root, pid = _project(tmp_path)
    append_user(plot_root, pid, "foundation", "codex", "u1", "old question")
    ended_id = archive_current_conversation(plot_root, pid, "foundation")
    append_user(plot_root, pid, "foundation", "codex", "u2", "new question")

    rows = list_conversations(plot_root, pid)

    assert [row["title"] for row in rows] == ["new question", "old question"]
    assert [row["ended"] for row in rows] == [False, True]
    assert rows[0]["id"] == "foundation.json"
    assert rows[1]["id"] == ended_id
    assert all(row["scope"] == "foundation" for row in rows)
    assert all(row["conversation_id"] for row in rows)
    assert rows[0]["conversation_id"] != rows[1]["conversation_id"]


def test_reopen_swaps_current_and_ended_conversations(tmp_path: Path) -> None:
    plot_root, pid = _project(tmp_path)
    append_user(plot_root, pid, "foundation", "codex", "u1", "chosen old question")
    chosen_conversation_id = read_conversation(plot_root, pid, "foundation").conversation_id
    chosen_id = archive_current_conversation(plot_root, pid, "foundation")
    assert chosen_id is not None
    assert (
        read_conversation_by_id(plot_root, pid, chosen_id).conversation_id == chosen_conversation_id
    )
    append_user(plot_root, pid, "foundation", "codex", "u2", "current question")
    current_conversation_id = read_conversation(plot_root, pid, "foundation").conversation_id
    assert current_conversation_id != chosen_conversation_id

    reopened = reopen_conversation(plot_root, pid, chosen_id)

    assert reopened.scope == "foundation"
    assert reopened.conversation_id == chosen_conversation_id
    current = read_conversation(plot_root, pid, "foundation")
    assert current.title == "chosen old question"
    assert current.conversation_id == chosen_conversation_id
    rows = list_conversations(plot_root, pid)
    assert {(row["title"], row["ended"]) for row in rows} == {
        ("chosen old question", False),
        ("current question", True),
    }
    transcript = read_recent_transcript(plot_root, pid, "foundation")
    assert "chosen old question" in transcript
    assert "current question" not in transcript
    assert {row["conversation_id"] for row in rows} == {
        chosen_conversation_id,
        current_conversation_id,
    }


def test_legacy_conversation_without_id_reads_and_gets_id_on_append(tmp_path: Path) -> None:
    plot_root, pid = _project(tmp_path)
    append_user(plot_root, pid, "foundation", "codex", "u1", "legacy question")
    path = plot_root / "chat" / "foundation.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw.pop("conversation_id")
    path.write_text(json.dumps(raw), encoding="utf-8")

    assert read_conversation(plot_root, pid, "foundation").conversation_id is None
    assert list_conversations(plot_root, pid)[0]["conversation_id"] is None

    append_user(plot_root, pid, "foundation", "codex", "u2", "continued")

    assigned = read_conversation(plot_root, pid, "foundation").conversation_id
    assert assigned is not None
    assert chat_store.current_conversation_id(plot_root, pid, "foundation") == assigned


def test_current_conversation_id_backfills_legacy_current_file(tmp_path: Path) -> None:
    plot_root, pid = _project(tmp_path)
    append_user(plot_root, pid, "foundation", "codex", "u1", "legacy question")
    path = plot_root / "chat" / "foundation.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw.pop("conversation_id")
    path.write_text(json.dumps(raw), encoding="utf-8")

    assigned = chat_store.current_conversation_id(plot_root, pid, "foundation")

    assert assigned is not None
    assert read_conversation(plot_root, pid, "foundation").conversation_id == assigned
    assert chat_store.current_conversation_id(plot_root, pid, "actors") is None


def test_archive_empty_current_is_noop(tmp_path: Path) -> None:
    plot_root, pid = _project(tmp_path)

    assert archive_current_conversation(plot_root, pid, "foundation") is None
    assert list_conversations(plot_root, pid) == []


def test_conversation_id_cannot_escape_chat_directory(tmp_path: Path) -> None:
    plot_root, pid = _project(tmp_path)

    with pytest.raises(ValueError, match="unsafe conversation id"):
        read_conversation_by_id(plot_root, pid, "../outside.json")
    with pytest.raises(ValueError, match="unsafe conversation id"):
        reopen_conversation(plot_root, pid, "../outside.json")
