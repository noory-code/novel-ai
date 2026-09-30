"""Draft-aware implementations for MCP canvas write tools."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mashbill.folder_io import (
    create_edge,
    create_node,
    read_canvas,
    sync_details_with_overview,
    update_node,
    write_canvas,
)
from mashbill.mcp_draft_tools import (
    ensure_draft,
    finish_canvas_write_draft,
    finish_node_write_draft,
    finish_write_draft,
)
from mashbill.mcp_write_rollback import with_draft_or_rollback
from mashbill.models import CanvasDoc, CanvasKind
from mashbill.references import set_node_references


def update_canvas_with_draft(
    plot_root: Path,
    project_id: str,
    validated: CanvasDoc,
    draft_id: str | None,
    chat_scope: str,
) -> tuple[dict[str, list[str]], str | None]:
    """Persist a whole canvas, reconcile details, and finish its draft."""
    if draft_id is not None:
        ensure_draft(plot_root, project_id, draft_id)
    service_id = validated.feature_ref if validated.canvas_kind == "feature" else None
    before = read_canvas(plot_root, project_id, validated.canvas_kind, service_id)

    def write_and_sync() -> tuple[CanvasDoc, dict[str, list[str]]]:
        saved = write_canvas(plot_root, project_id, validated)
        sync: dict[str, list[str]] = {
            "created": [],
            "restored": [],
            "archived": [],
            "skipped_archive": [],
        }
        if validated.canvas_kind == "services":
            sync = sync_details_with_overview(plot_root, project_id)
        return saved, sync

    def rollback() -> None:
        write_canvas(plot_root, project_id, before)
        if validated.canvas_kind == "services":
            sync_details_with_overview(plot_root, project_id)

    (saved, sync), warning = with_draft_or_rollback(
        write_and_sync,
        lambda written: finish_canvas_write_draft(
            plot_root, project_id, draft_id, before, written[0], chat_scope
        ),
        rollback,
    )
    return sync, warning


def update_node_with_draft(
    plot_root: Path,
    project_id: str,
    canvas_kind: CanvasKind,
    node_id: str,
    fields: dict[str, Any],
    service_id: str | None,
    draft_id: str | None,
    chat_scope: str,
) -> dict[str, Any]:
    """Patch one node and finish its draft only when design content changed."""
    if draft_id is not None:
        ensure_draft(plot_root, project_id, draft_id)
    before = read_canvas(plot_root, project_id, canvas_kind, service_id)
    before_node = next((node for node in before.nodes if node.id == node_id), None)
    out, warning = with_draft_or_rollback(
        lambda: update_node(plot_root, project_id, canvas_kind, node_id, fields, service_id),
        lambda written: finish_node_write_draft(
            plot_root,
            project_id,
            draft_id,
            canvas_kind,
            fields,
            written,
            chat_scope,
            service_id,
            before_node=before_node.model_dump(by_alias=True) if before_node is not None else None,
        ),
        lambda: write_canvas(plot_root, project_id, before),
    )
    if warning is not None:
        out["draft_warning"] = warning
    return out


def create_node_with_draft(
    plot_root: Path,
    project_id: str,
    canvas_kind: CanvasKind,
    kind: str,
    fields: dict[str, Any] | None,
    service_id: str | None,
    near: str | None,
    draft_id: str | None,
    chat_scope: str,
) -> dict[str, Any]:
    """Append one node and finish its draft, rolling back both canvases on failure."""
    if draft_id is not None:
        ensure_draft(plot_root, project_id, draft_id)
    before = read_canvas(plot_root, project_id, canvas_kind, service_id)
    sync_details = canvas_kind == "services" and kind == "feature"

    def write_and_sync() -> dict[str, Any]:
        out = create_node(plot_root, project_id, canvas_kind, kind, fields, service_id, near)
        if sync_details:
            # A feature is a drill target, so its detail canvas must exist as soon as
            # the overview node does. Rollback runs this reconciliation again below.
            sync_details_with_overview(plot_root, project_id)
        return out

    def rollback() -> None:
        write_canvas(plot_root, project_id, before)
        if sync_details:
            sync_details_with_overview(plot_root, project_id)

    out, warning = with_draft_or_rollback(
        write_and_sync,
        lambda written: finish_node_write_draft(
            plot_root,
            project_id,
            draft_id,
            canvas_kind,
            fields,
            written,
            chat_scope,
            service_id,
            [near] if near is not None else None,
        ),
        rollback,
    )
    if warning is not None:
        out["draft_warning"] = warning
    return out


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
    before = read_canvas(plot_root, project_id, canvas_kind, service_id)
    labels = {str(node.id): node.label for node in before.nodes}
    source_label = labels.get(source_id) or source_id
    target_label = labels.get(target_id) or target_id
    proposed_text = f"관계: {source_label} → {target_label}"

    def record_draft(out: dict[str, Any]) -> str | None:
        written_text = proposed_text
        written_label = str(out["edge"].get("label") or "")
        if written_label:
            written_text += f" ({written_label})"
        return finish_write_draft(
            plot_root,
            project_id,
            draft_id,
            canvas_kind,
            written_text,
            "edge",
            [source_id, target_id],
            [source_id, target_id],
            chat_scope,
            service_id,
        )

    out, warning = with_draft_or_rollback(
        lambda: create_edge(
            plot_root, project_id, canvas_kind, source_id, target_id, service_id, label
        ),
        record_draft,
        lambda: write_canvas(plot_root, project_id, before),
    )
    if warning is not None:
        out["draft_warning"] = warning
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
    before = read_canvas(plot_root, project_id, canvas_kind, service_id)
    before_node = next((node for node in before.nodes if node.id == node_id), None)
    proposed_text = "참조: " + " / ".join(
        f"{field} = {', '.join(ref_ids) if ref_ids else '없음'}" for field, ref_ids in refs.items()
    )
    out, warning = with_draft_or_rollback(
        lambda: set_node_references(plot_root, project_id, canvas_kind, node_id, refs, service_id),
        lambda written: finish_write_draft(
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
            design_content_changed=before_node is None
            or any(
                before_node.model_dump().get(field) != written["node"].get(field) for field in refs
            ),
        ),
        lambda: write_canvas(plot_root, project_id, before),
    )
    if warning is not None:
        out["draft_warning"] = warning
    return out
