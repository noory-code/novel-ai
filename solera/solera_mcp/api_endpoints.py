"""Basic Starlette HTTP endpoints backing the browser viewer.

Endpoints served here:

- ``GET    /api/health``
- ``GET    /api/graph``
- ``GET    /api/layout``
- ``PUT    /api/layout``
- ``POST   /api/{kind}``                   create an entity (kind ∈ role,
                                            persona, journey, narrative,
                                            concept)
- ``PATCH  /api/{kind}/{id}``              update one or more fields

The ``POST /api/concept/propose-from-narrative`` endpoint lives in
:mod:`solera_mcp.concept_propose` because it ships a lot of Moment-1
rule enforcement and its own helpers.

This module stays framework-only: writers live in
:mod:`solera_mcp.writers`, per-entity cross-ref rules live here, and
the HTTP app composition is in :mod:`solera_mcp.http_app`.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse

from solera_mcp.graph import Graph, build_graph, read_layout, write_layout
from solera_mcp.workspace import resolve_solera_root
from solera_mcp.writers import (
    create_concept,
    create_journey,
    create_narrative,
    create_persona,
    create_role,
    update_concept,
    update_journey,
    update_narrative,
    update_persona,
    update_role,
)


def graph_for(project_path: str) -> Graph:
    """Resolve the Solera root and build a typed graph. Raises ``FileNotFoundError``."""
    workspace = resolve_solera_root(project_path)
    return build_graph(workspace)


# ---------------------------------------------------------------------------
# Core read endpoints
# ---------------------------------------------------------------------------


async def graph_endpoint(request: Request) -> JSONResponse:
    project_path = request.query_params.get("project_path")
    if not project_path:
        return JSONResponse({"error": "project_path query param is required"}, status_code=400)
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
        return JSONResponse({"error": "project_path query param is required"}, status_code=400)
    try:
        workspace = resolve_solera_root(project_path)
    except FileNotFoundError as exc:
        return JSONResponse({"error": str(exc)}, status_code=404)
    return JSONResponse(read_layout(workspace))


async def layout_put_endpoint(request: Request) -> JSONResponse:
    project_path = request.query_params.get("project_path")
    if not project_path:
        return JSONResponse({"error": "project_path query param is required"}, status_code=400)
    try:
        workspace = resolve_solera_root(project_path)
    except FileNotFoundError as exc:
        return JSONResponse({"error": str(exc)}, status_code=404)
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"error": "invalid JSON body"}, status_code=400)
    if not isinstance(payload, dict):
        return JSONResponse({"error": "layout body must be an object"}, status_code=400)
    write_layout(workspace, payload)
    return JSONResponse({"ok": True})


# ---------------------------------------------------------------------------
# Shared request helpers
# ---------------------------------------------------------------------------


_VALID_KEBAB_RE = re.compile(r"^[a-z][a-z0-9-]{0,62}[a-z0-9]$")


def _err(message: str, status: int) -> JSONResponse:
    return JSONResponse({"error": message}, status_code=status)


async def _workspace_from_request(request: Request) -> Path | JSONResponse:
    project_path = request.query_params.get("project_path")
    if not project_path:
        return _err("project_path query param is required", 400)
    try:
        return resolve_solera_root(project_path)
    except FileNotFoundError as exc:
        return _err(str(exc), 404)


async def _json_body(request: Request) -> dict[str, Any] | JSONResponse:
    try:
        payload = await request.json()
    except Exception:
        return _err("invalid JSON body", 400)
    if not isinstance(payload, dict):
        return _err("body must be an object", 400)
    return payload


def _reject_disallowed(payload: dict[str, Any], allowed: frozenset[str]) -> JSONResponse | None:
    disallowed = set(payload.keys()) - allowed
    if disallowed:
        return _err(f"fields not allowed: {sorted(disallowed)}", 400)
    return None


def _allowed_status(value: Any) -> bool:
    return value in ("active", "deprecated", "archived")


# ---------------------------------------------------------------------------
# Per-kind file / dir configuration
# ---------------------------------------------------------------------------


_KIND_DIR = {
    "role": "roles",
    "persona": "personas",
    "journey": "journeys",
    "narrative": "narratives",
    "concept": "concepts",
}


def _entity_path(workspace: Path, kind: str, entity_id: str) -> Path:
    return workspace / _KIND_DIR[kind] / f"{entity_id}.md"


# ---------------------------------------------------------------------------
# Allowed-key sets per kind
# ---------------------------------------------------------------------------

ROLE_PATCH_ALLOWED: frozenset[str] = frozenset(
    {"name", "status", "description", "context", "parent"}
)
PERSONA_PATCH_ALLOWED: frozenset[str] = frozenset(
    {
        "name",
        "status",
        "role",
        "identity",
        "goals",
        "pains",
        "triggers",
        "quotes",
        "channels",
        "parent",
    }
)
JOURNEY_PATCH_ALLOWED: frozenset[str] = frozenset(
    {"name", "status", "walks", "walked_by", "trigger", "steps", "outcome", "parent"}
)
NARRATIVE_PATCH_ALLOWED: frozenset[str] = frozenset(
    {
        "name",
        "status",
        "form",
        "statement",
        "context",
        "acceptance_cues",
        "about_roles",
        "about_personas",
        "in_journey",
        "proposes",
    }
)
CONCEPT_PATCH_ALLOWED: frozenset[str] = frozenset(
    {"name", "status", "intent", "current_design", "current_shape", "horizon", "parent"}
)


# ---------------------------------------------------------------------------
# Cross-ref validators — each returns an error JSONResponse or None
# ---------------------------------------------------------------------------


def _validate_role_patch(
    workspace: Path, role_id: str, patch: dict[str, Any]
) -> JSONResponse | None:
    if "status" in patch and not _allowed_status(patch["status"]):
        return _err("status must be active | deprecated | archived", 400)
    if "parent" in patch:
        parent = patch["parent"]
        if parent is None:
            return None
        if not isinstance(parent, str):
            return _err("parent must be a Role id string or null", 400)
        if parent == role_id:
            return _err("Role cannot be its own parent", 400)
        if not _entity_path(workspace, "role", parent).exists():
            return _err(f"parent Role '{parent}' not found", 400)
        if _would_role_parent_cycle(workspace, role_id, parent):
            return _err("that parent would create a cycle", 400)
    return None


def _validate_persona_patch(
    workspace: Path, _persona_id: str, patch: dict[str, Any]
) -> JSONResponse | None:
    if "status" in patch and not _allowed_status(patch["status"]):
        return _err("status must be active | deprecated | archived", 400)
    if "role" in patch:
        role = patch["role"]
        if not isinstance(role, str) or not role:
            return _err("role is required and must be a non-empty string", 400)
        if not _entity_path(workspace, "role", role).exists():
            return _err(f"Role '{role}' not found", 400)
    return None


def _validate_journey_patch(
    workspace: Path, _journey_id: str, patch: dict[str, Any]
) -> JSONResponse | None:
    if "status" in patch and not _allowed_status(patch["status"]):
        return _err("status must be active | deprecated | archived", 400)
    if "walks" in patch:
        walks = patch["walks"]
        if not isinstance(walks, str) or not walks:
            return _err("walks is required and must be a Role id", 400)
        if not _entity_path(workspace, "role", walks).exists():
            return _err(f"walks Role '{walks}' not found", 400)
    if "walked_by" in patch:
        walked_by = patch["walked_by"]
        if not isinstance(walked_by, list):
            return _err("walked_by must be a list of Persona ids", 400)
        for pid in walked_by:
            if not isinstance(pid, str):
                return _err("walked_by entries must be strings", 400)
            if not _entity_path(workspace, "persona", pid).exists():
                return _err(f"walked_by Persona '{pid}' not found", 400)
    return None


def _validate_narrative_patch(
    workspace: Path, _narrative_id: str, patch: dict[str, Any]
) -> JSONResponse | None:
    if "status" in patch and not _allowed_status(patch["status"]):
        return _err("status must be active | deprecated | archived", 400)
    if "form" in patch and patch["form"] not in ("user_story", "jtbd", "scenario"):
        return _err("form must be user_story | jtbd | scenario", 400)
    if "about_roles" in patch:
        roles = patch["about_roles"]
        if not isinstance(roles, list) or not roles:
            return _err("about_roles must be a non-empty list", 400)
        for rid in roles:
            if not isinstance(rid, str):
                return _err("about_roles entries must be strings", 400)
            if not _entity_path(workspace, "role", rid).exists():
                return _err(f"about_roles Role '{rid}' not found", 400)
    if "about_personas" in patch:
        personas = patch["about_personas"]
        if not isinstance(personas, list):
            return _err("about_personas must be a list", 400)
        for pid in personas:
            if not isinstance(pid, str):
                return _err("about_personas entries must be strings", 400)
            if not _entity_path(workspace, "persona", pid).exists():
                return _err(f"about_personas Persona '{pid}' not found", 400)
    if "in_journey" in patch:
        journey = patch["in_journey"]
        if journey is None:
            return None
        if not isinstance(journey, str):
            return _err("in_journey must be a Journey id string or null", 400)
        if not _entity_path(workspace, "journey", journey).exists():
            return _err(f"in_journey Journey '{journey}' not found", 400)
    return None


def _validate_concept_patch(
    workspace: Path, concept_id: str, patch: dict[str, Any]
) -> JSONResponse | None:
    if "status" in patch and not _allowed_status(patch["status"]):
        return _err("status must be active | deprecated | archived", 400)
    if "parent" in patch:
        parent_val = patch["parent"]
        if parent_val is None:
            return None
        if not isinstance(parent_val, str):
            return _err("parent must be a Concept id string or null", 400)
        if parent_val == concept_id:
            return _err("Concept cannot be its own parent", 400)
        if not _entity_path(workspace, "concept", parent_val).exists():
            return _err(f"parent Concept '{parent_val}' not found", 400)
        if _would_concept_parent_cycle(workspace, concept_id, parent_val):
            return _err("that parent would create a cycle", 400)
    return None


# ---------------------------------------------------------------------------
# Cycle detection
# ---------------------------------------------------------------------------


def _would_concept_parent_cycle(workspace: Path, concept_id: str, proposed_parent: str) -> bool:
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


def _would_role_parent_cycle(workspace: Path, role_id: str, proposed_parent: str) -> bool:
    graph = build_graph(workspace)
    by_id = {r.id: r for r in graph.roles}
    current: str | None = proposed_parent
    seen: set[str] = set()
    while current is not None and current not in seen:
        if current == role_id:
            return True
        seen.add(current)
        role = by_id.get(current)
        current = role.parent if role else None
    return False


# Back-compat alias for the older concept cycle helper.
_would_create_cycle = _would_concept_parent_cycle


# ---------------------------------------------------------------------------
# Generic PATCH endpoint factory
# ---------------------------------------------------------------------------


def _make_patch_endpoint(
    kind: str,
    allowed: frozenset[str],
    validator: Callable[[Path, str, dict[str, Any]], JSONResponse | None],
    writer: Callable[[Path, dict[str, Any]], None],
    id_param: str,
) -> Callable[[Request], Any]:
    """Build a PATCH handler for a given entity kind.

    ``id_param`` is the path param name (e.g. ``role_id``).
    """

    async def handler(request: Request) -> JSONResponse:
        workspace_or_err = await _workspace_from_request(request)
        if isinstance(workspace_or_err, JSONResponse):
            return workspace_or_err
        workspace = workspace_or_err
        entity_id = request.path_params[id_param]
        target = _entity_path(workspace, kind, entity_id)
        if not target.exists():
            return _err(f"{kind.title()} '{entity_id}' not found", 404)
        payload_or_err = await _json_body(request)
        if isinstance(payload_or_err, JSONResponse):
            return payload_or_err
        payload = payload_or_err
        err = _reject_disallowed(payload, allowed)
        if err:
            return err
        if not payload:
            return _err("patch body is empty", 400)
        err = validator(workspace, entity_id, payload)
        if err:
            return err
        writer(target, payload)
        return JSONResponse({"ok": True})

    return handler


# ---------------------------------------------------------------------------
# POST endpoints (create)
# ---------------------------------------------------------------------------


def _validate_new_id(workspace: Path, kind: str, entity_id: Any) -> JSONResponse | None:
    if not isinstance(entity_id, str):
        return _err("id is required and must be a string", 400)
    if not _VALID_KEBAB_RE.match(entity_id):
        return _err(
            "id must be kebab-case: lowercase letters/digits/hyphens, "
            "starting with a letter, ending with letter/digit, length 2-64",
            400,
        )
    if _entity_path(workspace, kind, entity_id).exists():
        return _err(
            f"{kind.title()} '{entity_id}' already exists — use PATCH to update",
            409,
        )
    return None


async def role_post_endpoint(request: Request) -> JSONResponse:
    workspace_or_err = await _workspace_from_request(request)
    if isinstance(workspace_or_err, JSONResponse):
        return workspace_or_err
    workspace = workspace_or_err
    payload_or_err = await _json_body(request)
    if isinstance(payload_or_err, JSONResponse):
        return payload_or_err
    payload = payload_or_err
    id_err = _validate_new_id(workspace, "role", payload.get("id"))
    if id_err:
        return id_err
    role_id = payload["id"]
    v = _validate_role_patch(workspace, role_id, {k: v for k, v in payload.items() if k != "id"})
    if v:
        return v
    payload.setdefault("created", date.today().isoformat())
    path = create_role(workspace, payload)
    return JSONResponse(
        {"ok": True, "id": role_id, "path": str(path.relative_to(workspace.parent))}
    )


async def persona_post_endpoint(request: Request) -> JSONResponse:
    workspace_or_err = await _workspace_from_request(request)
    if isinstance(workspace_or_err, JSONResponse):
        return workspace_or_err
    workspace = workspace_or_err
    payload_or_err = await _json_body(request)
    if isinstance(payload_or_err, JSONResponse):
        return payload_or_err
    payload = payload_or_err
    id_err = _validate_new_id(workspace, "persona", payload.get("id"))
    if id_err:
        return id_err
    persona_id = payload["id"]
    if not isinstance(payload.get("role"), str) or not payload["role"]:
        return _err("role is required on create (the Role this Persona archetypes)", 400)
    v = _validate_persona_patch(
        workspace, persona_id, {k: v for k, v in payload.items() if k != "id"}
    )
    if v:
        return v
    payload.setdefault("created", date.today().isoformat())
    path = create_persona(workspace, payload)
    return JSONResponse(
        {"ok": True, "id": persona_id, "path": str(path.relative_to(workspace.parent))}
    )


async def journey_post_endpoint(request: Request) -> JSONResponse:
    workspace_or_err = await _workspace_from_request(request)
    if isinstance(workspace_or_err, JSONResponse):
        return workspace_or_err
    workspace = workspace_or_err
    payload_or_err = await _json_body(request)
    if isinstance(payload_or_err, JSONResponse):
        return payload_or_err
    payload = payload_or_err
    id_err = _validate_new_id(workspace, "journey", payload.get("id"))
    if id_err:
        return id_err
    journey_id = payload["id"]
    if not isinstance(payload.get("walks"), str) or not payload["walks"]:
        return _err("walks is required on create (the Role this Journey walks)", 400)
    v = _validate_journey_patch(
        workspace, journey_id, {k: v for k, v in payload.items() if k != "id"}
    )
    if v:
        return v
    payload.setdefault("created", date.today().isoformat())
    path = create_journey(workspace, payload)
    return JSONResponse(
        {"ok": True, "id": journey_id, "path": str(path.relative_to(workspace.parent))}
    )


async def narrative_post_endpoint(request: Request) -> JSONResponse:
    workspace_or_err = await _workspace_from_request(request)
    if isinstance(workspace_or_err, JSONResponse):
        return workspace_or_err
    workspace = workspace_or_err
    payload_or_err = await _json_body(request)
    if isinstance(payload_or_err, JSONResponse):
        return payload_or_err
    payload = payload_or_err
    id_err = _validate_new_id(workspace, "narrative", payload.get("id"))
    if id_err:
        return id_err
    narrative_id = payload["id"]
    if not isinstance(payload.get("about_roles"), list) or not payload["about_roles"]:
        return _err("about_roles is required on create (1+ active Role ids)", 400)
    v = _validate_narrative_patch(
        workspace, narrative_id, {k: v for k, v in payload.items() if k != "id"}
    )
    if v:
        return v
    payload.setdefault("created", date.today().isoformat())
    path = create_narrative(workspace, payload)
    return JSONResponse(
        {"ok": True, "id": narrative_id, "path": str(path.relative_to(workspace.parent))}
    )


async def concept_post_endpoint(request: Request) -> JSONResponse:
    workspace_or_err = await _workspace_from_request(request)
    if isinstance(workspace_or_err, JSONResponse):
        return workspace_or_err
    workspace = workspace_or_err
    payload_or_err = await _json_body(request)
    if isinstance(payload_or_err, JSONResponse):
        return payload_or_err
    payload = payload_or_err
    id_err = _validate_new_id(workspace, "concept", payload.get("id"))
    if id_err:
        return id_err
    concept_id = payload["id"]
    v = _validate_concept_patch(
        workspace, concept_id, {k: v for k, v in payload.items() if k != "id"}
    )
    if v:
        return v
    payload.setdefault("created", date.today().isoformat())
    path = create_concept(workspace, payload)
    return JSONResponse(
        {"ok": True, "id": concept_id, "path": str(path.relative_to(workspace.parent))}
    )


# ---------------------------------------------------------------------------
# PATCH endpoints (built via the factory)
# ---------------------------------------------------------------------------


role_patch_endpoint = _make_patch_endpoint(
    "role", ROLE_PATCH_ALLOWED, _validate_role_patch, update_role, "role_id"
)
persona_patch_endpoint = _make_patch_endpoint(
    "persona",
    PERSONA_PATCH_ALLOWED,
    _validate_persona_patch,
    update_persona,
    "persona_id",
)
journey_patch_endpoint = _make_patch_endpoint(
    "journey",
    JOURNEY_PATCH_ALLOWED,
    _validate_journey_patch,
    update_journey,
    "journey_id",
)
narrative_patch_endpoint = _make_patch_endpoint(
    "narrative",
    NARRATIVE_PATCH_ALLOWED,
    _validate_narrative_patch,
    update_narrative,
    "narrative_id",
)
concept_patch_endpoint = _make_patch_endpoint(
    "concept",
    CONCEPT_PATCH_ALLOWED,
    _validate_concept_patch,
    update_concept,
    "concept_id",
)
