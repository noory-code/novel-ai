"""Publish + unpublish + published-list endpoints (D-2026-06-11-B).

Extracted from the api_endpoints.py god module. Covers the project-level
blueprint publish (semver bump + git tag), the per-node publish + revert,
and the published-versions listing for the Inspector's history view.
"""

from __future__ import annotations

import json
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse

from mashbill.endpoints_common import (
    _ApiError,
    _error,
    _require_plot_root,
)
from mashbill.folder_io import _project_dir
from mashbill.git_store import GitNotInitializedError, TagAlreadyExistsError, tag_snapshot
from mashbill.workspace import workspace_root_from_plot_root


def _git_not_initialized_response(workspace_root: object) -> JSONResponse:
    """Structured 409 the viewer turns into the 'Initialize git repo?' modal
    (D-2026-06-11-D)."""
    return JSONResponse(
        {
            "error": "git not initialized in workspace",
            "needs_git_init": True,
            "workspace_root": str(workspace_root),
        },
        status_code=409,
    )

# ---------------------------------------------------------------------------
# v0.24.13 (D-2026-05-21-B) — project-level blueprint publish endpoint
# ---------------------------------------------------------------------------


def _bump_blueprint_version(current: str, bump: str) -> str:
    """Bump ``v<MAJOR>.<MINOR>.<PATCH>`` per the chosen level.

    - "major": ``v1.2.3`` → ``v2.0.0``
    - "minor": ``v1.2.3`` → ``v1.3.0``
    - "patch": ``v1.2.3`` → ``v1.2.4``
    """
    if not current.startswith("v"):
        raise ValueError(f"invalid blueprint version (must start with 'v'): {current!r}")
    parts = current[1:].split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        raise ValueError(f"invalid semver (need v<MAJOR>.<MINOR>.<PATCH>): {current!r}")
    major, minor, patch = (int(p) for p in parts)
    if bump == "major":
        return f"v{major + 1}.0.0"
    if bump == "minor":
        return f"v{major}.{minor + 1}.0"
    if bump == "patch":
        return f"v{major}.{minor}.{patch + 1}"
    raise ValueError(f"bump must be one of major/minor/patch, got {bump!r}")


async def project_publish_endpoint(request: Request) -> JSONResponse:
    """``POST /api/projects/{project_id}/publish``

    Body: ``{"bump": "major" | "minor" | "patch", "message": "..."}``

    Bumps ``ProjectDoc.blueprint_version``, persists the project, and
    creates a git tag at the resulting version. Tag name = the new
    version string (e.g. ``v0.2.0``). Idempotent for the *project*
    write (tags are unique, second call with the same target version
    after manual revert would 409).

    Returns ``{from_version, to_version, tag}``.
    """
    try:
        plot_root = _require_plot_root(request)
    except _ApiError as exc:
        return exc.response
    project_id = request.path_params["project_id"]
    folder = _project_dir(plot_root, project_id)
    if not (folder / "project.json").is_file():
        return _error(f"project not found: {project_id}", status=404)
    try:
        body: dict[str, Any] = await request.json()
    except json.JSONDecodeError:
        return _error("invalid JSON body")
    bump = body.get("bump")
    if bump not in ("major", "minor", "patch"):
        return _error("'bump' must be one of major/minor/patch")
    message_input = body.get("message")
    message = (
        message_input
        if isinstance(message_input, str) and message_input.strip()
        else None
    )

    from mashbill.folder_io import read_project, write_project

    project = read_project(plot_root, project_id)
    from_version = project.blueprint_version
    try:
        to_version = _bump_blueprint_version(from_version, bump)
    except ValueError as exc:
        return _error(str(exc))
    bumped = project.model_copy(update={"blueprint_version": to_version})
    write_project(plot_root, bumped)
    workspace_root = workspace_root_from_plot_root(plot_root)
    try:
        tag = tag_snapshot(workspace_root, to_version, message=message or to_version)
    except GitNotInitializedError:
        write_project(plot_root, project)
        return _git_not_initialized_response(workspace_root)
    except TagAlreadyExistsError as exc:
        # Roll back the project version on tag collision.
        write_project(plot_root, project)
        return _error(str(exc), status=409)
    return JSONResponse(
        {"from_version": from_version, "to_version": to_version, "tag": tag},
        status_code=201,
    )


# ---------------------------------------------------------------------------
# format F publish over HTTP (INT-g, D-2026-06-22-G) — the viewer-facing surface
# mirroring the MCP tools (publish_project_snapshot_tool / publish_service_tool).
# format F itself is defined in ``format_f.py`` + ``docs/specs/format-f.md``.
# ---------------------------------------------------------------------------


async def format_f_snapshot_endpoint(request: Request) -> JSONResponse:
    """``POST /api/projects/{project_id}/publish/snapshot``

    Freeze the project's shared structure (foundation / actors / entities) into
    a format F ``vP`` snapshot (D-2026-06-22-D). Returns the manifest.
    404 if the project is unknown.
    """
    try:
        plot_root = _require_plot_root(request)
    except _ApiError as exc:
        return exc.response
    project_id = request.path_params["project_id"]
    from mashbill.format_f import publish_project_snapshot

    try:
        manifest = publish_project_snapshot(plot_root, project_id)
    except FileNotFoundError as exc:
        return _error(str(exc), status=404)
    return JSONResponse(manifest, status_code=201)


async def format_f_service_publish_endpoint(request: Request) -> JSONResponse:
    """``POST /api/projects/{project_id}/services/{service_id}/publish``

    Freeze one service into a format F ``vS`` release — refs the latest ``vP``,
    bootstrap + refs-integrity gated (D-2026-06-22-D/E). Returns the manifest.
    Errors:
      - 404 if the project or service is not found
      - 409 if there is no ``vP`` yet (bootstrap) or a ref does not resolve in
        the based_on ``vP`` (refs-integrity) — both are write-boundary gates.
    """
    try:
        plot_root = _require_plot_root(request)
    except _ApiError as exc:
        return exc.response
    project_id = request.path_params["project_id"]
    service_id = request.path_params["service_id"]
    from mashbill.format_f import publish_service

    try:
        manifest = publish_service(plot_root, project_id, service_id)
    except FileNotFoundError as exc:
        return _error(str(exc), status=404)
    except ValueError as exc:
        return _error(str(exc), status=409)
    return JSONResponse(manifest, status_code=201)
