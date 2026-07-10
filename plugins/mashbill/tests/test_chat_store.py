"""Chat conversation persistence (D-2026-06-26-B).

In-memory chat died on an app restart and the user lost real work. Conversations
now persist to ``.noory/plot/chat/<scope>.json`` — one append-only log per scope,
engine-side — so they survive a restart and travel with the project.
"""

from __future__ import annotations

import pytest

from mashbill.chat_store import (
    append_assistant,
    append_user,
    list_conversations,
    read_conversation,
    read_recent_transcript,
)
from mashbill.project_io import create_project
from mashbill.workspace import resolve_plot_root


def _project(tmp_path):
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    return plot_root, "alpha"


def test_append_user_creates_file_with_title(tmp_path):
    plot_root, pid = _project(tmp_path)
    append_user(plot_root, pid, "foundation", "claude-code", "user_1", "Define the mission")
    doc = read_conversation(plot_root, pid, "foundation")
    assert doc.scope == "foundation"
    assert doc.provider == "claude-code"
    assert doc.title == "Define the mission"  # first user message
    assert doc.created == doc.updated
    assert [(m.role, m.text) for m in doc.messages] == [("user", "Define the mission")]


def test_recent_transcript_empty_when_no_conversation(tmp_path):
    # A brand-new thread genuinely starts from scratch — no history block.
    plot_root, pid = _project(tmp_path)
    assert read_recent_transcript(plot_root, pid, "foundation") == ""


def test_recent_transcript_carries_decided_value_and_roles(tmp_path):
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


def test_recent_transcript_keeps_newest_under_budget(tmp_path):
    plot_root, pid = _project(tmp_path)
    for i in range(50):
        append_user(
            plot_root, pid, "foundation", "claude-code", f"u{i}", f"message number {i} " + "x" * 200
        )
    out = read_recent_transcript(plot_root, pid, "foundation", max_chars=1000)
    assert len(out) < 2000  # bounded
    assert "message number 49" in out  # newest kept
    assert "message number 0" not in out  # oldest dropped


def test_append_assistant_appends_and_bumps_updated(tmp_path):
    plot_root, pid = _project(tmp_path)
    append_user(plot_root, pid, "foundation", "claude-code", "user_1", "Hi")
    created = read_conversation(plot_root, pid, "foundation").created
    append_assistant(plot_root, pid, "foundation", "claude-code", "turn_1", "Hello back")
    doc = read_conversation(plot_root, pid, "foundation")
    assert [m.role for m in doc.messages] == ["user", "assistant"]
    assert doc.created == created  # unchanged
    assert doc.updated >= created  # advanced (or equal at worst)
    assert doc.title == "Hi"  # never overwritten


def test_parametric_scope_filename_and_roundtrip(tmp_path):
    plot_root, pid = _project(tmp_path)
    append_user(plot_root, pid, "service:abc123", "codex", "user_1", "Refund flow")
    # ':' is sanitised to '__' on disk, fs-safe
    assert (plot_root / "chat" / "service__abc123.json").exists()
    # round-trips back through read + list
    assert read_conversation(plot_root, pid, "service:abc123").scope == "service:abc123"
    scopes = [c["scope"] for c in list_conversations(plot_root, pid)]
    assert "service:abc123" in scopes


def test_traversal_in_scope_id_is_rejected(tmp_path):
    plot_root, pid = _project(tmp_path)
    with pytest.raises(ValueError):
        append_user(plot_root, pid, "service:../../evil", "codex", "user_1", "x")


def test_empty_conversation_not_written(tmp_path):
    plot_root, pid = _project(tmp_path)
    # No turn ran — clicking into a scope writes nothing.
    assert list_conversations(plot_root, pid) == []
    assert not (plot_root / "chat").exists()


def test_list_sorted_by_updated_desc(tmp_path):
    plot_root, pid = _project(tmp_path)
    append_user(plot_root, pid, "foundation", "claude-code", "user_1", "first")
    append_user(plot_root, pid, "actors", "claude-code", "user_2", "second")
    scopes = [c["scope"] for c in list_conversations(plot_root, pid)]
    assert scopes == ["actors", "foundation"]  # newest-updated first


def test_read_missing_conversation_raises(tmp_path):
    plot_root, pid = _project(tmp_path)
    with pytest.raises(FileNotFoundError):
        read_conversation(plot_root, pid, "entities")


def test_survives_simulated_restart(tmp_path):
    """The regression for the actual bug: write, then read from a fresh root
    handle (process-equivalent) — the transcript is still there."""
    plot_root, pid = _project(tmp_path)
    append_user(plot_root, pid, "project", "claude-code", "user_1", "the mission")
    append_assistant(plot_root, pid, "project", "claude-code", "turn_1", "pinned it")
    fresh_root = resolve_plot_root(str(tmp_path))  # as if a new engine process opened it
    doc = read_conversation(fresh_root, pid, "project")
    assert [m.text for m in doc.messages] == ["the mission", "pinned it"]
