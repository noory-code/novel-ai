"""FastMCP tool surface for Novel (v0.4).

Claude Code uses these tools to read and mutate a Novel project. The surface
overlaps the HTTP API for project / canvas CRUD so a session can move between
both; it is not one-to-one — some tools are MCP-only (``search_project_nodes``,
``update_node``) and some HTTP routes have no tool (entity usage, masters,
anchors).
"""

from __future__ import annotations

import time
import webbrowser
from pathlib import Path
from typing import Any, Literal

from fastmcp import FastMCP

from mashbill.chat_selection import build_turn_preamble
from mashbill.design_check import set_design_check as set_design_check
from mashbill.folder_io import (
    create_project,
    list_feature_details,
    read_canvas,
    read_project,
)
from mashbill.format_f import publish_service
from mashbill.git_store import list_tags
from mashbill.mcp_canvas_tools import create_edge as create_edge
from mashbill.mcp_canvas_tools import create_node as create_node
from mashbill.mcp_canvas_tools import move_node as move_node
from mashbill.mcp_canvas_tools import set_node_references as set_node_references
from mashbill.mcp_canvas_tools import update_canvas as update_canvas
from mashbill.mcp_canvas_tools import update_node as update_node
from mashbill.mcp_context_tools import (
    get_canvas_framing,
    get_design_principles,
)
from mashbill.mcp_draft_tools import record_draft, resolve_draft, update_draft
from mashbill.mcp_git_tools import delete_project_tag, list_project_tags, tag_project
from mashbill.mcp_project_tools import rename_project_with_draft
from mashbill.mcp_publish import publish_blueprint_for_person
from mashbill.migrate import migrate_v01_to_v02
from mashbill.models import CanvasKind
from mashbill.models_foundation import PROJECT_ANCHOR_ID
from mashbill.node_search import search_nodes
from mashbill.tool_log import record_tool_call
from mashbill.viewer_context import read_viewer_context
from mashbill.workspace import (
    discover_projects,
    enumerate_projects,
    resolve_plot_root,
    resolved_port,
    workspace_root_from_plot_root,
)

mcp = FastMCP(
    "mashbill",
    instructions=(
        "Novel stores projects as folders of per-canvas JSON files under "
        "``.noory/novel/{project}/``. Use ``list_projects`` / ``get_project`` "
        "to discover state, ``get_canvas`` / ``update_canvas`` to read or write "
        "a single canvas (``foundation`` / ``actors`` / ``services`` / "
        "``entities`` / ``feature``), ``update_node`` to patch one node's content "
        "fields clobber-safely (preferred over ``update_canvas`` for a single-node "
        "edit), and ``tag_project`` to plant a named milestone in the project's "
        "git repo. Edits are never auto-committed — tag tools and blueprint "
        "publishing touch git."
    ),
)

for _tool in (
    get_design_principles,
    get_canvas_framing,
    record_draft,
    update_draft,
    resolve_draft,
    set_design_check,
    tag_project,
    list_project_tags,
    delete_project_tag,
):
    mcp.tool()(_tool)


# ---------------------------------------------------------------------------
# project CRUD
# ---------------------------------------------------------------------------


@mcp.tool()
def list_projects(project_path: str) -> list[dict[str, Any]]:
    """List every project folder directly under ``.noory/novel/`` (R9 layout)."""
    plot_root = resolve_plot_root(project_path)
    return [p.model_dump() for p in enumerate_projects(plot_root)]


@mcp.tool()
def discover_workspace_projects(project_path: str) -> list[dict[str, Any]]:
    """Discover every Novel project anywhere under the workspace root, each with
    its directory relative to the root (``"."`` for a root-level project).

    Mirrors ``GET /api/workspace/projects`` (v0.32.0)."""
    root = Path(project_path).expanduser().resolve()
    return [{"project": p.model_dump(), "dir": d} for p, d in discover_projects(root)]


