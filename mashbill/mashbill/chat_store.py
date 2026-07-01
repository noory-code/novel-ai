"""Chat conversation persistence — the disk SSOT for chat (D-2026-06-26-B).

In-memory chat sessions died on an app restart and the user lost real work. This
module shadows each live chat scope to one append-only file under the project at
``.noory/plot/chat/<scope>.json``, so conversations survive a restart and travel
with the project. The **engine is the sole writer** (no viewer race): the user
message is appended when a turn is sent, the assistant message on ``turn_complete``.

One conversation per scope, mirroring the one-live-session-per-scope registry.
Reopening restores the transcript *for reading* — it does not revive the CLI
session (a named v1 limit, see DECISIONS D-2026-06-26-B).
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from mashbill.storage import _ensure_project, _project_dir, _read_json, _write_json

_CHAT_DIRNAME = "chat"
_TITLE_CAP = 60


class ChatMessageRecord(BaseModel):
    """One persisted turn. ``id`` reuses the viewer's stable ``user_*`` / ``turn_*``
    ids so reopened rows keep collision-free keys."""

    id: str
    role: str  # "user" | "assistant"
    text: str
    ts: str


class ChatConversationDoc(BaseModel):
    schema_version: int = 1
    scope: str
    provider: str = ""
    title: str = ""
    created: str
    updated: str
    messages: list[ChatMessageRecord] = Field(default_factory=list)


def _now() -> str:
    return datetime.now(UTC).isoformat()


def scope_to_filename(scope: str) -> str:
    """``service:abc`` → ``service__abc.json`` (``:`` is awkward on some
    filesystems). Rejects path separators / traversal in the id (Fail Fast)."""
    if "/" in scope or "\\" in scope or ".." in scope:
        raise ValueError(f"unsafe chat scope: {scope!r}")
    return scope.replace(":", "__") + ".json"


def filename_to_scope(name: str) -> str:
    """Inverse of :func:`scope_to_filename`. The base word never contains
    ``__`` and the ``:`` sits right after it, so the first ``__`` is the
    separator (decode count=1 keeps any ``__`` inside the id intact)."""
    stem = name[:-5] if name.endswith(".json") else name
    return stem.replace("__", ":", 1)


def _chat_dir(plot_root: Path, project_id: str) -> Path:
    return _project_dir(plot_root, project_id) / _CHAT_DIRNAME


def _conversation_path(plot_root: Path, project_id: str, scope: str) -> Path:
    return _chat_dir(plot_root, project_id) / scope_to_filename(scope)


def append_user(
    plot_root: Path, project_id: str, scope: str, provider: str, msg_id: str, text: str
) -> None:
    """Append the user turn — creating the conversation file on first send
    (this is the empty-conversation guard: a scope merely clicked into never
    writes). ``title`` is set once from the first user message."""
    _ensure_project(plot_root, project_id)
    path = _conversation_path(plot_root, project_id, scope)
    now = _now()
    if path.exists():
        doc = ChatConversationDoc.model_validate(_read_json(path))
    else:
        doc = ChatConversationDoc(
            scope=scope,
            provider=provider,
            title=text.strip()[:_TITLE_CAP],
            created=now,
            updated=now,
        )
    doc.provider = provider
    doc.updated = now
    doc.messages.append(ChatMessageRecord(id=msg_id, role="user", text=text, ts=now))
    _write_json(path, doc.model_dump())


def append_assistant(
    plot_root: Path, project_id: str, scope: str, provider: str, msg_id: str, text: str
) -> None:
    """Append the assistant turn to an existing conversation. A no-op when the
    file is absent — an assistant reply with no preceding user message is not a
    real conversation."""
    _ensure_project(plot_root, project_id)
    path = _conversation_path(plot_root, project_id, scope)
    if not path.exists():
        return
    doc = ChatConversationDoc.model_validate(_read_json(path))
    now = _now()
    doc.provider = provider
    doc.updated = now
    doc.messages.append(ChatMessageRecord(id=msg_id, role="assistant", text=text, ts=now))
    _write_json(path, doc.model_dump())


def read_conversation(plot_root: Path, project_id: str, scope: str) -> ChatConversationDoc:
    """The full transcript for ``scope``. Raises ``FileNotFoundError`` (→ 404)
    when no conversation has been saved."""
    path = _conversation_path(plot_root, project_id, scope)
    return ChatConversationDoc.model_validate(_read_json(path))


def read_recent_transcript(
    plot_root: Path, project_id: str, scope: str, max_chars: int = 8000
) -> str:
    """Render the saved transcript for ``scope`` as a plain ``role: text`` block,
    most-recent-bounded to ``max_chars`` (D-2026-06-26-F).

    Re-fed to a FRESH coach session so it continues from what's already decided
    instead of re-asking. Returns ``""`` when no conversation is saved yet (a
    brand-new thread genuinely starts from scratch). Keeps the newest messages
    when over budget — the tail is what the next turn builds on.
    """
    try:
        doc = read_conversation(plot_root, project_id, scope)
    except FileNotFoundError:
        return ""
    if not doc.messages:
        return ""
    picked: list[str] = []
    total = 0
    for m in reversed(doc.messages):
        line = f"{m.role}: {m.text.strip()}"
        if total + len(line) > max_chars and picked:
            break
        picked.append(line)
        total += len(line)
    picked.reverse()
    header = (
        "[Earlier in this conversation — continue from here; what is already "
        "agreed below is settled, do not re-ask it]"
    )
    return header + "\n" + "\n".join(picked)


def list_conversations(plot_root: Path, project_id: str) -> list[dict[str, Any]]:
    """Saved conversations as metadata rows, newest-updated first. A corrupt /
    old-schema file is skipped rather than breaking the whole list."""
    chat_dir = _chat_dir(plot_root, project_id)
    if not chat_dir.exists():
        return []
    rows: list[dict[str, Any]] = []
    for path in chat_dir.glob("*.json"):
        try:
            doc = ChatConversationDoc.model_validate(_read_json(path))
        except Exception:  # noqa: BLE001 — a bad file must not break the list
            continue
        rows.append(
            {
                "scope": doc.scope,
                "title": doc.title,
                "provider": doc.provider,
                "updated": doc.updated,
                "message_count": len(doc.messages),
            }
        )
    rows.sort(key=lambda r: r["updated"], reverse=True)
    return rows
