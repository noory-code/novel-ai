"""External-CLI MCP registration endpoints (D-2026-06-11-E, Track 2.5).

Three URLs back the R7 chat panel's "connect Novel to your CLI" UX:

    GET  /api/mcp/providers              — list providers + status
    POST /api/mcp/providers/{name}/register
    POST /api/mcp/providers/{name}/unregister

Workspace-scoped via ``project_path`` so the endpoints sit alongside the
rest of the API surface, even though MCP registration itself is a
user-global edit to ``~/.<cli>/config…``.
"""

from __future__ import annotations

from pydantic import ValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse

from mashbill.chat_provider import (
    ChatProviderSelection,
    read_selection,
    write_selection,
)
from mashbill.endpoints_common import _ApiError, _error, _require_plot_root
from mashbill.mcp_registration import (
    ProviderName,
    detect_providers,
    plot_plugin_root,
    register_plot,
    unregister_plot,
)


async def mcp_providers_endpoint(_request: Request) -> JSONResponse:
    """``GET /api/mcp/providers`` — one row per supported provider.

    Each row: ``{name, installed, registered, config_path}``. The viewer's
    chat panel reads this once on open and re-reads after a
    register/unregister to refresh button state.
    """
    statuses = detect_providers()
    return JSONResponse(
        {
            "providers": [
                {
                    "name": s.name,
                    "installed": s.installed,
                    "registered": s.registered,
                    "config_path": s.config_path,
                }
                for s in statuses.values()
            ]
        }
    )


_VALID_PROVIDERS: frozenset[str] = frozenset({"claude-code", "codex"})


def _provider_from_path(request: Request) -> ProviderName | None:
    raw = request.path_params.get("provider", "")
    if raw == "claude-code":
        return "claude-code"
    if raw == "codex":
        return "codex"
    return None


async def mcp_register_endpoint(request: Request) -> JSONResponse:
    """``POST /api/mcp/providers/{provider}/register`` — add the Novel mcp
    server entry to the named provider's config. Idempotent."""
    provider = _provider_from_path(request)
    if provider is None:
        return _error(f"unknown provider: {request.path_params.get('provider')!r}", status=404)
    try:
        register_plot(provider, plot_plugin_root())
    except OSError as exc:
        return _error(f"failed to write provider config: {exc}", status=500)
    return JSONResponse({"ok": True, "provider": provider}, status_code=201)


async def mcp_unregister_endpoint(request: Request) -> JSONResponse:
    """``POST /api/mcp/providers/{provider}/unregister`` — drop the Novel
    entry from the provider's config. Idempotent."""
    provider = _provider_from_path(request)
    if provider is None:
        return _error(f"unknown provider: {request.path_params.get('provider')!r}", status=404)
    try:
        unregister_plot(provider)
    except OSError as exc:
        return _error(f"failed to write provider config: {exc}", status=500)
    return JSONResponse({"ok": True, "provider": provider})


async def chat_provider_get_endpoint(request: Request) -> JSONResponse:
    """``GET /api/chat/provider`` — return the workspace's persisted chat-CLI choice.

    Body shape: ``{"provider": ProviderName | null}``. A workspace with no
    persisted choice (fresh, or just cleared) returns ``null``. The choice
    lives at ``<workspace>/.noory/plot/chat-provider``.
    """
    try:
        plot_root = _require_plot_root(request)
    except _ApiError as exc:
        return exc.response
    sel = read_selection(plot_root)
    return JSONResponse({"provider": sel.provider, "model": sel.model})


async def chat_provider_put_endpoint(request: Request) -> JSONResponse:
    """``PUT /api/chat/provider`` — persist the workspace's chat-CLI choice.

    Body: ``{"provider": ProviderName | null}``. ``null`` clears the choice
    without removing the file (keeps a single SSOT on disk: presence of the
    file = "Novel has seen this workspace"). Pydantic rejects unknown
    provider strings with 422 so corrupt input never reaches disk.
    """
    try:
        plot_root = _require_plot_root(request)
    except _ApiError as exc:
        return exc.response
    try:
        body = await request.json()
    except ValueError:
        return _error("invalid JSON body", status=400)
    try:
        selection = ChatProviderSelection.model_validate(body)
    except ValidationError as exc:
        return _error(str(exc), status=422)
    write_selection(plot_root, selection)
    return JSONResponse({"provider": selection.provider, "model": selection.model})