@mcp.tool()
def get_project(project_path: str, project_id: str) -> dict[str, Any]:
    """Read a project's metadata + its feature ids + tags."""
    plot_root = resolve_plot_root(project_path)
    proj = read_project(plot_root, project_id)
    return {
        **proj.model_dump(),
        "feature_details": list_feature_details(plot_root, project_id),
        "tags": list_tags(workspace_root_from_plot_root(plot_root)),
    }


@mcp.tool()
def create_project_tool(project_path: str, project_id: str, name: str = "") -> dict[str, Any]:
    """Create a new project folder seeded with Core / Actors / Services-Overview."""
    plot_root = resolve_plot_root(project_path)
    proj = create_project(plot_root, project_id, name)
    return proj.model_dump()


@mcp.tool()
def publish_project_snapshot_tool(
    project_path: str,
    project_id: str,
    bump: Literal["major", "minor", "patch"],
    message: str | None = None,
    slugs: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Bump the blueprint version, commit and tag the data folder, then leave
    a format F ``vP`` snapshot. Ask the person for the bump and obtain their
    permission before calling this tool. A node published for the first time whose name has letters outside ASCII (for example Korean) needs an English id: propose one per node, have the person confirm it, and pass them as slugs={node_id: id}. Without them the tool fails and lists those nodes."""  # noqa: E501
    plot_root = resolve_plot_root(project_path)
    workspace_root = workspace_root_from_plot_root(plot_root)
    result = publish_blueprint_for_person(
        plot_root, project_id, bump, message, workspace_root, slugs=slugs
    )
    record_tool_call("publish_project_snapshot_tool", project_id=project_id)
    return result


@mcp.tool()
def publish_service_tool(
    project_path: str,
    project_id: str,
    service_id: str,
    slugs: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Freeze one service into a format F ``vS`` release (refs the latest ``vP``;
    bootstrap + refs-integrity gated). Returns the manifest. (D-2026-06-22-D.) A node published for the first time whose name has letters outside ASCII (for example Korean) needs an English id: propose one per node, have the person confirm it, and pass them as slugs={node_id: id}. Without them the tool fails and lists those nodes."""  # noqa: E501
    plot_root = resolve_plot_root(project_path)
    result = publish_service(plot_root, project_id, service_id, slugs=slugs)
    record_tool_call("publish_service_tool", project_id=project_id, service_id=service_id)
    return result


PERSON_ONLY_TOOLS = ("publish_project_snapshot_tool", "publish_service_tool")


def hide_person_only_tools(server: FastMCP) -> None:
    """Remove publication tools from an in-app coach's local tool catalog."""
    for name in PERSON_ONLY_TOOLS:
        server.local_provider.remove_tool(name)


@mcp.tool()
def rename_project(
    project_path: str,
    project_id: str,
    name: str,
    draft_id: str | None = None,
) -> dict[str, Any]:
    """Update a project's ``name`` and mirror it onto the Core canvas's
    Project anchor label in one shot. Pass the accepted project-name draft id
    when available."""
    plot_root = resolve_plot_root(project_path)
    renamed, warning = rename_project_with_draft(plot_root, project_id, name, draft_id)
    result = renamed.model_dump()
    if warning is not None:
        result["draft_warning"] = warning
    record_tool_call("rename_project", project_id=project_id, canvas="project", draft_id=draft_id)
    return result


# ---------------------------------------------------------------------------
# canvas read / write
# ---------------------------------------------------------------------------


@mcp.tool()
def get_canvas(
    project_path: str,
    project_id: str,
    canvas_kind: CanvasKind,
    service_id: str | None = None,
) -> dict[str, Any]:
    """Read a single canvas. ``canvas_kind`` ∈ ``foundation`` / ``actors`` /
    ``services`` / ``entities`` / ``feature``. ``service_id`` is
    required when ``canvas_kind == "feature"``."""
    plot_root = resolve_plot_root(project_path)
    canvas = read_canvas(plot_root, project_id, canvas_kind, service_id)
    doc = canvas.model_dump(by_alias=True)
    # D-2026-07-03-W — surface the viewer-synthetic project anchor to the
    # agent on anchored canvases, so "connect the pillar to the hub" is a
    # visible fact, not special-case prompt knowledge (B-14's deeper root).
    if canvas_kind in ("foundation", "actors", "services"):
        doc["nodes"] = [
            {
                "id": PROJECT_ANCHOR_ID,
                "kind": "project",
                "label": "(project anchor — the canvas hub; a valid edge endpoint)",
            },
            *doc["nodes"],
        ]
    return doc


for _canvas_tool in (
    update_canvas,
    update_node,
    move_node,
    create_node,
    create_edge,
    set_node_references,
):
    mcp.tool()(_canvas_tool)


@mcp.tool()
def list_detail_canvases(project_path: str, project_id: str) -> list[str]:
    """Return the service ids that have their own Detail canvas."""
    plot_root = resolve_plot_root(project_path)
    return list_feature_details(plot_root, project_id)


@mcp.tool()
def search_project_nodes(project_path: str, project_id: str, query: str) -> list[dict[str, Any]]:
    """Find nodes by name across all of a project's canvases (the "name" lookup
    entry point). Use this to resolve a node the user names but that isn't on the
    canvas you're looking at — e.g. "the comment feature", "the Reader actor".
    Case-insensitive label substring match; returns up to 20
    ``{id, kind, label, canvas}`` hits (``canvas`` is the scope: ``foundation`` …
    or ``feature:<service_id>``). Then ``get_canvas`` that scope to read details."""
    plot_root = resolve_plot_root(project_path)
    return search_nodes(plot_root, project_id, query)


# ---------------------------------------------------------------------------
# migration + utility
# ---------------------------------------------------------------------------


@mcp.tool()
def migrate_v01_sketches(project_path: str) -> list[str]:
    """Migrate any ``sketches/*.json`` (v0.1) files to the v0.4 folder layout.

    Idempotent. Returns the list of project ids that were migrated.
    Originals rename to ``{id}.json.v01.bak``. This also runs automatically
    whenever ``GET /api/projects`` is called from the viewer.
    """
    plot_root = resolve_plot_root(project_path)
    return migrate_v01_to_v02(plot_root)


@mcp.tool()
def get_viewer_context(project_path: str) -> dict[str, Any]:
    """Read what the Novel viewer is currently showing (D-2026-06-15-D).

    Returns the user's live canvas context so you can resolve "this" / "fix it"
    against what they have on screen, the same way the in-app chat does::

        {
          "active_canvas": "<scope>" | null,   # e.g. "foundation",
                                                # "feature:<id>"
          "selection": [{"id", "kind", "label"}, ...],
          "framing": "<canvas coaching system prompt>",  # guard + tone +
                                                # the canvas's coaching playbook
                                                # (same as in-app, Phase 3)
          "context": "<current Foundation + active-canvas turn context>",
          "updated_at": <epoch seconds> | null,
          "stale": <bool>,                       # report older than the TTL
          "has_viewer": <bool>                   # a live viewer is reporting
        }

    When ``has_viewer`` is false (no viewer open, or the last report is stale)
    ``active_canvas`` is null, ``selection`` is empty, and ``context`` is empty —
    do NOT treat an old selection as the user's current one.
    """
    plot_root = resolve_plot_root(project_path)
    context = read_viewer_context(plot_root, now=time.time())
    scope = context.get("active_canvas")
    selection = context.get("selection")
    if context.get("has_viewer") and isinstance(scope, str):
        context["context"] = build_turn_preamble(
            plot_root, scope, selection, project_path=project_path
        )
    else:
        context["context"] = ""
    return context


@mcp.tool()
def open_canvas(project_path: str, project_id: str | None = None) -> str:
    """Open the Novel viewer in the default browser."""
    resolve_plot_root(project_path)  # raises if path is unusable
    port = resolved_port()
    url = f"http://127.0.0.1:{port}/?project_path={project_path}"
    if project_id:
        url += f"&project={project_id}"
    webbrowser.open(url)
    return f"Opened {url}"
