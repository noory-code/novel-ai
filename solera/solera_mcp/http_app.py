"""Starlette app composition — wires endpoints, WebSocket, and static viewer."""

from __future__ import annotations

import logging

from starlette.applications import Starlette
from starlette.routing import BaseRoute, Mount, Route, WebSocketRoute
from starlette.staticfiles import StaticFiles
from starlette.websockets import WebSocket, WebSocketDisconnect

from solera_mcp.api_endpoints import (
    concept_patch_endpoint,
    concept_post_endpoint,
    graph_endpoint,
    health_endpoint,
    journey_patch_endpoint,
    journey_post_endpoint,
    layout_get_endpoint,
    layout_put_endpoint,
    narrative_patch_endpoint,
    narrative_post_endpoint,
    persona_patch_endpoint,
    persona_post_endpoint,
    role_patch_endpoint,
    role_post_endpoint,
)
from solera_mcp.broadcast import BroadcastHub
from solera_mcp.concept_propose import concept_propose_from_narrative_endpoint
from solera_mcp.workspace import find_viewer_dist, resolve_solera_root

_log = logging.getLogger(__name__)


def create_http_app(hub: BroadcastHub | None = None) -> Starlette:
    """Build the Starlette application exposing the browser-facing API.

    If ``hub`` is omitted, a fresh ``BroadcastHub`` is created and attached
    to ``app.state.hub`` so callers (and tests) can reach it.
    """
    target_hub = hub if hub is not None else BroadcastHub()

    async def ws_endpoint(ws: WebSocket) -> None:
        await ws.accept()
        project_path = ws.query_params.get("project_path")
        if not project_path:
            await ws.close(code=1008, reason="project_path query param required")
            return
        try:
            workspace = resolve_solera_root(project_path)
        except FileNotFoundError as exc:
            await ws.close(code=1008, reason=str(exc))
            return
        await target_hub.subscribe(ws, workspace)
        try:
            while True:
                await ws.receive_text()
        except WebSocketDisconnect:
            pass
        finally:
            await target_hub.unsubscribe(ws, workspace)

    routes: list[BaseRoute] = [
        Route("/api/health", health_endpoint),
        Route("/api/graph", graph_endpoint),
        Route("/api/layout", layout_get_endpoint, methods=["GET"]),
        Route("/api/layout", layout_put_endpoint, methods=["PUT"]),
        # Keep the specialised propose-from-narrative route BEFORE the
        # generic `/api/concept` POST so Starlette's pattern matcher
        # doesn't route `propose-from-narrative` through concept_post.
        Route(
            "/api/concept/propose-from-narrative",
            concept_propose_from_narrative_endpoint,
            methods=["POST"],
        ),
        # v5.1: unified POST/PATCH surface for every Living-axis entity.
        Route("/api/role", role_post_endpoint, methods=["POST"]),
        Route("/api/role/{role_id}", role_patch_endpoint, methods=["PATCH"]),
        Route("/api/persona", persona_post_endpoint, methods=["POST"]),
        Route("/api/persona/{persona_id}", persona_patch_endpoint, methods=["PATCH"]),
        Route("/api/journey", journey_post_endpoint, methods=["POST"]),
        Route("/api/journey/{journey_id}", journey_patch_endpoint, methods=["PATCH"]),
        Route("/api/narrative", narrative_post_endpoint, methods=["POST"]),
        Route(
            "/api/narrative/{narrative_id}",
            narrative_patch_endpoint,
            methods=["PATCH"],
        ),
        Route("/api/concept", concept_post_endpoint, methods=["POST"]),
        Route(
            "/api/concept/{concept_id}",
            concept_patch_endpoint,
            methods=["PATCH"],
        ),
        WebSocketRoute("/ws", ws_endpoint),
    ]
    viewer_dist = find_viewer_dist()
    if viewer_dist is not None:
        # SPA: html=True also serves index.html when a path 404s, so client
        # routes resolve without additional wiring.
        routes.append(Mount("/", app=StaticFiles(directory=viewer_dist, html=True)))
    else:
        _log.info("viewer dist not found; HTTP server will only expose /api and /ws")

    app = Starlette(routes=routes)
    app.state.hub = target_hub
    return app
