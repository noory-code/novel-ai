"""Project chat persistence and legacy history (D-2026-10-15-P).

The engine writes one current conversation at ``chat/project.json``. Each
message carries the scope of its turn; older per-scope files remain history.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from mashbill.chat_migration import legacy_doc, materialize, synthesize
from mashbill.chat_providers.base import DEFAULT_CHAT_SCOPE, CanvasAddition
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
    scope: str = DEFAULT_CHAT_SCOPE
    error: str | None = Field(default=None, exclude_if=lambda value: value is None)
    error_code: str | None = Field(default=None, exclude_if=lambda value: value is None)
    # What the turn added outside its own canvas (D-2026-10-15-A).
    added_elsewhere: list[CanvasAddition] | None = Field(
        default=None, exclude_if=lambda value: value is None
    )


class ChatConversationDoc(BaseModel):
    schema_version: int = 2
    conversation_id: str | None = None
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
    scope_to_filename(scope)  # validate even though current storage is project-wide
    return _chat_dir(plot_root, project_id) / "project.json"


def _conversation_id_path(plot_root: Path, project_id: str, conversation_id: str) -> Path:
    """Resolve a list-row id to one direct child of the chat directory."""
    if (
        not conversation_id
        or not conversation_id.endswith(".json")
        or "/" in conversation_id
        or "\\" in conversation_id
        or ".." in conversation_id
        or Path(conversation_id).name != conversation_id
    ):
        raise ValueError(f"unsafe conversation id: {conversation_id!r}")
    chat_dir = _chat_dir(plot_root, project_id)
    path = chat_dir / conversation_id
    if path.is_symlink() or path.resolve().parent != chat_dir.resolve():
        raise ValueError(f"unsafe conversation id: {conversation_id!r}")
    return path


def _archive_path(current_path: Path) -> Path:
    """Choose a filesystem-safe, non-overwriting UTC-stamped archive path."""
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    base = current_path.with_name(f"{current_path.stem}__{stamp}{current_path.suffix}")
    candidate = base
    collision = 1
    while candidate.exists():
        candidate = base.with_stem(f"{base.stem}__{collision}")
        collision += 1
    return candidate


def _ensure_conversation_id(doc: ChatConversationDoc) -> str:
    """Assign the durable identity once while preserving existing identities."""
    if doc.conversation_id is None:
        doc.conversation_id = uuid4().hex
    return doc.conversation_id


def append_user(
    plot_root: Path, project_id: str, scope: str, provider: str, msg_id: str, text: str
) -> None:
    """Append a scoped user turn to the current project conversation."""
    _ensure_project(plot_root, project_id)
    path = _conversation_path(plot_root, project_id, scope)
    converted = None
    if path.exists() or not _has_v2_history(path.parent):
        converted = materialize(path.parent, _archive_path(path))
    now = _now()
    if converted is not None:
        doc = ChatConversationDoc.model_validate(converted)
    else:
        doc = ChatConversationDoc(
            conversation_id=uuid4().hex,
            scope=DEFAULT_CHAT_SCOPE,
            provider=provider,
            title=text.strip()[:_TITLE_CAP],
            created=now,
            updated=now,
        )
    _ensure_conversation_id(doc)
    doc.provider = provider
    doc.updated = now
    doc.messages.append(ChatMessageRecord(id=msg_id, role="user", text=text, ts=now, scope=scope))
    _write_json(path, doc.model_dump())


def append_assistant(
    plot_root: Path,
    project_id: str,
    scope: str,
    provider: str,
    msg_id: str,
    text: str,
    *,
    error: str | None = None,
    error_code: str | None = None,
    added_elsewhere: list[CanvasAddition] | None = None,
) -> None:
    """Append the assistant reply to the current project conversation."""
    _ensure_project(plot_root, project_id)
    path = _conversation_path(plot_root, project_id, scope)
    if not path.exists():
        return
    doc = ChatConversationDoc.model_validate(_read_json(path))
    _ensure_conversation_id(doc)
    now = _now()
    doc.provider = provider
    doc.updated = now
    doc.messages.append(
        ChatMessageRecord(
            id=msg_id,
            role="assistant",
            text=text,
            ts=now,
            scope=scope,
            error=error,
            error_code=error_code,
            added_elsewhere=added_elsewhere,
        )
    )
    _write_json(path, doc.model_dump())


def find_conversation_path_by_conversation_id(
    plot_root: Path,
    project_id: str,
    scope: str,
    conversation_id: str,
) -> Path | None:
    """Find a scope's current or ended file by its durable conversation id.

    The current file is checked first because it is the overwhelmingly common
    case. Invalid or legacy files are skipped so callers can preserve the old
    current-file fallback behavior.
    """
    chat_dir = _chat_dir(plot_root, project_id)
    current_path = _conversation_path(plot_root, project_id, scope)
    candidates = [current_path]
    if chat_dir.exists():
        candidates.extend(path for path in chat_dir.glob("*.json") if path != current_path)
    for path in candidates:
        if not path.exists():
            continue
        try:
            doc = ChatConversationDoc.model_validate(_read_json(path))
        except Exception:  # noqa: BLE001 — one bad chat file must not block lookup
            continue
        if doc.conversation_id == conversation_id:
            return path
    return None


def append_assistant_to_conversation(
    plot_root: Path,
    project_id: str,
    scope: str,
    provider: str,
    msg_id: str,
    text: str,
    conversation_id: str | None,
    *,
    error: str | None = None,
    error_code: str | None = None,
    added_elsewhere: list[CanvasAddition] | None = None,
) -> None:
    """Append to the file owning ``conversation_id``, including ended files.

    A missing id or an unmatched legacy file falls back to the current scope,
    preserving :func:`append_assistant`'s established no-op behavior when no
    current conversation exists.
    """
    _ensure_project(plot_root, project_id)
    path = (
        find_conversation_path_by_conversation_id(plot_root, project_id, scope, conversation_id)
        if conversation_id is not None
        else None
    )
    if path is None:
        append_assistant(
            plot_root,
            project_id,
            scope,
            provider,
            msg_id,
            text,
            error=error,
            error_code=error_code,
            added_elsewhere=added_elsewhere,
        )
        return
    doc = ChatConversationDoc.model_validate(_read_json(path))
    now = _now()
    doc.provider = provider
    doc.updated = now
    doc.messages.append(
        ChatMessageRecord(
            id=msg_id,
            role="assistant",
            text=text,
            ts=now,
            scope=scope,
            error=error,
            error_code=error_code,
            added_elsewhere=added_elsewhere,
        )
    )
    _write_json(path, doc.model_dump())


def read_conversation(plot_root: Path, project_id: str, scope: str) -> ChatConversationDoc:
    """Read the project transcript; ``scope`` validates the caller's turn scope."""
    path = _conversation_path(plot_root, project_id, scope)
    if path.exists():
        try:
            raw = _read_json(path)
            if raw.get("schema_version") == 2:
                return ChatConversationDoc.model_validate(raw)
        except ValueError:
            pass
    elif _has_v2_history(path.parent):
        raise FileNotFoundError(path)
    merged = synthesize(path.parent)
    if merged is None:
        raise FileNotFoundError(path)
    return ChatConversationDoc.model_validate(merged)


