"""Read-only work proposal and published-basis HTTP endpoints."""

from __future__ import annotations

import json
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse

from mashbill.chat_provider import read_selection
from mashbill.chat_session import chat_registry
from mashbill.endpoints_common import _ApiError, _error, _require_workspace_root
from mashbill.mcp_registration import ProviderName
from mashbill.storage import _ensure_project
from mashbill.work_proposals import (
    UnknownSlugError,
    latest_service_releases,
    propose_nodes,
    propose_work_item,
    propose_work_split,
    published_basis,
    published_service_nodes,
    validate_split_request,
)
from mashbill.workspace import workspace_root_from_plot_root


def _coded_error(
    code: str, message: str, status: int, *, reason: str | None = None
) -> JSONResponse:
    body = {"error": message, "code": code}
    if reason is not None:
        body["reason"] = reason
    return JSONResponse(body, status_code=status)


def _selected_provider(plot_root: Any) -> tuple[ProviderName, str | None] | JSONResponse:
    selection = read_selection(plot_root)
    if selection.provider is None:
        return _coded_error("no_chat_provider", "no chat provider chosen", 409)
    return selection.provider, selection.model


def _provider(request: Request, plot_root: Any, provider_name: ProviderName) -> Any:
    registry = getattr(request.app.state, "chat_registry", None) or chat_registry()
    return registry.one_shot(workspace_root_from_plot_root(plot_root), provider_name)


def _proposal_error(exc: Exception) -> JSONResponse:
    reason = (
        "timed out" if isinstance(exc, TimeoutError) else str(exc).strip() or "proposal call failed"
    )
    return _coded_error("proposal_failed", "work proposal failed", 502, reason=reason[:200])


async def _request_data(
    request: Request, *, item: bool
) -> tuple[Any, Any, list[str], str] | JSONResponse:
    project = _project_data(request)
    if isinstance(project, JSONResponse):
        return project
    plot_root, project_dir = project
    try:
        body: Any = await request.json()
    except (json.JSONDecodeError, UnicodeError):
        return _error("invalid JSON body")
    if not isinstance(body, dict):
        return _error("invalid JSON body")
    slugs = body.get("slugs")
    if (
        not isinstance(slugs, list)
        or not slugs
        or any(not isinstance(slug, str) or not slug.strip() for slug in slugs)
    ):
        return _error("'slugs' must be a non-empty list of non-blank strings")
    if len(slugs) != len(set(slugs)):
        return _error("'slugs' must not contain duplicates")
    outcome = body.get("outcome", "") if item else ""
    if item and (not isinstance(outcome, str) or not outcome.strip()):
        return _error("'outcome' must be a non-blank string")
    return plot_root, project_dir, slugs, outcome


def _project_data(request: Request) -> tuple[Any, Any] | JSONResponse:
    try:
        workspace_root = _require_workspace_root(request)
    except _ApiError as exc:
        return exc.response
    if workspace_root.name == "novel" and workspace_root.parent.name == ".noory":
        plot_root = workspace_root
    else:
        plot_root = workspace_root / ".noory" / "novel"
    if not plot_root.is_dir():
        return _error(f"project data not found: {plot_root}", status=404)
    project_id = request.path_params["project_id"]
    try:
        project_dir = _ensure_project(plot_root, project_id)
    except FileNotFoundError:
        return _error(f"project not found: {project_id}", status=404)
    return plot_root, project_dir


async def published_releases_endpoint(request: Request) -> JSONResponse:
    project = _project_data(request)
    if isinstance(project, JSONResponse):
        return project
    _, project_dir = project
    releases = [
        {"service": service, "release": manifest["release"], "source": str(folder.resolve())}
        for service, folder, manifest in latest_service_releases(project_dir)
    ]
    return JSONResponse({"releases": releases})


async def work_proposal_nodes_endpoint(request: Request) -> JSONResponse:
    project = _project_data(request)
    if isinstance(project, JSONResponse):
        return project
    plot_root, project_dir = project
    try:
        body: Any = await request.json()
    except (json.JSONDecodeError, UnicodeError):
        return _error("invalid JSON body")
    if not isinstance(body, dict):
        return _error("invalid JSON body")
    goal = body.get("goal")
    conditions = body.get("conditions", [])
    ancestors = body.get("ancestors", [])
    if not isinstance(goal, str) or not goal.strip():
        return _error("'goal' must be a non-blank string")
    for name, value in (("conditions", conditions), ("ancestors", ancestors)):
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            return _error(f"'{name}' must be a list of strings")
    selected = _selected_provider(plot_root)
    if isinstance(selected, JSONResponse):
        return selected
    provider_name, model = selected
    try:
        nodes = published_service_nodes(latest_service_releases(project_dir))
        provider = _provider(request, plot_root, provider_name)
        candidates = await propose_nodes(goal, conditions, ancestors, nodes, provider, model)
    except Exception as exc:
        return _proposal_error(exc)
    return JSONResponse({"candidates": candidates})


async def work_proposal_basis_endpoint(request: Request) -> JSONResponse:
    data = await _request_data(request, item=False)
    if isinstance(data, JSONResponse):
        return data
    _, project_dir, slugs, _ = data
    try:
        releases = published_basis(project_dir, slugs)
    except UnknownSlugError as exc:
        return _coded_error("unknown_slug", f"unknown slug: {exc}", 404)
    return JSONResponse({"basis": [pin for pin, _, _ in releases]})


async def work_proposal_item_endpoint(request: Request) -> JSONResponse:
    data = await _request_data(request, item=True)
    if isinstance(data, JSONResponse):
        return data
    plot_root, project_dir, slugs, outcome = data
    try:
        releases = published_basis(project_dir, slugs)
    except UnknownSlugError as exc:
        return _coded_error("unknown_slug", f"unknown slug: {exc}", 404)
    selected = _selected_provider(plot_root)
    if isinstance(selected, JSONResponse):
        return selected
    provider_name, model = selected
    try:
        provider = _provider(request, plot_root, provider_name)
        proposal = await propose_work_item(slugs, outcome, releases, provider, model)
    except Exception as exc:
        return _proposal_error(exc)
    return JSONResponse({"proposal": proposal})


async def work_proposal_split_endpoint(request: Request) -> JSONResponse:
    project = _project_data(request)
    if isinstance(project, JSONResponse):
        return project
    plot_root, project_dir = project
    try:
        body: Any = await request.json()
    except (json.JSONDecodeError, UnicodeError):
        return _error("invalid JSON body")
    try:
        item, existing_children = validate_split_request(body)
    except ValueError as exc:
        return _error(str(exc))
    releases = []
    for slug in item.get("realizes", []):
        try:
            releases.extend(published_basis(project_dir, [slug]))
        except UnknownSlugError:
            continue
    selected = _selected_provider(plot_root)
    if isinstance(selected, JSONResponse):
        return selected
    provider_name, model = selected
    try:
        provider = _provider(request, plot_root, provider_name)
        proposal = await propose_work_split(item, existing_children, releases, provider, model)
    except Exception as exc:
        return _proposal_error(exc)
    return JSONResponse({"proposal": proposal})
