"""Chat HTTP endpoints and the provider-to-WebSocket streaming bridge.

``stream_chat_turn`` stays separate from the request handlers so streaming,
persistence, and in-progress scope tracking remain directly testable.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

from pydantic import ValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse

from mashbill.broadcast import BroadcastHub
from mashbill.chat_context import (
    build_context_preamble,
    build_framing_preamble,
    build_system_prompt,
)
from mashbill.chat_models import list_models
from mashbill.chat_output_filter import filter_save_announcements
from mashbill.chat_provider import read_selection
from mashbill.chat_providers.base import DEFAULT_CHAT_SCOPE, is_valid_scope
from mashbill.chat_selection import build_turn_preamble
from mashbill.chat_session import ChatProvider, ChatSessionRegistry, chat_registry
from mashbill.chat_store import (
    append_assistant_to_conversation,
    append_user,
    archive_current_conversation,
    current_conversation_id,
    list_conversations,
    read_conversation,
    read_conversation_by_id,
    read_recent_transcript,
    reopen_conversation,
    scope_to_filename,
)
from mashbill.chat_turn_state import finish_turn, start_turn, turn_in_progress
from mashbill.mcp_registration import ProviderName
from mashbill.workspace import enumerate_projects, resolve_plot_root

# Re-exported for back-compat — callers/tests historically import these two
# builders from this module; the SSOT now lives in ``chat_context`` so the MCP
# path can share them without importing the HTTP layer (D-2026-06-15-D).
__all__ = [
    "build_context_preamble",
    "build_framing_preamble",
    "chat_send_endpoint",
    "chat_reset_endpoint",
    "chat_models_endpoint",
    "chat_conversations_list_endpoint",
    "chat_conversation_get_endpoint",
    "chat_conversation_reopen_endpoint",
    "stream_chat_turn",
]


def _project_id_for(plot_root: Path) -> str | None:
    """The single project under a data root, or ``None`` (one-project-per-root,
    D-2026-06-21-AB). Used to key persisted conversations; ``None`` means there
    is nothing to persist against, so chat persistence quietly no-ops."""
    projects = enumerate_projects(plot_root)
    return projects[0].id if projects else None


# Runtime guard for the `provider` query param (ProviderName is a static
# Literal, so this is its runtime mirror).
_MODEL_PROVIDERS: frozenset[str] = frozenset({"claude-code", "codex"})


async def chat_models_endpoint(request: Request) -> JSONResponse:
    """``GET /api/chat/models?provider=<name>`` — the model catalogue for one
    provider (D-2026-06-22-B), pulled live from the CLI's own source
    (``agy models`` / codex cache) or the static claude aliases. Fail-soft: a
    bad / absent source yields ``{"models": []}`` so the selector falls back to
    its Custom… entry. Unknown / missing provider → 400.
    """
    raw = request.query_params.get("provider", "")
    if raw not in _MODEL_PROVIDERS:
        return JSONResponse({"error": f"unknown chat provider: {raw!r}"}, status_code=400)
    provider = cast(ProviderName, raw)
    # list_models may shell out (gemini → `agy models`) or read a file (codex
    # cache), so run it off the event loop.
    models = await asyncio.to_thread(list_models, provider)
    return JSONResponse({"models": [m.model_dump() for m in models]})


def _read_scope(body: dict[str, Any]) -> str | None:
    """Pull ``scope`` from a request body.

    Missing → the shared ``project`` bucket (Postel, Q1). Present but not a
    well-formed scope → ``None`` to signal the caller should 400 (Fail Fast on
    a typo before it silently creates an unreachable session). A valid scope is
    a base member or a parametric ``feature:<id>`` (Layer 1,
    D-2026-06-15-B), returned verbatim as the session key.
    """
    raw = body.get("scope")
    if raw is None:
        return DEFAULT_CHAT_SCOPE
    if isinstance(raw, str) and is_valid_scope(raw):
        return raw
    return None


_log = logging.getLogger(__name__)

# Event name carried on the WS payload. Viewer demultiplexes on ``event``;
# the existing project_changed payload uses ``"project_changed"``.
_CHAT_EVENT = "chat_stream_event"
_PERSIST_FAILED_EVENT = "chat_persist_failed"


def _hub_from_request(request: Request) -> BroadcastHub | None:
    hub = getattr(request.app.state, "broadcast_hub", None)
    return hub if isinstance(hub, BroadcastHub) else None


def _registry_from_request(request: Request) -> ChatSessionRegistry:
    reg = getattr(request.app.state, "chat_registry", None)
    if isinstance(reg, ChatSessionRegistry):
        return reg
    return chat_registry()


async def _notify_persist_failed(
    hub: BroadcastHub,
    plot_root: Path,
    project_id: str,
    scope: str,
    which: str,
) -> None:
    try:
        await hub.notify_event(
            plot_root,
            _PERSIST_FAILED_EVENT,
            {"project_id": project_id, "scope": scope, "which": which},
        )
    except Exception:  # noqa: BLE001 — notification must not affect chat
        _log.exception("chat persist failure notification failed for %s", plot_root)


async def stream_chat_turn(
    provider: ChatProvider,
    hub: BroadcastHub,
    plot_root: Path,
    user_message: str,
    scope: str = DEFAULT_CHAT_SCOPE,
    project_id: str | None = None,
    provider_name: str = "",
    model: str | None = None,
    conversation_id: str | None = None,
) -> None:
    """Fan provider events out to ``plot_root`` with the requested ``scope``.

    Errors become stream events. Assistant persistence is best-effort; completed
    turns never create drafts implicitly.
    """
    start_turn(plot_root, scope)
    try:
        async for event in filter_save_announcements(provider.stream_turn(user_message)):
            payload = event.model_dump()
            payload["scope"] = scope
            await hub.notify_event(plot_root, _CHAT_EVENT, payload)
            if event.type == "turn_complete" and project_id:
                try:
                    append_assistant_to_conversation(
                        plot_root,
                        project_id,
                        scope,
                        provider_name,
                        event.turn_id or f"turn_{uuid4().hex[:12]}",
                        event.text,
                        conversation_id,
                    )
                except Exception:  # noqa: BLE001 — persistence must not break chat
                    _log.exception("chat persist (assistant) failed for %s", plot_root)
                    await _notify_persist_failed(
                        hub,
                        plot_root,
                        project_id,
                        scope,
                        "assistant",
                    )
    except Exception as exc:  # noqa: BLE001 — boundary catch
        _log.exception("chat turn crashed for %s", plot_root)
        await hub.notify_event(
            plot_root,
            _CHAT_EVENT,
            {
                "type": "error",
                "turn_id": "",
                "error_message": f"chat turn crashed: {exc}",
                "scope": scope,
            },
        )
    finally:
        finish_turn(plot_root, scope)


async def chat_send_endpoint(request: Request) -> JSONResponse:
    """``POST /api/chat/send`` — schedule one assistant turn against the CLI.

    Body shape::

        {"project_path": "<absolute workspace path>", "message": "<user text>"}

    Returns ``202 {"accepted": true}`` once the background task is scheduled.
    The actual streamed assistant output arrives on the workspace's WS
    channel as ``chat_stream_event`` payloads.
    """
    try:
        body: dict[str, Any] = await request.json()
    except ValueError:
        return JSONResponse({"error": "invalid JSON body"}, status_code=400)

    project_path = body.get("project_path")
    message = body.get("message")
    if not isinstance(project_path, str) or not project_path:
        return JSONResponse({"error": "project_path required"}, status_code=400)
    if not isinstance(message, str) or not message.strip():
        return JSONResponse({"error": "message required"}, status_code=400)

    scope = _read_scope(body)
    if scope is None:
        return JSONResponse({"error": "invalid chat scope"}, status_code=400)

    try:
        plot_root = resolve_plot_root(project_path)
    except (FileNotFoundError, NotADirectoryError) as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)

    # The workspace's persisted CLI choice drives which provider runs the
    # turn. Without a choice the dock should be in its "pick a CLI" state
    # anyway — surface a 400 so a misbehaving viewer can't silently spawn a
    # default we never agreed on.
    selection = read_selection(plot_root)
    if selection.provider is None:
        return JSONResponse({"error": "no chat provider selected"}, status_code=400)
    # claude-code is allowed for in-app chat (D-2026-06-14-B, reversing
    # D-2026-06-13-H). Running it via ``claude -p`` bills separately from the
    # Claude subscription; that tradeoff is surfaced as a UI warning rather
    # than a hard server-side block, so the user opts in with eyes open.

    hub = _hub_from_request(request)
    if hub is None:
        return JSONResponse({"error": "broadcast hub not configured"}, status_code=500)

    registry = _registry_from_request(request)
    provider = registry.get_or_create(plot_root, selection.provider, scope)
    # Apply the workspace's model override (D-2026-06-16-C) before the turn —
    # ``None`` / empty leaves the CLI on its own configured default.
    provider.set_model(selection.model)
    # Lever 2 (docs/idea/chat/01-levers.md) — the Layer-3 framing + hallucination
    # guard go to the CLI as an authoritative system prompt, not glued into the
    # user message. The provider maps it per CLI (claude flag / codex prepend).
    provider.set_system_prompt(build_system_prompt(scope))
    provider.set_chat_scope(scope)

    # Layer 2 user-message context comes from the single context-provider seam
    # (D-2026-06-17-L, D-2026-08-18-E): current Foundation → active-canvas map →
    # cross-canvas registry → selected-node detail, all read engine-side. Even
    # project scope receives the current Foundation; the user's text follows.
    selection_nodes = body.get("selection")
    # ``project_path`` rides into the preamble so the agent gets the exact ids
    # ``update_node`` needs to save a confirmed change into the selected node
    # (D-2026-06-26-D) — the in-app agent's MCP server is stateless and never
    # otherwise learns the open project's path.
    preamble = build_turn_preamble(plot_root, scope, selection_nodes, project_path=project_path)

    project_id = _project_id_for(plot_root)
    # D-2026-06-26-F — re-feed the saved transcript on a FRESH CLI session. An app
    # / engine restart wipes the in-memory session registry, so the next turn's
    # coach starts with zero memory and re-asks what was already decided (and, with
    # nothing concrete to write, fabricates a save). Resume keeps memory within a
    # live session, so only the first turn of a fresh provider needs the history.
    history = ""
    if project_id is not None and provider.is_first_turn:
        history = read_recent_transcript(plot_root, project_id, scope)
    full_message = "\n\n".join(p for p in (history, preamble, message) if p)

    # Persist the user's turn before scheduling (D-2026-06-26-B) — the raw
    # ``message`` (not the context-injected ``full_message``), engine-side so it
    # survives a viewer crash. Best-effort: a write failure never blocks the turn.
    conversation_id = None
    if project_id is not None:
        try:
            append_user(
                plot_root,
                project_id,
                scope,
                selection.provider,
                f"user_{uuid4().hex[:12]}",
                message,
            )
            conversation_id = current_conversation_id(plot_root, project_id, scope)
        except Exception:  # noqa: BLE001 — persistence must not break chat
            _log.exception("chat persist (user) failed for %s", plot_root)
            await _notify_persist_failed(hub, plot_root, project_id, scope, "user")

    asyncio.create_task(
        stream_chat_turn(
            provider,
            hub,
            plot_root,
            full_message,
            scope,
            project_id,
            selection.provider,
            selection.model,
            conversation_id=conversation_id,
        )
    )
    return JSONResponse({"accepted": True}, status_code=202)


async def chat_conversations_list_endpoint(request: Request) -> JSONResponse:
    """``GET /api/chat/conversations?project_path=…`` — saved conversations as
    metadata rows, newest-updated first (D-2026-06-26-B). Empty list when the
    project has no saved chat yet."""
    project_path = request.query_params.get("project_path", "")
    if not project_path:
        return JSONResponse({"error": "project_path required"}, status_code=400)
    try:
        plot_root = resolve_plot_root(project_path, create=False)
    except (FileNotFoundError, NotADirectoryError) as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    project_id = _project_id_for(plot_root)
    rows = list_conversations(plot_root, project_id) if project_id is not None else []
    return JSONResponse({"conversations": rows})


async def chat_conversation_get_endpoint(request: Request) -> JSONResponse:
    """Read one current conversation by scope or any conversation by list-row id."""
    project_path = request.query_params.get("project_path", "")
    conversation_ref = request.path_params.get("conversation_ref", "")
    if not project_path:
        return JSONResponse({"error": "project_path required"}, status_code=400)
    if not is_valid_scope(conversation_ref) and not conversation_ref.endswith(".json"):
        return JSONResponse({"error": "invalid chat scope"}, status_code=400)
    if not is_valid_scope(conversation_ref) and (
        "/" in conversation_ref or "\\" in conversation_ref or ".." in conversation_ref
    ):
        return JSONResponse({"error": "invalid conversation id"}, status_code=400)
    try:
        plot_root = resolve_plot_root(project_path, create=False)
    except (FileNotFoundError, NotADirectoryError) as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    project_id = _project_id_for(plot_root)
    if project_id is None:
        return JSONResponse({"error": "conversation not found"}, status_code=404)
    try:
        if is_valid_scope(conversation_ref):
            doc = read_conversation(plot_root, project_id, conversation_ref)
        else:
            doc = read_conversation_by_id(plot_root, project_id, conversation_ref)
    except (FileNotFoundError, json.JSONDecodeError, ValidationError):
        return JSONResponse({"error": "conversation not found"}, status_code=404)
    except ValueError:
        return JSONResponse({"error": "invalid conversation id"}, status_code=400)
    return JSONResponse(doc.model_dump())


async def chat_conversation_reopen_endpoint(request: Request) -> JSONResponse:
    """``POST /api/chat/conversations/reopen`` — continue an ended conversation."""
    try:
        body: dict[str, Any] = await request.json()
    except ValueError:
        return JSONResponse({"error": "invalid JSON body"}, status_code=400)
    project_path = body.get("project_path")
    conversation_id = body.get("id")
    if not isinstance(project_path, str) or not project_path:
        return JSONResponse({"error": "project_path required"}, status_code=400)
    if not isinstance(conversation_id, str) or not conversation_id:
        return JSONResponse({"error": "id required"}, status_code=400)
    try:
        plot_root = resolve_plot_root(project_path, create=False)
    except (FileNotFoundError, NotADirectoryError) as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    project_id = _project_id_for(plot_root)
    if project_id is None:
        return JSONResponse({"error": "conversation not found"}, status_code=404)
    try:
        doc = read_conversation_by_id(plot_root, project_id, conversation_id)
    except (FileNotFoundError, json.JSONDecodeError, ValidationError):
        return JSONResponse({"error": "conversation not found"}, status_code=404)
    except ValueError:
        return JSONResponse({"error": "invalid conversation id"}, status_code=400)
    if turn_in_progress(plot_root, doc.scope):
        return JSONResponse(
            {"error": "turn in progress", "code": "turn_in_progress"}, status_code=409
        )
    try:
        doc = reopen_conversation(plot_root, project_id, conversation_id)
    except (FileNotFoundError, json.JSONDecodeError, ValidationError):
        return JSONResponse({"error": "conversation not found"}, status_code=404)
    except ValueError:
        return JSONResponse({"error": "invalid conversation id"}, status_code=400)
    registry = _registry_from_request(request)
    registry.reset(plot_root, scope=doc.scope)
    return JSONResponse(
        {
            "reopened": True,
            "id": scope_to_filename(doc.scope),
            "scope": doc.scope,
        }
    )


async def chat_reset_endpoint(request: Request) -> JSONResponse:
    """End the current conversation and drop its cached CLI session."""
    try:
        body: dict[str, Any] = await request.json()
    except ValueError:
        return JSONResponse({"error": "invalid JSON body"}, status_code=400)
    project_path = body.get("project_path")
    if not isinstance(project_path, str) or not project_path:
        return JSONResponse({"error": "project_path required"}, status_code=400)
    scope = _read_scope(body)
    if scope is None:
        return JSONResponse({"error": "invalid chat scope"}, status_code=400)
    try:
        plot_root = resolve_plot_root(project_path)
    except (FileNotFoundError, NotADirectoryError) as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    if turn_in_progress(plot_root, scope):
        return JSONResponse(
            {"error": "turn in progress", "code": "turn_in_progress"}, status_code=409
        )
    registry = _registry_from_request(request)
    project_id = _project_id_for(plot_root)
    if project_id is not None:
        archive_current_conversation(plot_root, project_id, scope)
    # Wipe only the active canvas thread across all providers (Q3); other
    # scopes' conversations survive.
    registry.reset(plot_root, scope=scope)
    return JSONResponse({"reset": True})
