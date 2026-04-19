"""Combined MCP (stdio) + HTTP (localhost) server for solera-map.

A single asyncio event loop hosts two transports side-by-side:

- FastMCP over stdio for Claude Code tool calls
- Starlette + uvicorn over http://127.0.0.1:{port} for the browser viewer

Both transports read the same `Graph` built by `solera_mcp.graph.build_graph`
against a Solera root directory supplied by the caller. The server holds no
process-wide project state — every request resolves its own `project_path`.

Solera root resolution (Solera v4 onwards):
- `.solera/` (the v4 location) is preferred.
- `workspace/` (the v3 location) is accepted with a deprecation warning for
  one minor version (solera-map v0.1.x). v0.2.0 will drop the fallback.

Port selection:
- Default 5170; override via `SOLERA_MAP_PORT`.
- If the port is in use, the HTTP server logs a warning and skips HTTP
  startup — the MCP transport remains usable so the plugin still works.
"""

from __future__ import annotations

import asyncio
import logging
import os
import socket
from pathlib import Path
from typing import Any

import uvicorn
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import BaseRoute, Mount, Route, WebSocketRoute
from starlette.staticfiles import StaticFiles
from starlette.websockets import WebSocket, WebSocketDisconnect

from solera_mcp.graph import (
    Graph,
    build_graph,
    read_layout,
    update_concept_frontmatter,
    write_layout,
)
from solera_mcp.watcher import WorkspaceWatcher

_log = logging.getLogger(__name__)

DEFAULT_HTTP_PORT = 5170


# ---------------------------------------------------------------------------
# Project path resolution
# ---------------------------------------------------------------------------


def resolve_solera_root(project_path: str) -> Path:
    """Resolve the Solera workspace root directory under a project path.

    Resolution order (Solera v4):
      1. `{project_path}/.solera/` — v4 location (preferred).
      2. `{project_path}/workspace/` — v3 location, accepted with a
         DeprecationWarning. To be removed in solera-map v0.2.0.
      3. `{project_path}/` itself — last-ditch fallback for callers that
         already point at the workspace dir (any name).

    A directory qualifies as a Solera workspace if it contains either
    `concepts/` or `identity/`. Raises `FileNotFoundError` otherwise.
    """
    base = Path(project_path).expanduser().resolve()
    candidates: list[tuple[Path, str | None]] = [
        (base / ".solera", None),
        (base / "workspace", "v3"),
        (base, None),
    ]
    for candidate, deprecation_label in candidates:
        if (candidate / "concepts").exists() or (candidate / "identity").exists():
            if deprecation_label == "v3":
                _log.warning(
                    "Reading from legacy %s layout at %s. Run "
                    "`solera-migrate-workspace-to-dotsolera` to relocate to .solera/. "
                    "solera-map v0.2.0 will drop this fallback.",
                    deprecation_label,
                    candidate,
                )
            return candidate
    raise FileNotFoundError(
        f"No Solera workspace found under {project_path!r} "
        "(looked for `.solera/`, `workspace/`, and bare directory)"
    )


# Deprecated alias kept for one minor version so external callers / tests
# updating in lockstep don't break. Internal call sites use
# `resolve_solera_root` directly.
resolve_workspace = resolve_solera_root


def _graph_for(project_path: str) -> Graph:
    workspace = resolve_solera_root(project_path)
    return build_graph(workspace)


# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "solera-map",
    instructions=(
        "solera-map exposes a Solera workspace as a typed graph of Concepts, "
        "Concept↔Concept edges, Milestones, Stories, Action Items, and Releases. "
        "Use `get_map(project_path)` to read the full graph. Future tools will "
        "propose edges and concepts before they are persisted."
    ),
)


@mcp.tool()
def get_map(project_path: str) -> dict[str, Any]:
    """Return the Solera workspace graph for `project_path` as a JSON-ready dict.

    Args:
        project_path: Project root containing `.solera/` (Solera v4) or
            `workspace/` (Solera v3, deprecated fallback). May also be the
            Solera root directory itself.
    """
    return _graph_for(project_path).model_dump(by_alias=True)


