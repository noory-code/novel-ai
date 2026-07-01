"""Project + workspace-discovery endpoints (D-2026-06-11-B).

Extracted from the api_endpoints.py god module. Covers project CRUD,
the anchor PATCH endpoint, and the workspace discovery + dir-tree picker
used by the new-project UI.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from mashbill.endpoints_common import (
    _ApiError,
    _error,
    _require_plot_root,
    _require_workspace_root,
)
from mashbill.file_io import UnsafePathError
from mashbill.folder_io import (
    create_project,
    delete_project,
    list_feature_details,
    read_project,
    rename_project,
    write_project,
)
from mashbill.git_store import init_workspace_repo, list_tags
from mashbill.migrate import migrate_v01_to_v02
from mashbill.models import DirTreeResponse, DiscoveredProject, WorkspaceDiscoveryResponse
from mashbill.workspace import (
    build_dir_tree,
    create_workspace_dir,
    discover_projects,
    enumerate_projects,
    resolve_plot_root,
    workspace_root_from_plot_root,
)


async def projects_list_endpoint(request: Request) -> JSONResponse:
    try:
        plot_root = _require_plot_root(request)
    except _ApiError as exc:
        return exc.response
    # Silently migrate any leftover v0.1 files in the (now-legacy)
    # ``sketches/`` root. Only runs if that directory still exists.
    migrated = migrate_v01_to_v02(plot_root)
    projects = [p.model_dump() for p in enumerate_projects(plot_root)]
    return JSONResponse({"projects": projects, "migrated": migrated})


async def workspace_discover_endpoint(request: Request) -> JSONResponse:
    """Recursively discover every Novel project anywhere under the workspace
    root, each with its directory relative to the root (v0.32.0)."""
    try:
        root = _require_workspace_root(request)
    except _ApiError as exc:
        return exc.response
    # Back-compat: migrate the root-level ``.plot`` only (same as the legacy
    # list endpoint); nested projects are already v0.2+.
    migrated = migrate_v01_to_v02(resolve_plot_root(str(root)))
    payload = WorkspaceDiscoveryResponse(
        projects=[DiscoveredProject(project=p, dir=d) for p, d in discover_projects(root)],
        migrated=migrated,
    )
    return JSONResponse(payload.model_dump())


async def dir_tree_endpoint(request: Request) -> JSONResponse:
    """Return the nested directory tree (with ``has_plot`` flags) under the
    workspace root, for the new-project picker (v0.32.0)."""
    try:
        root = _require_workspace_root(request)
    except _ApiError as exc:
        return exc.response
    return JSONResponse(DirTreeResponse(root=build_dir_tree(root)).model_dump())


async def dir_create_endpoint(request: Request) -> JSONResponse:
    """Create a new directory under the workspace root (v0.37.0,
    D-2026-05-31-AC) — backs the picker's "new folder" affordance. Body:
    ``{"rel": "banana"}`` (POSIX-relative, path-safe). Returns ``{"rel": ...}``."""
    try:
        root = _require_workspace_root(request)
    except _ApiError as exc:
        return exc.response
    try:
        body: dict[str, Any] = await request.json()
    except json.JSONDecodeError:
        return _error("invalid JSON body")
    rel = body.get("rel")
    if not rel or not isinstance(rel, str):
        return _error("'rel' is required and must be a string")
    try:
        created = create_workspace_dir(root, rel)
    except UnsafePathError as exc:
        return _error(str(exc), status=400)
    return JSONResponse({"rel": created}, status_code=201)


async def project_post_endpoint(request: Request) -> JSONResponse:
    try:
        plot_root = _require_plot_root(request)
    except _ApiError as exc:
        return exc.response
    try:
        body: dict[str, Any] = await request.json()
    except json.JSONDecodeError:
        return _error("invalid JSON body")
    project_id = body.get("id")
    name = body.get("name") or ""
    if not project_id or not isinstance(project_id, str):
        return _error("'id' is required and must be a string")
    try:
        proj = create_project(plot_root, project_id, name)
    except FileExistsError as exc:
        return _error(str(exc), status=409)
    except ValidationError as exc:
        return _error(str(exc), status=422)
    return JSONResponse(proj.model_dump(), status_code=201)


async def project_get_endpoint(request: Request) -> JSONResponse:
    try:
        plot_root = _require_plot_root(request)
    except _ApiError as exc:
        return exc.response
    project_id = request.path_params["project_id"]
    try:
        proj = read_project(plot_root, project_id)
    except FileNotFoundError as exc:
        return _error(str(exc), status=404)
    details = list_feature_details(plot_root, project_id)
    tags = list_tags(workspace_root_from_plot_root(plot_root))
    return JSONResponse(
        {
            **proj.model_dump(),
            "feature_details": details,
            "tags": tags,
        }
    )


async def project_patch_endpoint(request: Request) -> JSONResponse:
    try:
        plot_root = _require_plot_root(request)
    except _ApiError as exc:
        return exc.response
    project_id = request.path_params["project_id"]
    try:
        body: dict[str, Any] = await request.json()
    except json.JSONDecodeError:
        return _error("invalid JSON body")
    name = body.get("name")
    if not isinstance(name, str) or not name.strip():
        return _error("'name' is required and must be a non-empty string")
    try:
        renamed = rename_project(plot_root, project_id, name)
    except FileNotFoundError as exc:
        return _error(str(exc), status=404)
    return JSONResponse(renamed.model_dump())


async def project_anchor_patch_endpoint(request: Request) -> JSONResponse:
    """v0.13 Phase 0: PATCH the project anchor for a given canvas.

    Body fields (all optional):
      x, y, width, height, color, shape
    Only supplied fields are updated; the rest stay as before.
    """
    try:
        plot_root = _require_plot_root(request)
    except _ApiError as exc:
        return exc.response
    project_id = request.path_params["project_id"]
    canvas = request.path_params["canvas"]
    if canvas not in {"foundation", "actors", "services", "entities"}:
        return _error(f"unknown canvas {canvas!r}", status=400)
    try:
        body: dict[str, Any] = await request.json()
    except json.JSONDecodeError:
        return _error("invalid JSON body")
    try:
        proj = read_project(plot_root, project_id)
    except FileNotFoundError as exc:
        return _error(str(exc), status=404)
    from mashbill.models import AnchorPlacement

    current = proj.anchors.get(canvas, AnchorPlacement())
    patched = current.model_copy(update={k: v for k, v in body.items() if v is not None})
    new_anchors = {**proj.anchors, canvas: patched}
    proj = proj.model_copy(update={"anchors": new_anchors})
    write_project(plot_root, proj)
    return JSONResponse(proj.model_dump())


async def project_delete_endpoint(request: Request) -> Response:
    try:
        plot_root = _require_plot_root(request)
    except _ApiError as exc:
        return exc.response
    project_id = request.path_params["project_id"]
    try:
        delete_project(plot_root, project_id)
    except FileNotFoundError as exc:
        return _error(str(exc), status=404)
    return JSONResponse({"ok": True})


async def workspace_git_init_endpoint(request: Request) -> JSONResponse:
    """``POST /api/workspace/git-init`` — explicit user consent to create
    a git repo at the workspace root (D-2026-06-11-D).

    Idempotent: a workspace that already has ``.git/`` gets a 200 no-op
    so the viewer can retry-then-init without checking twice. A fresh
    init returns 201.
    """
    try:
        root = _require_workspace_root(request)
    except _ApiError as exc:
        return exc.response
    created = init_workspace_repo(root)
    return JSONResponse(
        {"ok": True, "created": created, "workspace_root": str(root)},
        status_code=201 if created else 200,
    )
