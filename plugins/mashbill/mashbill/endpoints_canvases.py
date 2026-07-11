"""Canvas GET/PUT endpoints (D-2026-06-11-B).

Extracted from the api_endpoints.py god module. Owns the per-canvas
serialisation enrichments (MD parse warnings + per-node dirty signal)
that ride the response envelope without polluting the persisted model.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse

from mashbill.endpoints_common import _ApiError, _error, _parse_canvas_kind, _require_plot_root
from mashbill.entity_refs import entity_usage
from mashbill.folder_io import read_canvas, sync_details_with_overview, write_canvas
from mashbill.masters import create_master
from mashbill.models import CanvasDoc


async def entity_usage_endpoint(request: Request) -> JSONResponse:
    """GET — the read-only "어디서 쓰이나" back-reference for an entity
    (D-2026-06-20-Q): the features whose ``step.ref_entity_ids`` reference it.
    Scans all feature canvases server-side (the viewer can't — it loads
    canvases lazily)."""
    try:
        plot_root = _require_plot_root(request)
    except _ApiError as exc:
        return exc.response
    project_id = request.path_params["project_id"]
    entity_id = request.path_params["entity_id"]
    try:
        usages = entity_usage(plot_root, project_id, entity_id)
    except FileNotFoundError as exc:
        return _error(str(exc), status=404)
    return JSONResponse({"entity_id": entity_id, "usages": usages})


async def master_create_endpoint(request: Request) -> JSONResponse:
    """POST — create a lightweight upstream master from a downstream reference
    (D-2026-06-19-C, pick-OR-create). Body ``{kind, label}`` with ``kind`` in
    ``actor`` / ``core_value`` / ``identity``; the engine creates the master on
    its home canvas (Actors / Foundation) and returns its id so the caller can
    add the chip. Encapsulates the home-canvas + positioning logic so the viewer
    never has to write across the canvas boundary itself."""
    try:
        plot_root = _require_plot_root(request)
    except _ApiError as exc:
        return exc.response
    project_id = request.path_params["project_id"]
    try:
        body: dict[str, Any] = await request.json()
    except json.JSONDecodeError:
        return _error("invalid JSON body")
    kind = body.get("kind")
    label = body.get("label")
    if not isinstance(kind, str) or not isinstance(label, str):
        return _error("kind and label are required strings")
    try:
        new_id = create_master(plot_root, project_id, kind, label)
    except ValueError as exc:
        return _error(str(exc))
    except FileNotFoundError as exc:
        return _error(str(exc), status=404)
    return JSONResponse({"id": new_id, "kind": kind}, status_code=201)


async def canvas_get_endpoint(request: Request) -> JSONResponse:
    try:
        plot_root = _require_plot_root(request)
    except _ApiError as exc:
        return exc.response
    project_id = request.path_params["project_id"]
    kind_raw = request.path_params["kind"]
    canvas_kind = _parse_canvas_kind(kind_raw)
    if canvas_kind is None:
        return _error(f"unknown canvas kind: {kind_raw!r}")
    service_id = request.query_params.get("service_id")
    if canvas_kind == "feature" and not service_id:
        return _error("service_id query param required for feature")
    try:
        canvas = read_canvas(plot_root, project_id, canvas_kind, service_id)
    except FileNotFoundError as exc:
        return _error(str(exc), status=404)
    raw = canvas.model_dump(by_alias=True)
    # v0.13 Phase 7 — enrich foundation nodes with MD-parse warnings so
    # the Inspector can surface a yellow ⚠ + actionable hint. Not part of
    # the model (stays clean on write); pure response decoration.
    from mashbill.folder_io import collect_foundation_md_warnings

    warnings_by_node = collect_foundation_md_warnings(plot_root, project_id, canvas)
    if warnings_by_node:
        for n in raw.get("nodes", []):
            warns = warnings_by_node.get(n.get("id"))
            if warns:
                n["_md_warnings"] = warns
    return JSONResponse(raw)


async def canvas_put_endpoint(request: Request) -> JSONResponse:
    try:
        plot_root = _require_plot_root(request)
    except _ApiError as exc:
        return exc.response
    project_id = request.path_params["project_id"]
    kind_raw = request.path_params["kind"]
    canvas_kind = _parse_canvas_kind(kind_raw)
    if canvas_kind is None:
        return _error(f"unknown canvas kind: {kind_raw!r}")
    try:
        body: dict[str, Any] = await request.json()
    except json.JSONDecodeError:
        return _error("invalid JSON body")
    body["canvas_kind"] = canvas_kind
    try:
        canvas = CanvasDoc.model_validate(body)
    except ValidationError as exc:
        return _error(str(exc), status=422)
    try:
        write_canvas(plot_root, project_id, canvas)
    except FileNotFoundError as exc:
        return _error(str(exc), status=404)
    sync: dict[str, list[str]] = {"created": [], "archived": [], "skipped_archive": []}
    if canvas_kind == "services":
        sync = sync_details_with_overview(plot_root, project_id)
    raw = canvas.model_dump(by_alias=True)
    return JSONResponse({"canvas": raw, "sync": sync})