@mcp.tool()
def open_map(project_path: str) -> str:
    """Open the Solera Map viewer in the user's default browser.

    Invoked by the `/map` slash command. Validates that `project_path` is a
    readable Solera workspace before opening, so the browser never lands on
    a blank error page.
    """
    import webbrowser

    resolve_solera_root(project_path)  # raises if not a workspace
    port = _resolved_port()
    url = f"http://127.0.0.1:{port}/?project_path={project_path}"
    webbrowser.open(url)
    return f"Opened {url}"


# ---------------------------------------------------------------------------
# HTTP server
# ---------------------------------------------------------------------------


async def _graph_endpoint(request: Request) -> JSONResponse:
    project_path = request.query_params.get("project_path")
    if not project_path:
        return JSONResponse(
            {"error": "project_path query param is required"}, status_code=400
        )
    try:
        graph = _graph_for(project_path)
    except FileNotFoundError as exc:
        return JSONResponse({"error": str(exc)}, status_code=404)
    return JSONResponse(graph.model_dump(by_alias=True))


async def _health_endpoint(_request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "solera-map"})


async def _layout_get_endpoint(request: Request) -> JSONResponse:
    project_path = request.query_params.get("project_path")
    if not project_path:
        return JSONResponse(
            {"error": "project_path query param is required"}, status_code=400
        )
    try:
        workspace = resolve_workspace(project_path)
    except FileNotFoundError as exc:
        return JSONResponse({"error": str(exc)}, status_code=404)
    return JSONResponse(read_layout(workspace))


async def _layout_put_endpoint(request: Request) -> JSONResponse:
    project_path = request.query_params.get("project_path")
    if not project_path:
        return JSONResponse(
            {"error": "project_path query param is required"}, status_code=400
        )
    try:
        workspace = resolve_workspace(project_path)
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


async def _concept_patch_endpoint(request: Request) -> JSONResponse:
    project_path = request.query_params.get("project_path")
    concept_id = request.path_params["concept_id"]
    if not project_path:
        return JSONResponse(
            {"error": "project_path query param is required"}, status_code=400
        )
    try:
        workspace = resolve_workspace(project_path)
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


# ---------------------------------------------------------------------------
# POST /api/concept/propose-from-narrative
# ---------------------------------------------------------------------------
#
# Surfaces the Service canvas's "Propose as Concept" action ergonomically WITHOUT
# bypassing the Moment 1 collaboration rule (`solera/skills/solera-write-concept/
# SKILL.md:86-92` — "AI must not invent the Intent"). Behavior:
#
# 1. Validate the named Narrative exists.
# 2. Validate the proposed concept_id does NOT already exist (this endpoint
#    creates a stub; updates go through PATCH /api/concept/{id} or a direct
#    `solera-write-concept update` invocation).
# 3. Write a stub Concept whose `# Intent` is explicitly flagged
#    "needs human review per solera-write-concept Moment 1 rule" — the human
#    must run `solera-write-concept` in `update` mode to fill the real Intent.
# 4. Append the new concept_id to the Narrative's `proposes:` frontmatter.
# 5. Return the path of the new Concept file.
#
# What the endpoint does NOT do: finalize the Concept; copy the full Workflow
# section from concept-template.md (solera-map does not vendor solera plugin
# assets — the Workflow is added by `solera-write-concept update`); validate
# axes-and-status invariants beyond the create-vs-update distinction.

_VALID_KEBAB_RE = __import__("re").compile(r"^[a-z][a-z0-9-]{0,62}[a-z0-9]$")


