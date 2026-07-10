"""Starlette app composition — routes + WebSocket + static viewer."""

from __future__ import annotations

import logging
import os

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import BaseRoute, Mount, Route, WebSocketRoute
from starlette.staticfiles import StaticFiles
from starlette.websockets import WebSocket, WebSocketDisconnect

from mashbill.api_endpoints import (
    canvas_get_endpoint,
    canvas_put_endpoint,
    dir_create_endpoint,
    dir_tree_endpoint,
    entity_usage_endpoint,
    file_get_endpoint,
    file_put_endpoint,
    file_raw_endpoint,
    folder_post_endpoint,
    format_f_service_publish_endpoint,
    format_f_snapshot_endpoint,
    health_endpoint,
    master_create_endpoint,
    project_anchor_patch_endpoint,
    project_at_tag_endpoint,
    project_delete_endpoint,
    project_get_endpoint,
    project_patch_endpoint,
    project_post_endpoint,
    project_publish_endpoint,
    projects_list_endpoint,
    tag_delete_endpoint,
    tag_post_endpoint,
    tags_list_endpoint,
    workspace_discover_endpoint,
    workspace_git_init_endpoint,
)
from mashbill.auth import WS_TOKEN_PARAM, AuthMiddleware, check_ws_token, configured_token
from mashbill.broadcast import BroadcastHub
from mashbill.chat_session import ChatSessionRegistry, chat_registry
from mashbill.debug_endpoints import debug_get_endpoint, debug_post_endpoint
from mashbill.endpoints_chat import (
    chat_conversation_get_endpoint,
    chat_conversations_list_endpoint,
    chat_models_endpoint,
    chat_reset_endpoint,
    chat_send_endpoint,
)
from mashbill.endpoints_mcp import (
    chat_provider_get_endpoint,
    chat_provider_put_endpoint,
    mcp_providers_endpoint,
    mcp_register_endpoint,
    mcp_unregister_endpoint,
)
from mashbill.endpoints_viewer import viewer_context_endpoint
from mashbill.workspace import find_viewer_dist, resolve_plot_root

_log = logging.getLogger(__name__)


