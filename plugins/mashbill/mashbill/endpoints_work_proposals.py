"""Read-only work proposal and published-basis HTTP endpoints."""

from __future__ import annotations

import json
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse

from mashbill.chat_provider import read_selection
from mashbill.chat_session import chat_registry
from mashbill.endpoints_common import _ApiError, _error, _require_workspace_root
from mashbill.folder_io import _project_dir
from mashbill.work_proposals import UnknownSlugError, propose_work_item, published_basis
from mashbill.workspace import workspace_root_from_plot_root


def _coded_error(
    code: str, message: str, status: int, *, reason: str | None = None
) -> JSONResponse:
    body = {"error": message, "code": code}
    if reason is not None:
        body["reason"] = reason
    return JSONResponse(body, status_code=status)


async def _request_data(
    request: Request, *, item: bool
) -> tuple[Any, Any, list[str], str] | JSONResponse:
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
    project_dir = _project_dir(plot_root, project_id)
    if not (project_dir / "project.json").is_file():
        return _error(f"project not found: {project_id}", status=404)
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
    selection = read_selection(plot_root)
    if selection.provider is None:
        return _coded_error("no_chat_provider", "no chat provider chosen", 409)
    registry = getattr(request.app.state, "chat_registry", None) or chat_registry()
    try:
        provider = registry.one_shot(workspace_root_from_plot_root(plot_root), selection.provider)
        proposal = await propose_work_item(slugs, outcome, releases, provider, selection.model)
    except Exception as exc:
        reason = (
            "timed out"
            if isinstance(exc, TimeoutError)
            else str(exc).strip() or "proposal call failed"
        )
        return _coded_error("proposal_failed", "work proposal failed", 502, reason=reason[:200])
    return JSONResponse({"proposal": proposal})
