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

from mashbill.blueprint_publish import BlueprintUnchangedError, publish_blueprint
from mashbill.chat_provider import read_selection
from mashbill.chat_session import chat_registry
from mashbill.endpoints_common import (
    _ApiError,
    _error,
    _require_plot_root,
)
from mashbill.folder_io import _project_dir
from mashbill.format_f_slugs import InvalidSlugNamesError, SlugNamesNeededError
from mashbill.git_store import (
    GitNotInitializedError,
    TagAlreadyExistsError,
    blueprint_canvas_changed,
)
from mashbill.workspace import workspace_root_from_plot_root


def _parse_slugs(body: dict[str, Any]) -> dict[str, str] | None:
    if "slugs" not in body:
        return None
    value = body["slugs"]
    if not isinstance(value, dict) or not all(
        isinstance(node_id, str) and isinstance(slug, str) for node_id, slug in value.items()
    ):
        raise ValueError("'slugs' must be an object of node id to English id")
    return value


def _invalid_slugs_response(exc: InvalidSlugNamesError) -> JSONResponse:
    return JSONResponse(
        {"error": str(exc), "invalid_slugs": exc.problems},
        status_code=400,
    )


def _needs_slugs_response(exc: SlugNamesNeededError) -> JSONResponse:
    return JSONResponse(
        {"error": str(exc), "needs_slugs": exc.nodes},
        status_code=409,
    )


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


async def project_publish_endpoint(request: Request) -> JSONResponse:
    """``POST /api/projects/{project_id}/publish``

    Body: ``{"bump": "major" | "minor" | "patch", "message": "..."}``

    Atomically writes a format-F snapshot, bumps the project version, and tags
    the resulting Novel data commit.
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
        body: Any = await request.json()
    except json.JSONDecodeError:
        return _error("invalid JSON body")
    if not isinstance(body, dict):
        return _error("invalid JSON body")
    bump = body.get("bump")
    if not isinstance(bump, str) or bump not in ("major", "minor", "patch"):
        return _error("'bump' must be one of major/minor/patch")
    message_input = body.get("message")
    message = message_input if isinstance(message_input, str) and message_input.strip() else None
    try:
        slugs = _parse_slugs(body)
    except ValueError as exc:
        return _error(str(exc))
    workspace_root = workspace_root_from_plot_root(plot_root)
    try:
        result = publish_blueprint(plot_root, project_id, bump, message=message, slugs=slugs)
    except FileNotFoundError as exc:
        return _error(str(exc), status=404)
    except GitNotInitializedError:
        return _git_not_initialized_response(workspace_root)
    except BlueprintUnchangedError as exc:
        return JSONResponse(
            {
                "error": str(exc),
                "unchanged": True,
            },
            status_code=409,
        )
    except TagAlreadyExistsError as exc:
        return _error(str(exc), status=409)
    except InvalidSlugNamesError as exc:
        return _invalid_slugs_response(exc)
    except SlugNamesNeededError as exc:
        return _needs_slugs_response(exc)
    except ValueError as exc:
        return _error(str(exc))
    return JSONResponse(result, status_code=201)


async def project_publish_status_endpoint(request: Request) -> JSONResponse:
    """``GET /api/projects/{project_id}/publish/status``

    Report whether canvas content differs from the current blueprint-version
    tag without changing project files or git state; no git repo means changed.
    """
    try:
        plot_root = _require_plot_root(request)
    except _ApiError as exc:
        return exc.response
    project_id = request.path_params["project_id"]
    folder = _project_dir(plot_root, project_id)
    if not (folder / "project.json").is_file():
        return _error(f"project not found: {project_id}", status=404)

    from mashbill.folder_io import read_project

    project = read_project(plot_root, project_id)
    workspace_root = workspace_root_from_plot_root(plot_root)
    try:
        changed = blueprint_canvas_changed(
            workspace_root,
            folder,
            project.blueprint_version,
        )
    except GitNotInitializedError:
        changed = True
    return JSONResponse({"current_version": project.blueprint_version, "changed": changed})


# ---------------------------------------------------------------------------
# format F service publish over HTTP (INT-g, D-2026-06-22-G).
# format F itself is defined in ``format_f.py`` + ``docs/specs/format-f.md``.
# ---------------------------------------------------------------------------


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

    raw = await request.body()
    if raw:
        try:
            body: Any = json.loads(raw)
        except json.JSONDecodeError:
            return _error("invalid JSON body")
        if not isinstance(body, dict):
            return _error("invalid JSON body")
    else:
        body = {}
    try:
        slugs = _parse_slugs(body)
    except ValueError as exc:
        return _error(str(exc))
    try:
        manifest = publish_service(plot_root, project_id, service_id, slugs=slugs)
    except FileNotFoundError as exc:
        return _error(str(exc), status=404)
    except InvalidSlugNamesError as exc:
        return _invalid_slugs_response(exc)
    except SlugNamesNeededError as exc:
        return _needs_slugs_response(exc)
    except ValueError as exc:
        return _error(str(exc), status=409)
    return JSONResponse(manifest, status_code=201)


async def slug_proposals_endpoint(request: Request) -> JSONResponse:
    """Propose person-confirmable English ids for one publication scope."""
    try:
        plot_root = _require_plot_root(request)
    except _ApiError as exc:
        return exc.response
    project_id = request.path_params["project_id"]
    folder = _project_dir(plot_root, project_id)
    if not (folder / "project.json").is_file():
        return _error(f"project not found: {project_id}", status=404)
    try:
        body: Any = await request.json()
    except json.JSONDecodeError:
        return _error("invalid JSON body")
    if not isinstance(body, dict):
        return _error("invalid JSON body")
    scope = body.get("scope")
    if scope not in ("project", "service"):
        return _error("'scope' must be one of project/service")
    service_id = body.get("service_id")
    if service_id is not None and not isinstance(service_id, str):
        return _error("'service_id' must be a string")
    if scope == "service" and not service_id:
        return _error("'service_id' is required for service scope")
    suggest = body.get("suggest", True)
    if not isinstance(suggest, bool):
        return _error("'suggest' must be a boolean")

    selection = read_selection(plot_root)
    provider = None
    if suggest and selection.provider is not None:
        registry = getattr(request.app.state, "chat_registry", None) or chat_registry()
        provider = registry.one_shot(
            workspace_root_from_plot_root(plot_root),
            selection.provider,
        )
    from mashbill.slug_suggest import slug_proposals

    try:
        result = await slug_proposals(
            plot_root,
            project_id,
            scope,
            service_id,
            suggest=suggest,
            provider=provider,
            model=selection.model,
        )
    except FileNotFoundError as exc:
        return _error(str(exc), status=404)
    except ValueError as exc:
        return _error(str(exc), status=409 if scope == "service" else 400)
    return JSONResponse(result)
