"""Viewer-context bridge endpoint (D-2026-06-15-D).

``POST /api/viewer/context`` — the viewer reports its live canvas context
(active scope + node selection) so the external MCP agent can read it via
``get_viewer_context``. Body::

    {"project_path": "<abs path>", "scope": "<ChatScope>", "selection": [...]}

The server stamps ``updated_at`` (its own ``time.time()`` — same machine as the
reader, so the clock is shared) and writes the rendezvous file. Returns
``202 {"accepted": true}``. Fire-and-forget from the viewer's perspective.
"""

from __future__ import annotations

import time
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse

from mashbill.chat_providers.base import DEFAULT_CHAT_SCOPE, is_valid_scope
from mashbill.viewer_context import write_viewer_context
from mashbill.workspace import resolve_plot_root


def _sanitize_selection(raw: Any) -> list[dict[str, Any]]:
    """Keep only well-formed ``{id, kind, label}`` dicts; drop the rest."""
    if not isinstance(raw, list):
        return []
    return [n for n in raw if isinstance(n, dict)]


async def viewer_context_endpoint(request: Request) -> JSONResponse:
    """``POST /api/viewer/context`` — record the viewer's current context."""
    try:
        body: dict[str, Any] = await request.json()
    except ValueError:
        return JSONResponse({"error": "invalid JSON body"}, status_code=400)

    project_path = body.get("project_path")
    if not isinstance(project_path, str) or not project_path:
        return JSONResponse({"error": "project_path required"}, status_code=400)

    raw_scope = body.get("scope")
    scope: str
    if raw_scope is None:
        scope = DEFAULT_CHAT_SCOPE
    elif isinstance(raw_scope, str) and is_valid_scope(raw_scope):
        scope = raw_scope
    else:
        return JSONResponse({"error": "invalid chat scope"}, status_code=400)

    try:
        plot_root = resolve_plot_root(project_path)
    except (FileNotFoundError, NotADirectoryError) as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)

    write_viewer_context(
        plot_root,
        scope=scope,
        selection=_sanitize_selection(body.get("selection")),
        now=time.time(),
    )
    return JSONResponse({"accepted": True}, status_code=202)