def create_http_app(
    hub: BroadcastHub | None = None,
    chat_registry_instance: ChatSessionRegistry | None = None,
) -> Starlette:
    """Build the Starlette application exposing the browser-facing API.

    ``chat_registry_instance`` lets tests inject a registry whose factory
    returns a fake :class:`ChatProvider`; production paths leave it ``None``
    and the module-level singleton is used.
    """
    target_hub = hub if hub is not None else BroadcastHub()
    target_registry = (
        chat_registry_instance if chat_registry_instance is not None else chat_registry()
    )

    async def ws_endpoint(ws: WebSocket) -> None:
        await ws.accept()
        # D-2026-06-12-F — same env-gated rule as the HTTP middleware. When
        # ``MASHBILL_AUTH_TOKEN`` is unset (dev), any client may subscribe; when
        # set (bundled Tauri / future remote), the viewer attaches
        # ``?auth=<token>`` and a missing / wrong value closes the socket.
        presented = ws.query_params.get(WS_TOKEN_PARAM)
        if not check_ws_token(presented):
            await ws.close(code=1008, reason="auth token required")
            return
        project_path = ws.query_params.get("project_path")
        if not project_path:
            await ws.close(code=1008, reason="project_path query param required")
            return
        try:
            plot_root = resolve_plot_root(project_path)
        except (FileNotFoundError, NotADirectoryError) as exc:
            await ws.close(code=1008, reason=str(exc))
            return
        await target_hub.subscribe(ws, plot_root)
        try:
            while True:
                await ws.receive_text()
        except WebSocketDisconnect:
            pass
        finally:
            await target_hub.unsubscribe(ws, plot_root)

    routes: list[BaseRoute] = [
        Route("/api/health", health_endpoint),
        # v0.4 project + canvas + tag surface
        Route("/api/projects", projects_list_endpoint, methods=["GET"]),
        Route("/api/projects", project_post_endpoint, methods=["POST"]),
        # v0.32.0 — recursive workspace discovery + dir-tree picker
        Route("/api/workspace/projects", workspace_discover_endpoint, methods=["GET"]),
        Route("/api/workspace/tree", dir_tree_endpoint, methods=["GET"]),
        Route("/api/workspace/dir", dir_create_endpoint, methods=["POST"]),
        # D-2026-06-11-D — explicit user consent to `git init` at the workspace
        Route("/api/workspace/git-init", workspace_git_init_endpoint, methods=["POST"]),
        # Track 2.5 (D-2026-06-11-E) — register mashbill MCP server with external CLIs
        Route("/api/mcp/providers", mcp_providers_endpoint, methods=["GET"]),
        Route(
            "/api/mcp/providers/{provider}/register",
            mcp_register_endpoint,
            methods=["POST"],
        ),
        Route(
            "/api/mcp/providers/{provider}/unregister",
            mcp_unregister_endpoint,
            methods=["POST"],
        ),
        # D-2026-06-11-E Phase B step B3 — workspace-scoped chat-CLI choice
        Route("/api/chat/provider", chat_provider_get_endpoint, methods=["GET"]),
        Route("/api/chat/provider", chat_provider_put_endpoint, methods=["PUT"]),
        # D-2026-06-12-D Phase C — subprocess streaming (POST schedules a
        # turn; the assistant output arrives on the workspace WS as
        # ``chat_stream_event`` payloads).
        Route("/api/chat/models", chat_models_endpoint, methods=["GET"]),
        Route("/api/chat/send", chat_send_endpoint, methods=["POST"]),
        Route("/api/chat/reset", chat_reset_endpoint, methods=["POST"]),
        # Persisted conversations (D-2026-06-26-B) — list + reopen one.
        Route(
            "/api/chat/conversations",
            chat_conversations_list_endpoint,
            methods=["GET"],
        ),
        Route(
            "/api/chat/conversations/{scope}",
            chat_conversation_get_endpoint,
            methods=["GET"],
        ),
        Route("/api/viewer/context", viewer_context_endpoint, methods=["POST"]),
        Route("/api/projects/{project_id}", project_get_endpoint, methods=["GET"]),
        Route(
            "/api/projects/{project_id}",
            project_patch_endpoint,
            methods=["PATCH"],
        ),
        Route(
            "/api/projects/{project_id}",
            project_delete_endpoint,
            methods=["DELETE"],
        ),
        # v0.13 Phase 0 — anchor placement per canvas
        Route(
            "/api/projects/{project_id}/anchors/{canvas}",
            project_anchor_patch_endpoint,
            methods=["PATCH"],
        ),
        Route(
            "/api/projects/{project_id}/canvases/{kind}",
            canvas_get_endpoint,
            methods=["GET"],
        ),
        Route(
            "/api/projects/{project_id}/canvases/{kind}",
            canvas_put_endpoint,
            methods=["PUT"],
        ),
        Route(
            "/api/projects/{project_id}/entities/{entity_id}/usage",
            entity_usage_endpoint,
            methods=["GET"],
        ),
        Route(
            "/api/projects/{project_id}/masters",
            master_create_endpoint,
            methods=["POST"],
        ),
        # v0.7 file + folder surface (for Inspector MD editor)
        Route("/api/files", file_get_endpoint, methods=["GET"]),
        Route("/api/files", file_put_endpoint, methods=["PUT"]),
        # v0.24.0 (D-2026-05-17-L) — raw image bytes for Live Preview embeds
        Route("/api/files/raw", file_raw_endpoint, methods=["GET"]),
        Route("/api/folders", folder_post_endpoint, methods=["POST"]),
        Route(
            "/api/projects/{project_id}/tags",
            tags_list_endpoint,
            methods=["GET"],
        ),
        Route(
            "/api/projects/{project_id}/tags",
            tag_post_endpoint,
            methods=["POST"],
        ),
        Route(
            "/api/projects/{project_id}/tags/{tag_name}",
            tag_delete_endpoint,
            methods=["DELETE"],
        ),
        # v0.24.13 (D-2026-05-21-B) — project-level blueprint publish.
        # Replaces "세션 기록" UX with semver bump (major/minor/patch).
        Route(
            "/api/projects/{project_id}/publish",
            project_publish_endpoint,
            methods=["POST"],
        ),
        # v0.24.14 (D-2026-05-21-C) — read-only snapshot at git tag.
        Route(
            "/api/projects/{project_id}/at-tag/{tag}",
            project_at_tag_endpoint,
            methods=["GET"],
        ),
        # format F publish over HTTP (INT-g, D-2026-06-22-G) — vP snapshot +
        # vS service release, mirroring the MCP tools for the viewer surface.
        Route(
            "/api/projects/{project_id}/publish/snapshot",
            format_f_snapshot_endpoint,
            methods=["POST"],
        ),
        Route(
            "/api/projects/{project_id}/services/{service_id}/publish",
            format_f_service_publish_endpoint,
            methods=["POST"],
        ),
        WebSocketRoute("/ws", ws_endpoint),
    ]
    # v0.55.0 (D-2026-06-09-D / flavor gating) — the debug channel exists ONLY
    # in the debug flavor: the shell's debug build spawns the sidecar with
    # MASHBILL_DEBUG=1. Release builds never register the surface (404).
    if os.environ.get("MASHBILL_DEBUG") == "1":
        routes.append(Route("/api/debug", debug_get_endpoint, methods=["GET"]))
        routes.append(Route("/api/debug", debug_post_endpoint, methods=["POST"]))
    viewer_dist = find_viewer_dist()
    if viewer_dist is not None:
        routes.append(Mount("/", app=StaticFiles(directory=viewer_dist, html=True)))
    else:
        _log.info("viewer dist not found; HTTP server will only expose /api and /ws")

    # The engine binds 127.0.0.1 only; a bundled desktop frontend (Tauri,
    # origin tauri://localhost) calls it cross-origin, so allow any origin for
    # the local API. Auth/token hardening is a separate follow-up.
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )
    ]
    # D-2026-06-12-F — auth middleware sits ABOVE CORS so a preflight that
    # passes CORS still has to satisfy the token check. The middleware is
    # only mounted when ``MASHBILL_AUTH_TOKEN`` is set; the dev path stays
    # latency-identical to v0.64.x.
    if configured_token() is not None:
        middleware.append(Middleware(AuthMiddleware))
    app = Starlette(routes=routes, middleware=middleware)
    app.state.hub = target_hub
    app.state.broadcast_hub = target_hub
    app.state.chat_registry = target_registry
    return app
