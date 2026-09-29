"""MCP-callable draft operations and draft-aware node-write helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mashbill.draft_store import read_draft
from mashbill.draft_store import record_applied_draft as persist_applied_draft
from mashbill.draft_store import record_draft as persist_draft
from mashbill.draft_store import resolve_draft as persist_resolution
from mashbill.models_canvas import CanvasKind
from mashbill.models_draft import DraftDoc, ResolvedDraftStatus
from mashbill.workspace import resolve_plot_root

AUTO_DRAFT_RATIONALE = "Coach applied the change directly without recording a draft."


def _draft_result(draft: DraftDoc) -> dict[str, Any]:
    return {"draft_id": draft.id, **draft.model_dump()}


def record_draft(
    project_path: str,
    project_id: str,
    canvas_kind: CanvasKind,
    proposed_text: str,
    rationale: str,
    chat_scope: str,
    target_node_ids: list[str] | None = None,
    proposed_kind: str | None = None,
    service_id: str | None = None,
) -> dict[str, Any]:
    """Keep a concrete proposal shown to the person, separately from chat.

    Call this whenever presenting text for a node or proposing a new node.
    ``rationale`` is one line explaining why; ``chat_scope`` comes from the
    [Write target]. ``target_node_ids`` may be empty for a new concept.
    """
    plot_root = resolve_plot_root(project_path)
    draft = persist_draft(
        plot_root,
        project_id,
        canvas_kind,
        proposed_text,
        rationale,
        chat_scope,
        target_node_ids,
        proposed_kind,
        service_id,
    )
    return _draft_result(draft)


def resolve_draft(
    project_path: str,
    project_id: str,
    draft_id: str,
    status: ResolvedDraftStatus,
    node_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Mark a proposal confirmed, edited, or rejected without deleting it.

    For ``confirmed`` or ``edited``, pass the ids of nodes that received the
    proposal. A later resolution is allowed and refreshes ``updated``.
    """
    plot_root = resolve_plot_root(project_path)
    return _draft_result(persist_resolution(plot_root, project_id, draft_id, status, node_ids))


def ensure_draft(plot_root: Path, project_id: str, draft_id: str) -> None:
    """Fail before a node write when the supplied draft does not exist."""
    read_draft(plot_root, project_id, draft_id)


def confirm_draft(plot_root: Path, project_id: str, draft_id: str, node_id: str) -> None:
    """Link a successful node write back to its draft."""
    persist_resolution(plot_root, project_id, draft_id, "confirmed", [node_id])


def finish_node_write_draft(
    plot_root: Path,
    project_id: str,
    draft_id: str | None,
    canvas_kind: CanvasKind,
    fields: dict[str, Any] | None,
    write_result: dict[str, Any],
    chat_scope: str,
    service_id: str | None,
) -> None:
    """Confirm the supplied draft or create the fallback for a successful write."""
    if draft_id is not None:
        confirm_draft(plot_root, project_id, draft_id, str(write_result["node"]["id"]))
        return
    record_applied_draft(
        plot_root, project_id, canvas_kind, fields, write_result, chat_scope, service_id
    )


def record_applied_draft(
    plot_root: Path,
    project_id: str,
    canvas_kind: CanvasKind,
    fields: dict[str, Any] | None,
    write_result: dict[str, Any],
    chat_scope: str,
    service_id: str | None = None,
) -> None:
    """Record one successful MCP node write that arrived without a draft id."""
    node = write_result["node"]
    rejected = set(write_result["rejected_fields"])
    written_fields = [name for name in (fields or {}) if name not in rejected]
    if not written_fields:
        written_fields = ["label"]
    proposed_text = "\n".join(
        f"{name}: {_display_value(node.get(name))}" for name in written_fields
    )
    persist_applied_draft(
        plot_root,
        project_id,
        canvas_kind,
        proposed_text,
        AUTO_DRAFT_RATIONALE,
        chat_scope,
        str(node["id"]),
        str(node["kind"]),
        service_id,
    )


def _display_value(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True)
