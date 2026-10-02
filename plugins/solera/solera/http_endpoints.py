"""Thin Starlette endpoints over Solera's deterministic core."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import asdict
from pathlib import Path
from typing import Any, TypeVar, cast

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from . import __version__
from .broadcast import BroadcastHub
from .errors import SoleraError, UnknownParentError, UnknownWorkItemError
from .gate import GateResult
from .graph import completion, items_by_slugs, load_items
from .planning import add_after, create_item, move_item, remove_after, set_goal, set_realizes
from .supervisor import blocked_items, check_item, ready_leaves, uncheck_item
from .workspace import Workspace

_Model = TypeVar("_Model", bound=BaseModel)
_Endpoint = Callable[[Request], Awaitable[Response]]
# A check returns the last characters of the gate's output, enough to see why it failed.
_GATE_OUTPUT_TAIL = 4000


class _Body(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class SlugsBody(_Body):
    slugs: list[str]


class CreateItemBody(_Body):
    parent: str | None
    goal: str
    level: str | None = None
    gate: str = ""
    realizes: list[str] = Field(default_factory=list)
    after: list[str] = Field(default_factory=list)


class PatchItemBody(_Body):
    goal: str = ""
    realizes: list[str] = Field(default_factory=list)


class MoveItemBody(_Body):
    parent: str | None
    index: int | None


class AfterBody(_Body):
    predecessor: str


class HttpError(Exception):
    """A request-level error with its public status and message."""

    def __init__(self, status_code: int, message: str, code: str = "invalid") -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.code = code


def _errors(endpoint: _Endpoint) -> _Endpoint:
    async def wrapped(request: Request) -> Response:
        try:
            return await endpoint(request)
        except HttpError as exc:
            return JSONResponse(
                {"error": exc.message, "code": exc.code}, status_code=exc.status_code
            )
        except (UnknownWorkItemError, UnknownParentError) as exc:
            return JSONResponse({"error": str(exc), "code": exc.code}, status_code=404)
        except SoleraError as exc:
            return JSONResponse({"error": str(exc), "code": exc.code}, status_code=400)
        except ValueError as exc:
            return JSONResponse({"error": str(exc), "code": "invalid"}, status_code=400)

    return wrapped


async def _parse_body(request: Request, model: type[_Model]) -> _Model:
    try:
        value = await request.json()
        return model.model_validate(value)
    except (ValueError, ValidationError) as exc:
        raise HttpError(400, str(exc), "invalid_request") from exc


def _project_path(raw: str | None) -> Path:
    if raw is None or not raw:
        raise HttpError(400, "project_path query param required", "project_path_required")
    path = Path(raw)
    if not path.is_absolute():
        raise HttpError(
            400,
            "project_path must be an absolute path",
            "project_path_not_absolute",
        )
    return path


def _workspace(request: Request) -> Workspace:
    project_path = _project_path(request.query_params.get("project_path"))
    return Workspace(project_path / ".noory" / "solera")


def _hub(request: Request) -> BroadcastHub:
    return cast(BroadcastHub, request.app.state.hub)


def _require_item(ws: Workspace, item_id: str, *, as_parent: bool = False) -> None:
    if item_id not in ws.list_items():
        error_type = UnknownParentError if as_parent else UnknownWorkItemError
        raise error_type(f"unknown work item: {item_id}")


def _blocked_json(blocked: list[Any]) -> list[dict[str, Any]]:
    return [
        {
            "id": leaf.leaf_id,
            "waiting_on": list(leaf.waiting_on),
            "reasons": list(leaf.reasons),
            "names_no_design_node": leaf.names_no_design_node,
        }
        for leaf in blocked
    ]


@_errors
async def health_endpoint(_request: Request) -> Response:
    return JSONResponse({"ok": True, "engine": "solera", "version": __version__})


@_errors
async def work_endpoint(request: Request) -> Response:
    ws = _workspace(request)
    items = load_items(ws)
    ready, _agent_blocked = ready_leaves(ws)
    blocked = blocked_items(ws)
    current = ws.load_progress().item if ws.progress_path.is_file() else None
    return JSONResponse(
        {
            "items": [item.model_dump() for item in items.values()],
            "progress": {item_id: asdict(value) for item_id, value in completion(items).items()},
            "ready": ready,
            "blocked": _blocked_json(blocked),
            "current": current,
        }
    )


@_errors
async def work_by_slugs_endpoint(request: Request) -> Response:
    ws = _workspace(request)
    body = await _parse_body(request, SlugsBody)
    return JSONResponse({"by_slug": items_by_slugs(load_items(ws), body.slugs)})


@_errors
async def create_item_endpoint(request: Request) -> Response:
    ws = _workspace(request)
    body = await _parse_body(request, CreateItemBody)
    if body.parent is not None:
        _require_item(ws, body.parent, as_parent=True)
    level = body.level if body.level is not None else ("story" if body.parent is None else "action")
    item = create_item(
        ws,
        level,
        body.goal,
        gate=body.gate,
        parent=body.parent,
        realizes=body.realizes,
        after=body.after,
    )
    await _hub(request).notify_write(ws.root)
    return JSONResponse(item.model_dump(), status_code=201)


@_errors
async def patch_item_endpoint(request: Request) -> Response:
    ws = _workspace(request)
    item_id = request.path_params["id"]
    _require_item(ws, item_id)
    body = await _parse_body(request, PatchItemBody)
    if not body.model_fields_set:
        raise HttpError(
            400,
            "at least one of goal or realizes is required",
            "invalid_request",
        )
    if "goal" in body.model_fields_set:
        set_goal(ws, item_id, body.goal)
    if "realizes" in body.model_fields_set:
        set_realizes(ws, item_id, body.realizes)
    item = ws.load_item(item_id)
    await _hub(request).notify_write(ws.root)
    return JSONResponse(item.model_dump())


@_errors
async def move_item_endpoint(request: Request) -> Response:
    ws = _workspace(request)
    item_id = request.path_params["id"]
    _require_item(ws, item_id)
    body = await _parse_body(request, MoveItemBody)
    if body.parent is not None:
        _require_item(ws, body.parent, as_parent=True)
    before = load_items(ws)
    move_item(ws, item_id, body.parent, body.index)
    after = load_items(ws)
    rewritten = [item for changed_id, item in after.items() if before.get(changed_id) != item]
    if rewritten:
        await _hub(request).notify_write(ws.root)
    return JSONResponse({"items": [item.model_dump() for item in rewritten]})


@_errors
async def add_after_endpoint(request: Request) -> Response:
    ws = _workspace(request)
    item_id = request.path_params["id"]
    _require_item(ws, item_id)
    body = await _parse_body(request, AfterBody)
    before = ws.load_item(item_id)
    item = add_after(ws, item_id, body.predecessor)
    if item != before:
        await _hub(request).notify_write(ws.root)
    return JSONResponse(item.model_dump())


@_errors
async def remove_after_endpoint(request: Request) -> Response:
    ws = _workspace(request)
    item_id = request.path_params["id"]
    _require_item(ws, item_id)
    before = ws.load_item(item_id)
    item = remove_after(ws, item_id, request.path_params["predecessor"])
    if item != before:
        await _hub(request).notify_write(ws.root)
    return JSONResponse(item.model_dump())


def _gate_json(result: GateResult | None) -> dict[str, Any] | None:
    if result is None:
        return None
    return {
        "passed": result.passed,
        "exit_code": result.exit_code,
        "timed_out": result.timed_out,
        "output": (result.stdout + result.stderr)[-_GATE_OUTPUT_TAIL:],
    }


@_errors
async def check_item_endpoint(request: Request) -> Response:
    project_path = _project_path(request.query_params.get("project_path"))
    ws = _workspace(request)
    item_id = request.path_params["id"]
    _require_item(ws, item_id)
    before = ws.load_item(item_id)
    # A gate may run for minutes; keep it off the event loop.
    result = await run_in_threadpool(check_item, ws, item_id, cwd=project_path)
    if result.item != before:
        await _hub(request).notify_write(ws.root)
    return JSONResponse({"item": result.item.model_dump(), "gate": _gate_json(result.gate)})


@_errors
async def uncheck_item_endpoint(request: Request) -> Response:
    ws = _workspace(request)
    item_id = request.path_params["id"]
    _require_item(ws, item_id)
    before = ws.load_item(item_id)
    item = uncheck_item(ws, item_id)
    if item != before:
        await _hub(request).notify_write(ws.root)
    return JSONResponse({"item": item.model_dump()})
