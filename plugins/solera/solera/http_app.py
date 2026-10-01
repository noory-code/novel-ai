"""Starlette application factory for Solera's HTTP and WebSocket engine."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import BaseRoute, Route, WebSocketRoute
from starlette.websockets import WebSocket, WebSocketDisconnect

from .auth import WS_TOKEN_PARAM, AuthMiddleware, check_ws_token
from .broadcast import BroadcastHub
from .http_endpoints import (
    HttpError,
    _project_path,
    add_after_endpoint,
    create_item_endpoint,
    health_endpoint,
    move_item_endpoint,
    patch_item_endpoint,
    remove_after_endpoint,
    work_by_slugs_endpoint,
    work_endpoint,
)


def create_http_app(hub: BroadcastHub | None = None) -> Starlette:
    """Build the localhost API with an injectable broadcast hub for tests."""
    target_hub = hub if hub is not None else BroadcastHub()

    async def websocket_endpoint(socket: WebSocket) -> None:
        await socket.accept()
        if not check_ws_token(socket.query_params.get(WS_TOKEN_PARAM)):
            await socket.close(code=1008, reason="invalid auth token")
            return
        try:
            project_path = _project_path(socket.query_params.get("project_path"))
        except HttpError as exc:
            await socket.close(code=1008, reason=exc.message)
            return
        workspace_root = project_path / ".noory" / "solera"
        await target_hub.subscribe(socket, workspace_root)
        try:
            while True:
                await socket.receive_text()
        except WebSocketDisconnect:
            pass
        finally:
            await target_hub.unsubscribe(socket, workspace_root)

    routes: list[BaseRoute] = [
        Route("/api/health", health_endpoint, methods=["GET"]),
        Route("/api/work", work_endpoint, methods=["GET"]),
        Route("/api/work/by-slugs", work_by_slugs_endpoint, methods=["POST"]),
        Route("/api/work/items", create_item_endpoint, methods=["POST"]),
        Route("/api/work/items/{id}", patch_item_endpoint, methods=["PATCH"]),
        Route("/api/work/items/{id}/move", move_item_endpoint, methods=["POST"]),
        Route("/api/work/items/{id}/after", add_after_endpoint, methods=["POST"]),
        Route(
            "/api/work/items/{id}/after/{predecessor}",
            remove_after_endpoint,
            methods=["DELETE"],
        ),
        WebSocketRoute("/ws", websocket_endpoint),
    ]
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        ),
        Middleware(AuthMiddleware),
    ]

    @asynccontextmanager
    async def lifespan(_app: Starlette) -> AsyncIterator[None]:
        yield
        await target_hub.shutdown()

    app = Starlette(routes=routes, middleware=middleware, lifespan=lifespan)
    app.state.hub = target_hub
    return app
