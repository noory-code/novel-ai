"""Append-preserving storage for coach-proposed design drafts.

Each draft owns one JSON file under ``drafts/``. New records therefore never
rewrite a shared list and cannot erase a concurrent record; writes use the same
temporary-file replacement helper as chat and canvas persistence.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from mashbill.models_canvas import CanvasKind
from mashbill.models_draft import DraftDoc, DraftOrigin, DraftStatus, ResolvedDraftStatus
from mashbill.storage import _ensure_project, _project_dir, _read_json, _write_json

_DRAFT_DIRNAME = "drafts"


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _draft_dir(plot_root: Path, project_id: str) -> Path:
    return _project_dir(plot_root, project_id) / _DRAFT_DIRNAME


def _draft_path(plot_root: Path, project_id: str, draft_id: str) -> Path:
    if not draft_id or not draft_id.replace("-", "").replace("_", "").isalnum():
        raise ValueError(f"unsafe draft id: {draft_id!r}")
    return _draft_dir(plot_root, project_id) / f"{draft_id}.json"


def record_draft(
    plot_root: Path,
    project_id: str,
    canvas_kind: CanvasKind,
    proposed_text: str,
    rationale: str,
    chat_scope: str,
    target_node_ids: list[str] | None = None,
    proposed_kind: str | None = None,
    service_id: str | None = None,
) -> DraftDoc:
    """Persist a newly shown proposal as an immutable-identity draft document."""
    return _record_new_draft(
        plot_root,
        project_id,
        canvas_kind,
        proposed_text,
        rationale,
        chat_scope,
        target_node_ids or [],
        proposed_kind,
        service_id,
        status="proposed",
        origin="recorded",
        resolved_node_ids=[],
    )


def record_applied_draft(
    plot_root: Path,
    project_id: str,
    canvas_kind: CanvasKind,
    proposed_text: str,
    rationale: str,
    chat_scope: str,
    node_id: str,
    proposed_kind: str,
    service_id: str | None = None,
) -> DraftDoc:
    """Persist the confirmed fallback record for an MCP node write."""
    return _record_new_draft(
        plot_root,
        project_id,
        canvas_kind,
        proposed_text,
        rationale,
        chat_scope,
        [node_id],
        proposed_kind,
        service_id,
        status="confirmed",
        origin="auto",
        resolved_node_ids=[node_id],
    )


def _record_new_draft(
    plot_root: Path,
    project_id: str,
    canvas_kind: CanvasKind,
    proposed_text: str,
    rationale: str,
    chat_scope: str,
    target_node_ids: list[str],
    proposed_kind: str | None,
    service_id: str | None,
    *,
    status: DraftStatus,
    origin: DraftOrigin,
    resolved_node_ids: list[str],
) -> DraftDoc:
    """Write one new draft file with its initial resolution state."""
    _ensure_project(plot_root, project_id)
    now = _now()
    draft = DraftDoc(
        id=f"draft_{uuid4().hex[:12]}",
        created=now,
        updated=now,
        canvas_kind=canvas_kind,
        service_id=service_id,
        target_node_ids=list(target_node_ids),
        proposed_kind=proposed_kind,
        proposed_text=proposed_text,
        rationale=rationale,
        status=status,
        origin=origin,
        chat_scope=chat_scope,
        resolved_node_ids=list(resolved_node_ids),
    )
    _write_json(_draft_path(plot_root, project_id, draft.id), draft.model_dump())
    return draft


def read_draft(plot_root: Path, project_id: str, draft_id: str) -> DraftDoc:
    """Read one draft, raising ``FileNotFoundError`` when its id is unknown."""
    _ensure_project(plot_root, project_id)
    path = _draft_path(plot_root, project_id, draft_id)
    try:
        return DraftDoc.model_validate(_read_json(path))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"draft not found: {draft_id}") from exc


def resolve_draft(
    plot_root: Path,
    project_id: str,
    draft_id: str,
    status: ResolvedDraftStatus,
    node_ids: list[str] | None = None,
) -> DraftDoc:
    """Change a draft's resolution without deleting its proposal record.

    Resolved node ids accumulate in first-seen order. Later status changes keep
    those links, so rejecting a once-applied draft does not erase its history.
    """
    draft = read_draft(plot_root, project_id, draft_id)
    resolved = list(draft.resolved_node_ids)
    if status in ("confirmed", "edited"):
        for node_id in node_ids or []:
            if node_id not in resolved:
                resolved.append(node_id)
    updated = draft.model_copy(
        update={"status": status, "updated": _now(), "resolved_node_ids": resolved}
    )
    _write_json(_draft_path(plot_root, project_id, draft_id), updated.model_dump())
    return updated


def list_drafts(
    plot_root: Path,
    project_id: str,
    *,
    status: DraftStatus | None = None,
    canvas_kind: CanvasKind | None = None,
    node_id: str | None = None,
) -> list[DraftDoc]:
    """List matching drafts newest-updated first."""
    _ensure_project(plot_root, project_id)
    directory = _draft_dir(plot_root, project_id)
    if not directory.exists():
        return []
    drafts = [DraftDoc.model_validate(_read_json(path)) for path in directory.glob("*.json")]
    if status is not None:
        drafts = [draft for draft in drafts if draft.status == status]
    if canvas_kind is not None:
        drafts = [draft for draft in drafts if draft.canvas_kind == canvas_kind]
    if node_id is not None:
        drafts = [
            draft
            for draft in drafts
            if node_id in draft.target_node_ids or node_id in draft.resolved_node_ids
        ]
    drafts.sort(key=lambda draft: draft.updated, reverse=True)
    return drafts
