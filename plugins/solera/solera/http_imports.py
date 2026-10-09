"""HTTP adapter for importing published format F releases."""

from __future__ import annotations

import json
import re
from pathlib import Path

from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from .errors import FormatError
from .http_endpoints import HttpError, _Body, _errors, _hub, _parse_body, _project_path
from .intake import (
    ImportConflictError,
    _reject_conflicting_import,
    import_release,
    load_imported_release,
    read_published_release,
)
from .workspace import Workspace, validate_path_name


class ImportBody(_Body):
    source: str


def _manifest_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _same_manifests(ws: Workspace, source: Path, project_snapshot: Path, destination: Path) -> bool:
    try:
        if destination.is_symlink() or any(path.is_symlink() for path in destination.rglob("*")):
            return False
        load_imported_release(ws, destination.name)
        return _manifest_json(source / "manifest.json") == _manifest_json(
            destination / "service" / "manifest.json"
        ) and _manifest_json(project_snapshot / "manifest.json") == _manifest_json(
            destination / "project" / "manifest.json"
        )
    except (OSError, ValueError):
        return False


def _import_for_http(ws: Workspace, source: Path, label: str) -> tuple[str, bool]:
    with ws.lock():
        try:
            incoming, project_snapshot = read_published_release(source)
        except (OSError, ValueError) as exc:
            raise HttpError(400, str(exc), "invalid_release") from exc
        service = incoming["service"]
        if (
            service["release"] != source.name
            or service["service"] != f"service/{source.parent.name}"
        ):
            raise HttpError(
                400, "release identity does not match source folders", "invalid_release"
            )

        destination = ws.spec_dir(label)
        if destination.exists() or destination.is_symlink():
            if _same_manifests(ws, source, project_snapshot, destination):
                return service["release"], False
            raise HttpError(
                409, f"different bundle already imported under {label}", "import_conflict"
            )

        try:
            _reject_conflicting_import(
                ws,
                incoming,
                service_path=source / "manifest.json",
                project_path=project_snapshot / "manifest.json",
            )
        except ImportConflictError as exc:
            raise HttpError(409, str(exc), "import_conflict") from exc

        try:
            import_release(ws, source, label=label)
        except (FileExistsError, ImportConflictError) as exc:
            raise HttpError(409, str(exc), "import_conflict") from exc
        except (OSError, ValueError) as exc:
            raise HttpError(400, str(exc), "invalid_release") from exc
        return service["release"], True


@_errors
async def import_release_endpoint(request: Request) -> Response:
    project = _project_path(request.query_params.get("project_path"))
    body = await _parse_body(request, ImportBody)
    source = Path(body.source).expanduser()
    if not source.is_absolute():
        source = project / source
    try:
        project_root = project.resolve()
        resolved_source = source.resolve()
        inside = resolved_source != project_root and resolved_source.is_relative_to(project_root)
        if not inside or not resolved_source.is_dir():
            raise ValueError("source does not resolve to a directory inside project_path")
    except (OSError, RuntimeError, ValueError) as exc:
        raise HttpError(400, str(exc), "import_source_outside") from exc

    if not re.fullmatch(r"vS[1-9][0-9]*", source.name):
        raise HttpError(400, "source folder must be named vS<N>", "invalid_release")
    for component in (source, *source.parents):
        if component.resolve() == project_root:
            break
        if component.is_symlink():
            raise HttpError(
                400, f"format F bundle contains a symlink: {component}", "invalid_release"
            )

    label = f"{source.parent.name}-{source.name}"
    try:
        validate_path_name(label)
    except FormatError as exc:
        raise HttpError(400, str(exc), "invalid_release") from exc
    ws = Workspace(project / ".noory" / "solera")
    release, imported = await run_in_threadpool(_import_for_http, ws, source, label)
    if imported:
        await _hub(request).notify_write(ws.root)
    return JSONResponse(
        {"label": label, "release": release, "imported": imported},
        status_code=201 if imported else 200,
    )