def _has_v2_history(chat_dir: Path) -> bool:
    for path in chat_dir.glob("project__*.json"):
        try:
            if _read_json(path).get("schema_version") == 2:
                return True
        except (OSError, ValueError):
            continue
    return False


def current_conversation_id(plot_root: Path, project_id: str, scope: str) -> str | None:
    """Return the current project's durable id without modifying legacy files."""
    try:
        doc = read_conversation(plot_root, project_id, scope)
    except FileNotFoundError:
        return None
    return doc.conversation_id


def read_conversation_by_id(
    plot_root: Path, project_id: str, conversation_id: str
) -> ChatConversationDoc:
    """Read a current or ended conversation by the opaque id from the list API."""
    path = _conversation_id_path(plot_root, project_id, conversation_id)
    raw = _read_json(path)
    converted = raw if raw.get("schema_version") == 2 else legacy_doc(raw)
    return ChatConversationDoc.model_validate(converted)


def archive_current_conversation(plot_root: Path, project_id: str, scope: str) -> str | None:
    """Move the current conversation aside and return its ended-conversation id.

    A missing current file or a current document with no messages is intentionally
    left untouched: merely opening a canvas does not create an ended conversation.
    """
    _ensure_project(plot_root, project_id)
    current_path = _conversation_path(plot_root, project_id, scope)
    if not current_path.exists():
        if _has_v2_history(current_path.parent) or not synthesize(current_path.parent):
            return None
        materialize(current_path.parent, _archive_path(current_path))
    elif _read_json(current_path).get("schema_version") != 2:
        materialize(current_path.parent, _archive_path(current_path))
    doc = read_conversation(plot_root, project_id, scope)
    if not doc.messages:
        return None
    archive_path = _archive_path(current_path)
    current_path.replace(archive_path)
    return archive_path.name


