"""Text-file + folder endpoints powering the Inspector MD editor
(D-2026-06-11-B). Extracted from the api_endpoints.py god module.

Everything a project owns sits under ``.plot/{project_id}/``; the path
helpers here scope every request to that prefix so a caller can't climb
into another project (or outside ``.plot/``).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse, Response

from mashbill.endpoints_common import _ApiError, _error, _require_plot_root
from mashbill.file_io import (
    ALLOWED_IMAGE_EXTENSIONS,
    ExtensionNotAllowedError,
    UnsafePathError,
    ensure_folder,
    read_text_file,
    resolve_safe_path,
    uniquify_folder,
    write_text_file,
)


def _project_scoped_root(plot_root: Path, project_id: str) -> Path:
    """Directory a project owns; File/folder API paths are relative to this
    scope so a request can't climb out of it.

    S2 (D-2026-06-21-AB): flat layout — ``_project_dir`` returns ``plot_root``
    itself for the lone project (or the legacy nested ``{project_id}/`` while it
    survives). Callers must confirm the project exists via
    ``project.json`` (``plot_root`` always ``is_dir``).
    """
    from mashbill.folder_io import _project_dir

    return _project_dir(plot_root, project_id)


async def file_get_endpoint(request: Request) -> JSONResponse:
    try:
        plot_root = _require_plot_root(request)
    except _ApiError as exc:
        return exc.response
    project_id = request.query_params.get("project_id")
    if not project_id:
        return _error("'project_id' query param is required")
    rel_path = request.query_params.get("path")
    if not rel_path:
        return _error("'path' query param is required")
    project_root = _project_scoped_root(plot_root, project_id)
    if not (project_root / "project.json").is_file():
        return _error(f"project not found: {project_id}", status=404)
    try:
        content = read_text_file(project_root, rel_path)
    except (UnsafePathError, ExtensionNotAllowedError) as exc:
        return _error(str(exc), status=400)
    except ValueError as exc:
        return _error(str(exc), status=413)
    return JSONResponse({"path": rel_path, "content": content})


async def file_raw_endpoint(request: Request) -> Response:
    """v0.24.0 (D-2026-05-17-L) — serve raw bytes for image embeds.

    Same query shape as ``file_get_endpoint`` (``project_path`` +
    ``project_id`` + ``path``), but returns the file's bytes via
    ``FileResponse`` so the browser ``<img>`` tag can render it
    directly. Extension allow-list = ``ALLOWED_IMAGE_EXTENSIONS``
    (.png/.jpg/.jpeg/.gif/.webp/.avif/.svg). Path-traversal safety
    via the existing ``resolve_safe_path``.
    """
    try:
        plot_root = _require_plot_root(request)
    except _ApiError as exc:
        return exc.response
    project_id = request.query_params.get("project_id")
    if not project_id:
        return _error("'project_id' query param is required")
    rel_path = request.query_params.get("path")
    if not rel_path:
        return _error("'path' query param is required")
    project_root = _project_scoped_root(plot_root, project_id)
    if not (project_root / "project.json").is_file():
        return _error(f"project not found: {project_id}", status=404)
    try:
        target = resolve_safe_path(project_root, rel_path)
    except UnsafePathError as exc:
        return _error(str(exc), status=400)
    if target.suffix.lower() not in ALLOWED_IMAGE_EXTENSIONS:
        return _error(
            f"extension {target.suffix!r} not allowed for raw image read",
            status=400,
        )
    if not target.is_file():
        return _error(f"file not found: {rel_path}", status=404)
    return FileResponse(target)


async def file_put_endpoint(request: Request) -> JSONResponse:
    try:
        plot_root = _require_plot_root(request)
    except _ApiError as exc:
        return exc.response
    project_id = request.query_params.get("project_id")
    if not project_id:
        return _error("'project_id' query param is required")
    rel_path = request.query_params.get("path")
    if not rel_path:
        return _error("'path' query param is required")
    try:
        body: dict[str, Any] = await request.json()
    except json.JSONDecodeError:
        return _error("invalid JSON body")
    content = body.get("content")
    if not isinstance(content, str):
        return _error("'content' must be a string")
    project_root = _project_scoped_root(plot_root, project_id)
    if not (project_root / "project.json").is_file():
        return _error(f"project not found: {project_id}", status=404)
    try:
        write_text_file(project_root, rel_path, content)
    except (UnsafePathError, ExtensionNotAllowedError) as exc:
        return _error(str(exc), status=400)
    except ValueError as exc:
        return _error(str(exc), status=413)
    # v0.9: no longer mirrors a summary back into the canvas — typed
    # fields live on the node directly, so writing ``details.md`` is a
    # leaf operation. The watcher still picks up the disk change and
    # broadcasts ``project_changed`` for any open client.
    return JSONResponse({"path": rel_path, "ok": True})


async def folder_post_endpoint(request: Request) -> JSONResponse:
    """Create ``.plot/{project_id}/{path}`` with a fresh ``index.md``. Returns
    the path actually created (may have a ``-2``/``-3`` suffix when the
    desired name was taken)."""
    try:
        plot_root = _require_plot_root(request)
    except _ApiError as exc:
        return exc.response
    try:
        body: dict[str, Any] = await request.json()
    except json.JSONDecodeError:
        return _error("invalid JSON body")
    project_id = body.get("project_id")
    if not isinstance(project_id, str) or not project_id:
        return _error("'project_id' is required and must be a non-empty string")
    desired = body.get("path")
    if not isinstance(desired, str) or not desired.strip():
        return _error("'path' is required and must be a non-empty string")
    project_root = _project_scoped_root(plot_root, project_id)
    if not (project_root / "project.json").is_file():
        return _error(f"project not found: {project_id}", status=404)
    try:
        actual = uniquify_folder(project_root, desired)
        ensure_folder(project_root, actual)
    except UnsafePathError as exc:
        return _error(str(exc), status=400)
    return JSONResponse({"path": actual}, status_code=201)
