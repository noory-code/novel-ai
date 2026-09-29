"""MCP-callable draft operations and draft-aware node-write helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mashbill.draft_store import read_draft
from mashbill.draft_store import record_draft as persist_draft
from mashbill.draft_store import resolve_draft as persist_resolution
from mashbill.models_canvas import CanvasKind
from mashbill.models_draft import DraftDoc, ResolvedDraftStatus
from mashbill.workspace import resolve_plot_root


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