def _stub_concept_body(narrative_id: str, today: str) -> str:
    """Body of a stub Concept created from a Narrative proposal.

    Intentionally MINIMAL. The `# Intent` is the Moment 1 guardrail — flagged
    "needs human review" so a casual reader cannot mistake it for a real
    Intent. The `## Workflow` section is INTENTIONALLY OMITTED here; running
    `solera-write-concept` in `update` mode will inject the canonical Workflow
    from solera's `concept-template.md`.
    """
    return (
        f"# Intent\n"
        f"(proposed from narrative `{narrative_id}` on {today} — "
        f"needs human review per solera-write-concept Moment 1 rule)\n"
        f"\n"
        f"# Current Design\n"
        f"\n"
        f"# Current Shape\n"
        f"(no Stories have contributed yet)\n"
        f"\n"
        f"# Horizon\n"
        f"(not set yet)\n"
        f"\n"
        f"# Health\n"
        f"(no signals yet)\n"
        f"\n"
        f"# Contributions\n"
        f"| Story | What it left behind | Date |\n"
        f"|-------|---------------------|------|\n"
        f"\n"
        f"# Related Artifacts\n"
        f"\n"
        f"# Proposed From Narratives\n"
        f"- [[narrative/{narrative_id}]]\n"
        f"\n"
        f"<!-- Stub created by solera-map propose-from-narrative on {today}.\n"
        f"     Run `solera-write-concept` in `update` mode to fill Intent and\n"
        f"     install the canonical ## Workflow section. -->\n"
    )


def _append_to_narrative_proposes(narrative_path: Path, concept_id: str) -> None:
    """Add `concept_id` to a Narrative's frontmatter `proposes:` list (idempotent).

    Reads the existing list (if any), appends if absent, rewrites the
    frontmatter while preserving body and key order. If the file lacks
    frontmatter, this is treated as an integrity violation — narrative
    files always have frontmatter — so we skip silently rather than corrupt.
    """
    from solera_mcp.graph import parse_frontmatter  # local import to avoid cycle clarity

    text = narrative_path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    if not fm:
        # Defensive: do not invent frontmatter for a malformed Narrative.
        return
    existing = fm.get("proposes") or []
    if isinstance(existing, str):
        existing = [existing]
    elif not isinstance(existing, list):
        existing = []
    if concept_id in existing:
        return
    existing.append(concept_id)
    fm["proposes"] = existing
    import yaml as _yaml

    dumped = _yaml.safe_dump(fm, allow_unicode=True, sort_keys=False).strip()
    narrative_path.write_text(f"---\n{dumped}\n---\n{body}", encoding="utf-8")


async def _concept_propose_from_narrative_endpoint(request: Request) -> JSONResponse:
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
        return JSONResponse({"error": "body must be an object"}, status_code=400)

    narrative_id = payload.get("narrative_id")
    concept_id = payload.get("concept_id")
    concept_name = payload.get("concept_name")

    for field, value in (
        ("narrative_id", narrative_id),
        ("concept_id", concept_id),
        ("concept_name", concept_name),
    ):
        if not isinstance(value, str) or not value.strip():
            return JSONResponse(
                {"error": f"{field} is required and must be a non-empty string"},
                status_code=400,
            )

    assert isinstance(concept_id, str)  # narrowed for mypy
    assert isinstance(narrative_id, str)
    assert isinstance(concept_name, str)

    if not _VALID_KEBAB_RE.match(concept_id):
        return JSONResponse(
            {
                "error": (
                    "concept_id must be kebab-case: lowercase letters/digits/hyphens, "
                    "starting with a letter, ending with letter/digit, length 2-64"
                )
            },
            status_code=400,
        )

    narrative_path = workspace / "narratives" / f"{narrative_id}.md"
    if not narrative_path.exists():
        return JSONResponse(
            {"error": f"Narrative '{narrative_id}' not found"}, status_code=404
        )

    concept_path = workspace / "concepts" / f"{concept_id}.md"
    if concept_path.exists():
        return JSONResponse(
            {
                "error": (
                    f"Concept '{concept_id}' already exists. Use a different id, or "
                    f"run `solera-write-concept` in update mode against the existing one."
                )
            },
            status_code=409,
        )

    from datetime import date

    today = date.today().isoformat()

    concept_path.parent.mkdir(parents=True, exist_ok=True)
    frontmatter = (
        f"---\n"
        f"id: {concept_id}\n"
        f"name: {concept_name}\n"
        f"status: active\n"
        f"created: {today}\n"
        f"---\n\n"
    )
    concept_path.write_text(
        frontmatter + _stub_concept_body(narrative_id, today), encoding="utf-8"
    )

    _append_to_narrative_proposes(narrative_path, concept_id)

    return JSONResponse(
        {
            "ok": True,
            "concept_path": str(concept_path.relative_to(workspace.parent)),
            "concept_id": concept_id,
            "needs_intent_review": True,
        }
    )