def reopen_conversation(
    plot_root: Path, project_id: str, conversation_id: str
) -> ChatConversationDoc:
    """Make one ended conversation current, archiving the displaced current one."""
    _ensure_project(plot_root, project_id)
    ended_path = _conversation_id_path(plot_root, project_id, conversation_id)
    raw = _read_json(ended_path)
    converted = raw if raw.get("schema_version") == 2 else legacy_doc(raw)
    doc = ChatConversationDoc.model_validate(converted)
    current_path = _conversation_path(plot_root, project_id, DEFAULT_CHAT_SCOPE)
    if ended_path == current_path:
        if raw.get("schema_version") == 2:
            raise ValueError("conversation is already current")
        original = ended_path.read_bytes()
        materialize(current_path.parent, _archive_path(current_path))
        ended_path = next(
            path
            for path in current_path.parent.glob("project__*.json")
            if path.read_bytes() == original
        )
    archive_current_conversation(plot_root, project_id, DEFAULT_CHAT_SCOPE)
    doc.conversation_id = uuid4().hex
    doc.scope = DEFAULT_CHAT_SCOPE
    _write_json(current_path, doc.model_dump())
    return doc


def read_recent_transcript(
    plot_root: Path,
    project_id: str,
    scope: str,
    max_chars: int = 12000,
    *,
    exclude_message_id: str | None = None,
) -> str:
    """Render bounded project history with each message's turn scope.

    The header, labels and text together fit ``max_chars``. Failed replies
    and ``exclude_message_id`` are omitted from the fresh provider's prompt.
    """
    try:
        doc = read_conversation(plot_root, project_id, scope)
    except FileNotFoundError:
        return ""
    if not doc.messages:
        return ""
    header = (
        "[Earlier in this project — continue from here; what is already "
        "agreed below is settled, do not re-ask it. Treat earlier messages as "
        "facts and decisions only; do not imitate the wording or style of earlier "
        "assistant replies]"
    )
    budget = max_chars - len(header) - 1
    if budget <= 0:
        return header[:max_chars]
    picked: list[str] = []
    total = 0
    for m in reversed(doc.messages):
        if m.id == exclude_message_id:
            continue
        if m.error is not None:
            continue
        line = f"[{m.scope}] {m.role}: {m.text.strip()}"
        remaining = budget - total - (1 if picked else 0)
        if len(line) > remaining and picked:
            break
        picked.append(line[:remaining] if len(line) > remaining else line)
        total += len(picked[-1]) + (1 if len(picked) > 1 else 0)
    if not picked:
        return ""
    picked.reverse()
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
            raw = _read_json(path)
            doc = ChatConversationDoc.model_validate(raw)
            current_name = "project.json"
            legacy = raw.get("schema_version", 1) != 2
        except Exception:  # noqa: BLE001 — a bad file must not break the list
            continue
        rows.append(
            {
                "id": path.name,
                "conversation_id": doc.conversation_id,
                "scope": doc.scope,
                "title": doc.title,
                "provider": doc.provider,
                "updated": doc.updated,
                "message_count": len(doc.messages),
                "ended": legacy or path.name != current_name,
                "legacy": legacy,
            }
        )
    rows.sort(key=lambda r: r["updated"], reverse=True)
    return rows
