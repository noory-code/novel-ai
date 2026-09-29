"""Read-only HTTP surface for durable coach drafts."""

from __future__ import annotations

from typing import cast

from starlette.requests import Request
from starlette.responses import JSONResponse

from mashbill.draft_store import list_drafts
from mashbill.endpoints_common import _ApiError, _error, _parse_canvas_kind, _require_plot_root
from mashbill.models_draft import DraftCanvasKind, DraftStatus

_DRAFT_STATUSES: frozenset[str] = frozenset({"proposed", "confirmed", "edited", "rejected"})


async def drafts_list_endpoint(request: Request) -> JSONResponse:
    """``GET /api/projects/{project_id}/drafts`` with optional filters."""
    try:
        plot_root = _require_plot_root(request, create=False)
    except _ApiError as exc:
        return exc.response
    raw_status = request.query_params.get("status")
    if raw_status is not None and raw_status not in _DRAFT_STATUSES:
        return _error(f"unknown draft status: {raw_status!r}")
    raw_canvas_kind = request.query_params.get("canvas_kind")
    canvas_kind: DraftCanvasKind | None = None
    if raw_canvas_kind is not None:
        canvas_kind = (
            "project" if raw_canvas_kind == "project" else _parse_canvas_kind(raw_canvas_kind)
        )
        if canvas_kind is None:
            return _error(f"unknown canvas kind: {raw_canvas_kind!r}")
    try:
        drafts = list_drafts(
            plot_root,
            request.path_params["project_id"],
            status=cast(DraftStatus | None, raw_status),
            canvas_kind=canvas_kind,
            node_id=request.query_params.get("node_id"),
        )
    except FileNotFoundError as exc:
        return _error(str(exc), status=404)
    return JSONResponse({"drafts": [draft.model_dump() for draft in drafts]})