def _would_create_cycle(workspace: Path, concept_id: str, proposed_parent: str) -> bool:
    """Walk the chain from `proposed_parent` upward; fail if we hit `concept_id`."""
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


class BroadcastHub:
    """Fan-out between workspace watchers and connected WebSocket clients.

    One watcher per workspace, created on the first subscription and torn
    down when the last client for that workspace disconnects. Broadcasts
    are idempotent — `notify(workspace)` can be called directly (by tests
    or future MCP triggers) without a real filesystem event.

    Tests that don't want a real filesystem watcher may pass
    `enable_watchers=False`; subscriptions still work and `notify` remains
    the event source.
    """

    def __init__(self, *, enable_watchers: bool = True) -> None:
        self._subs: dict[Path, set[WebSocket]] = {}
        self._watchers: dict[Path, WorkspaceWatcher] = {}
        self._lock = asyncio.Lock()
        self._enable_watchers = enable_watchers

    async def subscribe(self, ws: WebSocket, workspace: Path) -> None:
        async with self._lock:
            if workspace not in self._subs:
                self._subs[workspace] = set()
                if self._enable_watchers:
                    self._watchers[workspace] = self._start_watcher(workspace)
            self._subs[workspace].add(ws)

    async def unsubscribe(self, ws: WebSocket, workspace: Path) -> None:
        async with self._lock:
            subs = self._subs.get(workspace)
            if subs is None:
                return
            subs.discard(ws)
            if not subs:
                self._subs.pop(workspace, None)
                watcher = self._watchers.pop(workspace, None)
                if watcher is not None:
                    watcher.stop()

    async def notify(self, workspace: Path) -> None:
        """Broadcast a `graph_changed` event to all subscribers of workspace."""
        async with self._lock:
            targets = list(self._subs.get(workspace, ()))
        dead: list[WebSocket] = []
        for ws in targets:
            try:
                await ws.send_json({"event": "graph_changed"})
            except Exception:
                dead.append(ws)
        if dead:
            async with self._lock:
                subs = self._subs.get(workspace)
                if subs is not None:
                    for ws in dead:
                        subs.discard(ws)

    def subscription_count(self, workspace: Path) -> int:
        return len(self._subs.get(workspace, ()))

    def _start_watcher(self, workspace: Path) -> WorkspaceWatcher:
        loop = asyncio.get_running_loop()

        async def on_change() -> None:
            await self.notify(workspace)

        watcher = WorkspaceWatcher(workspace, on_change=on_change, loop=loop)
        watcher.start()
        return watcher

    async def shutdown(self) -> None:
        async with self._lock:
            for watcher in self._watchers.values():
                watcher.stop()
            self._watchers.clear()
            self._subs.clear()


