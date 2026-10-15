"""Read-only legacy chat conversion and first-send materialization."""

from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from mashbill.storage import _read_json, _write_json


def _timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)


def legacy_doc(raw: dict[str, Any]) -> dict[str, Any]:
    """Return a v2 copy without changing the source or its conversation ID."""
    scope = raw["scope"]
    return {
        **raw,
        "schema_version": 2,
        "scope": "project",
        "messages": [
            {**message, "scope": message.get("scope", scope)} for message in raw["messages"]
        ],
    }


def synthesize(chat_dir: Path) -> dict[str, Any] | None:
    """Merge valid v1 current files in stable timestamp/file/index order."""
    from mashbill.chat_store import ChatConversationDoc

    entries: list[tuple[datetime, str, int, dict[str, Any]]] = []
    docs: list[dict[str, Any]] = []
    for path in sorted(chat_dir.glob("*.json")):
        try:
            raw = _read_json(path)
            scope = raw["scope"]
            if raw.get("schema_version", 1) != 1 or path.name != scope.replace(":", "__") + ".json":
                continue
            ChatConversationDoc.model_validate(raw)
            _timestamp(raw["created"])
            _timestamp(raw["updated"])
            for index, message in enumerate(raw["messages"]):
                entries.append(
                    (_timestamp(message["ts"]), path.name, index, {**message, "scope": scope})
                )
            docs.append(raw)
        except Exception:  # noqa: BLE001 — one corrupt legacy file must not block the merge
            continue
    if not docs:
        return None
    entries.sort(key=lambda item: item[:3])
    seen: set[str] = set()
    messages: list[dict[str, Any]] = []
    for _, filename, index, message in entries:
        original = message["id"]
        candidate = original
        if candidate in seen:
            candidate = f"{original}__legacy_{uuid5(NAMESPACE_URL, f'{filename}:{index}').hex[:12]}"
        seen.add(candidate)
        messages.append({**message, "id": candidate})
    first = min(docs, key=lambda doc: _timestamp(doc["created"]))
    last = max(docs, key=lambda doc: _timestamp(doc["updated"]))
    return {
        "schema_version": 2,
        "conversation_id": uuid5(NAMESPACE_URL, str(chat_dir.resolve())).hex,
        "scope": "project",
        "provider": last.get("provider", ""),
        "title": first.get("title", "")
        or next((m["text"][:60] for m in messages if m["role"] == "user"), ""),
        "created": first["created"],
        "updated": last["updated"],
        "messages": messages,
    }


def materialize(chat_dir: Path, archive_path: Path) -> dict[str, Any] | None:
    """Copy old project current before the atomic v2 write; retry safely."""
    current = chat_dir / "project.json"
    if current.exists():
        try:
            raw = _read_json(current)
            if raw.get("schema_version") == 2:
                return raw
        except ValueError:
            pass
    merged = synthesize(chat_dir)
    if current.exists() and not any(
        path.read_bytes() == current.read_bytes() for path in chat_dir.glob("project__*.json")
    ):
        shutil.copy2(current, archive_path)
    if merged is None:
        return None
    _write_json(current, merged)
    return merged
