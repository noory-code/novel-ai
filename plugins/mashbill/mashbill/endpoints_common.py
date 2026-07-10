"""Shared request helpers + health endpoint (D-2026-06-11-B).

Extracted from the api_endpoints.py god module. Every per-area endpoint
module imports the helpers from here so the request → ``plot_root`` /
``workspace_root`` resolution and the standard JSON error envelope stay
in one place.
"""

from __future__ import annotations

from pathlib import Path

from starlette.requests import Request
from starlette.responses import JSONResponse

from mashbill.models import CanvasKind
from mashbill.workspace import resolve_plot_root

_ALLOWED_CANVAS_KINDS: frozenset[str] = frozenset(
    ("foundation", "actors", "services", "entities", "feature"),
)


def _project_path(request: Request) -> str | None:
    return request.query_params.get("project_path")


def _error(msg: str, status: int = 400) -> JSONResponse:
    return JSONResponse({"error": msg}, status_code=status)


class _ApiError(Exception):
    """Raised by ``_require_plot_root`` to short-circuit to a JSONResponse."""

    def __init__(self, response: JSONResponse):
        self.response = response


def _require_plot_root(request: Request) -> Path:
    """Return the resolved ``plot_root`` or raise ``_ApiError`` for a 4xx reply."""
    project_path = _project_path(request)
    if not project_path:
        raise _ApiError(_error("project_path query param is required"))
    try:
        return resolve_plot_root(project_path)
    except (FileNotFoundError, NotADirectoryError) as exc:
        raise _ApiError(_error(str(exc), status=404)) from exc


def _require_workspace_root(request: Request) -> Path:
    """Validate ``project_path`` and return the WORKSPACE ROOT itself (not its
    ``.plot/``) — used by the recursive discovery + dir-tree endpoints."""
    project_path = _project_path(request)
    if not project_path:
        raise _ApiError(_error("project_path query param is required"))
    base = Path(project_path).expanduser().resolve()
    if not base.exists():
        raise _ApiError(_error(f"project_path does not exist: {base}", status=404))
    if not base.is_dir():
        raise _ApiError(_error(f"project_path is not a directory: {base}", status=404))
    return base


def _parse_canvas_kind(raw: str) -> CanvasKind | None:
    if raw not in _ALLOWED_CANVAS_KINDS:
        return None
    # mypy is happy with the narrowed literal here.
    return raw  # type: ignore[return-value]


async def health_endpoint(_request: Request) -> JSONResponse:
    # ``schema_version`` + ``engine_version`` feed the viewer's boot-time compat
    # banner (D-2026-06-20-N Phase D part c): the app compares the engine's wire
    # schema_version against its committed wire-contract and warns on mismatch.
    from mashbill import __version__
    from mashbill.schema_export import SCHEMA_VERSION

    return JSONResponse(
        {
            "status": "ok",
            "service": "mashbill",
            "schema_version": SCHEMA_VERSION,
            "engine_version": __version__,
        }
    )