def create_http_app(hub: BroadcastHub | None = None) -> Starlette:
    """Build the Starlette application exposing the browser-facing API.

    If `hub` is omitted, a fresh `BroadcastHub` is created and attached to
    `app.state.hub` so callers (and tests) can reach it.
    """
    target_hub = hub if hub is not None else BroadcastHub()

    async def ws_endpoint(ws: WebSocket) -> None:
        await ws.accept()
        project_path = ws.query_params.get("project_path")
        if not project_path:
            await ws.close(code=1008, reason="project_path query param required")
            return
        try:
            workspace = resolve_workspace(project_path)
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
        Route("/api/health", _health_endpoint),
        Route("/api/graph", _graph_endpoint),
        Route("/api/layout", _layout_get_endpoint, methods=["GET"]),
        Route("/api/layout", _layout_put_endpoint, methods=["PUT"]),
        Route(
            "/api/concept/propose-from-narrative",
            _concept_propose_from_narrative_endpoint,
            methods=["POST"],
        ),
        Route(
            "/api/concept/{concept_id}",
            _concept_patch_endpoint,
            methods=["PATCH"],
        ),
        WebSocketRoute("/ws", ws_endpoint),
    ]
    viewer_dist = _find_viewer_dist()
    if viewer_dist is not None:
        # SPA: html=True also serves index.html when a path 404s, so client
        # routes resolve without additional wiring.
        routes.append(Mount("/", app=StaticFiles(directory=viewer_dist, html=True)))
    else:
        _log.info("viewer dist not found; HTTP server will only expose /api and /ws")

    app = Starlette(routes=routes)
    app.state.hub = target_hub
    return app


def _find_viewer_dist() -> Path | None:
    """Locate `viewer/dist/` produced by Vite.

    Plugin runtime path: `${CLAUDE_PLUGIN_ROOT}/viewer/dist`
    Dev path: walk up from this file until we find `viewer/dist/index.html`.
    """
    env = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if env:
        candidate = Path(env) / "viewer" / "dist"
        if (candidate / "index.html").exists():
            return candidate
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "viewer" / "dist"
        if (candidate / "index.html").exists():
            return candidate
    return None


def _port_is_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def _resolved_port() -> int:
    raw = os.environ.get("SOLERA_MAP_PORT")
    if not raw:
        return DEFAULT_HTTP_PORT
    try:
        return int(raw)
    except ValueError:
        _log.warning("Invalid SOLERA_MAP_PORT=%r; falling back to %d", raw, DEFAULT_HTTP_PORT)
        return DEFAULT_HTTP_PORT


async def _serve() -> None:
    hub = BroadcastHub()
    http_app = create_http_app(hub=hub)
    port = _resolved_port()

    # `SOLERA_MAP_NO_MCP=1` skips the MCP stdio task. Set by the VSCode
    # extension's spawn helper, which only consumes the HTTP+WS interface and
    # would otherwise leak a stdio reader that has no client. Default behavior
    # (Claude Code plugin invocation) keeps stdio on.
    skip_mcp = os.environ.get("SOLERA_MAP_NO_MCP", "").lower() in ("1", "true", "yes")
    tasks: list[asyncio.Task[None]] = []
    if not skip_mcp:
        tasks.append(asyncio.create_task(mcp.run_stdio_async(), name="mcp-stdio"))
    else:
        _log.info("SOLERA_MAP_NO_MCP set; skipping MCP stdio transport")

    if _port_is_free(port):
        http_config = uvicorn.Config(
            http_app,
            host="127.0.0.1",
            port=port,
            log_level="warning",
            access_log=False,
        )
        http_server = uvicorn.Server(http_config)
        tasks.append(asyncio.create_task(http_server.serve(), name="http"))
    else:
        _log.warning(
            "HTTP port %d in use; another solera-map instance may already serve the browser. "
            "MCP stdio transport remains available.",
            port,
        )

    if not tasks:
        # Defensive: skip_mcp + port busy → nothing to serve. Avoid hanging.
        _log.error("No transports to start (MCP skipped, HTTP port busy). Exiting.")
        return

    try:
        await asyncio.gather(*tasks)
    finally:
        await hub.shutdown()


def run() -> None:
    """Entry point invoked by `python -m solera_mcp`."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    try:
        asyncio.run(_serve())
    except KeyboardInterrupt:
        pass


def run_http_only() -> None:
    """Run only the HTTP server — useful for `npm run dev` against an existing
    browser, or for manual end-to-end verification without an MCP client.
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    hub = BroadcastHub()
    app = create_http_app(hub=hub)
    port = _resolved_port()
    try:
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
    except KeyboardInterrupt:
        pass
    finally:
        # Sync shutdown — acceptable since we own the loop.
        asyncio.run(hub.shutdown())
