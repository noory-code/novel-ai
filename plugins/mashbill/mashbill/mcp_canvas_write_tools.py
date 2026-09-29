"""Draft-aware implementations for MCP canvas write tools."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mashbill.folder_io import create_edge, read_canvas, sync_details_with_overview, write_canvas
from mashbill.mcp_draft_tools import ensure_draft, finish_canvas_write_draft, finish_write_draft
from mashbill.models import CanvasDoc, CanvasKind
from mashbill.references import set_node_references


def update_canvas_with_draft(
    plot_root: Path,
    project_id: str,
    validated: CanvasDoc,
    draft_id: str | None,
    chat_scope: str,
) -> dict[str, list[str]]:
    """Persist a whole canvas, reconcile details, and finish its draft."""
    if draft_id is not None:
        ensure_draft(plot_root, project_id, draft_id)
    service_id = validated.feature_ref if validated.canvas_kind == "feature" else None
    before = read_canvas(plot_root, project_id, validated.canvas_kind, service_id)
    saved = write_canvas(plot_root, project_id, validated)
    sync: dict[str, list[str]] = {"created": [], "archived": [], "skipped_archive": []}
    if validated.canvas_kind == "services":
        sync = sync_details_with_overview(plot_root, project_id)
    finish_canvas_write_draft(plot_root, project_id, draft_id, before, saved, chat_scope)
    return sync


def create_edge_with_draft(
    plot_root: Path,
    project_id: str,
    canvas_kind: CanvasKind,
    source_id: str,
    target_id: str,
    service_id: str | None,
    label: str,
    draft_id: str | None,
    chat_scope: str,
) -> dict[str, Any]:
    """Append an edge and confirm or record its draft."""
    if draft_id is not None:
        ensure_draft(plot_root, project_id, draft_id)
    canvas = read_canvas(plot_root, project_id, canvas_kind, service_id)
    labels = {str(node.id): node.label for node in canvas.nodes}
    out = create_edge(
        plot_root, project_id, canvas_kind, source_id, target_id, service_id, label
    )
    source_label = labels.get(source_id) or source_id
    target_label = labels.get(target_id) or target_id
    proposed_text = f"관계: {source_label} → {target_label}"
    written_label = str(out["edge"].get("label") or "")
    if written_label:
        proposed_text += f" ({written_label})"
    finish_write_draft(
        plot_root,
        project_id,
        draft_id,
        canvas_kind,
        proposed_text,
        "edge",
        [source_id, target_id],
        [source_id, target_id],
        chat_scope,
        service_id,
    )
    return out


def set_node_references_with_draft(
    plot_root: Path,
    project_id: str,
    canvas_kind: CanvasKind,
    node_id: str,
    refs: dict[str, list[str]],
    service_id: str | None,
    draft_id: str | None,
    chat_scope: str,
) -> dict[str, Any]:
    """Assign references and confirm or record their draft."""
    if draft_id is not None:
        ensure_draft(plot_root, project_id, draft_id)
    out = set_node_references(plot_root, project_id, canvas_kind, node_id, refs, service_id)
    proposed_text = "참조: " + " / ".join(
        f"{field} = {', '.join(ref_ids) if ref_ids else '없음'}"
        for field, ref_ids in refs.items()
    )
    finish_write_draft(
        plot_root,
        project_id,
        draft_id,
        canvas_kind,
        proposed_text,
        "references",
        [node_id],
        [node_id],
        chat_scope,
        service_id,
    )
    return out
