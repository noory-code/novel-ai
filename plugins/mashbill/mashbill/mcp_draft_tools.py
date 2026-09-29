"""MCP-callable draft operations and draft-aware node-write helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mashbill.blueprint_content import _canvas_design_content
from mashbill.chat_scope_env import effective_chat_scope
from mashbill.draft_store import read_draft
from mashbill.draft_store import record_applied_draft as persist_applied_draft
from mashbill.draft_store import record_draft as persist_draft
from mashbill.draft_store import resolve_draft as persist_resolution
from mashbill.models_canvas import CanvasDoc, CanvasKind
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
    chat_scope: str = "",
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
        effective_chat_scope(chat_scope),
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


def draft_matches_write(
    plot_root: Path,
    project_id: str,
    draft_id: str,
    canvas_kind: CanvasKind,
    touched_node_ids: list[str],
    service_id: str | None = None,
) -> bool:
    """Return whether a supplied draft describes the successful write."""
    draft = read_draft(plot_root, project_id, draft_id)
    if draft.status == "rejected" or draft.canvas_kind != canvas_kind:
        return False
    if canvas_kind == "feature" and draft.service_id != service_id:
        return False
    if not draft.target_node_ids:
        return True
    return bool(set(draft.target_node_ids).intersection(touched_node_ids))


def confirm_draft(plot_root: Path, project_id: str, draft_id: str, node_ids: list[str]) -> None:
    """Link a successful write back to its draft."""
    persist_resolution(plot_root, project_id, draft_id, "confirmed", node_ids)


def finish_write_draft(
    plot_root: Path,
    project_id: str,
    draft_id: str | None,
    canvas_kind: CanvasKind,
    proposed_text: str,
    proposed_kind: str | None,
    target_node_ids: list[str],
    resolved_node_ids: list[str],
    chat_scope: str,
    service_id: str | None = None,
) -> str | None:
    """Confirm the supplied draft or record one successful MCP write."""
    if draft_id is not None and draft_matches_write(
        plot_root,
        project_id,
        draft_id,
        canvas_kind,
        target_node_ids,
        service_id,
    ):
        confirm_draft(plot_root, project_id, draft_id, resolved_node_ids)
        return None
    persist_applied_draft(
        plot_root,
        project_id,
        canvas_kind,
        proposed_text,
        AUTO_DRAFT_RATIONALE,
        effective_chat_scope(chat_scope),
        target_node_ids,
        proposed_kind,
        service_id,
        resolved_node_ids,
    )
    if draft_id is None:
        return None
    return _draft_mismatch_warning(draft_id)


def finish_node_write_draft(
    plot_root: Path,
    project_id: str,
    draft_id: str | None,
    canvas_kind: CanvasKind,
    fields: dict[str, Any] | None,
    write_result: dict[str, Any],
    chat_scope: str,
    service_id: str | None,
    additional_touched_node_ids: list[str] | None = None,
) -> str | None:
    """Confirm the supplied draft or create the fallback for a successful write."""
    node_id = str(write_result["node"]["id"])
    touched_node_ids = [node_id, *(additional_touched_node_ids or [])]
    if draft_id is not None and draft_matches_write(
        plot_root,
        project_id,
        draft_id,
        canvas_kind,
        touched_node_ids,
        service_id,
    ):
        confirm_draft(plot_root, project_id, draft_id, [node_id])
        return None
    record_applied_draft(
        plot_root, project_id, canvas_kind, fields, write_result, chat_scope, service_id
    )
    if draft_id is None:
        return None
    return _draft_mismatch_warning(draft_id)


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
        effective_chat_scope(chat_scope),
        [str(node["id"])],
        str(node["kind"]),
        service_id,
        [str(node["id"])],
    )


def finish_canvas_write_draft(
    plot_root: Path,
    project_id: str,
    draft_id: str | None,
    before: CanvasDoc,
    after: CanvasDoc,
    chat_scope: str,
) -> str | None:
    """Confirm or record a whole-canvas write from its normalized content diff."""
    before_content = _canvas_design_content(before.model_dump(by_alias=True))
    after_content = _canvas_design_content(after.model_dump(by_alias=True))
    if before_content == after_content:
        service_id = after.feature_ref if after.canvas_kind == "feature" else None
        if draft_id is not None and draft_matches_write(
            plot_root, project_id, draft_id, after.canvas_kind, [], service_id
        ):
            confirm_draft(plot_root, project_id, draft_id, [])
        return None

    before_nodes = before_content["nodes"]
    after_nodes = after_content["nodes"]
    added = [node_id for node_id in after_nodes if node_id not in before_nodes]
    changed = [
        node_id
        for node_id in after_nodes
        if node_id in before_nodes and after_nodes[node_id] != before_nodes[node_id]
    ]
    removed = [node_id for node_id in before_nodes if node_id not in after_nodes]

    def names(node_ids: list[str], nodes: dict[str, dict[str, Any]]) -> str:
        labels = (str(nodes[node_id].get("label") or node_id) for node_id in node_ids)
        return ", ".join(labels) or "없음"

    proposed_text = (
        f"더함: {names(added, after_nodes)} / "
        f"바꿈: {names(changed, after_nodes)} / "
        f"뺌: {names(removed, before_nodes)}"
    )
    before_edges = before_content["edges"]
    after_edges = after_content["edges"]
    edges_added = [edge_id for edge_id in after_edges if edge_id not in before_edges]
    edges_changed = [
        edge_id
        for edge_id in after_edges
        if edge_id in before_edges and after_edges[edge_id] != before_edges[edge_id]
    ]
    edges_removed = [edge_id for edge_id in before_edges if edge_id not in after_edges]
    if edges_added or edges_changed or edges_removed:
        proposed_text += (
            f"\n선: 더함 {len(edges_added)} / 바꿈 {len(edges_changed)} / 뺌 {len(edges_removed)}"
        )

    return finish_write_draft(
        plot_root,
        project_id,
        draft_id,
        after.canvas_kind,
        proposed_text,
        "canvas",
        [*added, *changed, *removed],
        [*added, *changed],
        chat_scope,
        after.feature_ref if after.canvas_kind == "feature" else None,
    )


def _draft_mismatch_warning(draft_id: str) -> str:
    return f"draft {draft_id} does not match this write; recorded an auto draft instead"


def _display_value(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True)
