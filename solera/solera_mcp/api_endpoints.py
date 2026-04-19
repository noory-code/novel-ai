"""Basic Starlette HTTP endpoints backing the browser viewer.

Endpoints served here:

- ``GET  /api/health``
- ``GET  /api/graph``
- ``GET  /api/layout``
- ``PUT  /api/layout``
- ``PATCH /api/concept/{concept_id}``

The ``POST /api/concept/propose-from-narrative`` endpoint lives in
:mod:`solera_mcp.concept_propose` because it ships a lot of Moment-1 rule
enforcement and its own helpers.
"""

from __future__ import annotations

from pathlib import Path

from starlette.requests import Request
from starlette.responses import JSONResponse

from solera_mcp.graph import (
    Graph,
    build_graph,
    read_layout,
    update_concept_frontmatter,
    write_layout,
)
from solera_mcp.workspace import resolve_solera_root


def graph_for(project_path: str) -> Graph:
    """Resolve the Solera root and build a typed graph. Raises ``FileNotFoundError``."""
    workspace = resolve_solera_root(project_path)
    return build_graph(workspace)


async def graph_endpoint(request: Request) -> JSONResponse:
    project_path = request.query_params.get("project_path")
    if not project_path:
        return JSONResponse(
            {"error": "project_path query param is required"}, status_code=400
        )
    try:
        graph = graph_for(project_path)
    except FileNotFoundError as exc:
        return JSONResponse({"error": str(exc)}, status_code=404)
    return JSONResponse(graph.model_dump(by_alias=True))


async def health_endpoint(_request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "solera-map"})


async def layout_get_endpoint(request: Request) -> JSONResponse:
    project_path = request.query_params.get("project_path")
    if not project_path:
        return JSONResponse(
            {"error": "project_path query param is required"}, status_code=400
        )
    try:
        workspace = resolve_solera_root(project_path)
    except FileNotFoundError as exc:
        return JSONResponse({"error": str(exc)}, status_code=404)
    return JSONResponse(read_layout(workspace))


async def layout_put_endpoint(request: Request) -> JSONResponse:
    project_path = request.query_params.get("project_path")
    if not project_path:
        return JSONResponse(
            {"error": "project_path query param is required"}, status_code=400
        )
    try:
        workspace = resolve_solera_root(project_path)
    except FileNotFoundError as exc:
        return JSONResponse({"error": str(exc)}, status_code=404)
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"error": "invalid JSON body"}, status_code=400)
    if not isinstance(payload, dict):
        return JSONResponse(
            {"error": "layout body must be an object"}, status_code=400
        )
    write_layout(workspace, payload)
    return JSONResponse({"ok": True})


_CONCEPT_PATCH_ALLOWED: frozenset[str] = frozenset({"parent"})


async def concept_patch_endpoint(request: Request) -> JSONResponse:
    project_path = request.query_params.get("project_path")
    concept_id = request.path_params["concept_id"]
    if not project_path:
        return JSONResponse(
            {"error": "project_path query param is required"}, status_code=400
        )
    try:
        workspace = resolve_solera_root(project_path)
    except FileNotFoundError as exc:
        return JSONResponse({"error": str(exc)}, status_code=404)

    target = workspace / "concepts" / f"{concept_id}.md"
    if not target.exists():
        return JSONResponse(
            {"error": f"Concept '{concept_id}' not found"}, status_code=404
        )

    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"error": "invalid JSON body"}, status_code=400)
    if not isinstance(payload, dict):
        return JSONResponse({"error": "patch body must be an object"}, status_code=400)

    disallowed = set(payload.keys()) - _CONCEPT_PATCH_ALLOWED
    if disallowed:
        return JSONResponse(
            {"error": f"fields not allowed: {sorted(disallowed)}"}, status_code=400
        )

    if "parent" in payload:
        parent_val = payload["parent"]
        if parent_val is not None and not isinstance(parent_val, str):
            return JSONResponse(
                {"error": "parent must be a Concept id string or null"},
                status_code=400,
            )
        if isinstance(parent_val, str):
            if parent_val == concept_id:
                return JSONResponse(
                    {"error": "Concept cannot be its own parent"}, status_code=400
                )
            parent_file = workspace / "concepts" / f"{parent_val}.md"
            if not parent_file.exists():
                return JSONResponse(
                    {"error": f"parent Concept '{parent_val}' not found"},
                    status_code=400,
                )
            if _would_create_cycle(workspace, concept_id, parent_val):
                return JSONResponse(
                    {"error": "that parent would create a cycle"}, status_code=400
                )

    update_concept_frontmatter(target, payload)
    return JSONResponse({"ok": True})


def _would_create_cycle(workspace: Path, concept_id: str, proposed_parent: str) -> bool:
    """Walk the chain from ``proposed_parent`` upward; fail if we hit ``concept_id``."""
    graph = build_graph(workspace)
    by_id = {c.id: c for c in graph.concepts}
    current: str | None = proposed_parent
    seen: set[str] = set()
    while current is not None and current not in seen:
        if current == concept_id:
            return True
        seen.add(current)
        parent = by_id.get(current)
        current = parent.parent if parent else None
    return False
