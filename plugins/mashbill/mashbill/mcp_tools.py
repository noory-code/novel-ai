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
from typing import Any

from fastmcp import FastMCP

from mashbill.chat_selection import build_turn_preamble
from mashbill.folder_io import (
    create_project,
    list_feature_details,
    read_canvas,
    read_project,
)
from mashbill.git_store import (
    list_tags,
)
from mashbill.mcp_canvas_write_tools import (
    create_edge_with_draft,
    create_node_with_draft,
    set_node_references_with_draft,
    update_canvas_with_draft,
    update_node_with_draft,
)
from mashbill.mcp_context_tools import (
    get_canvas_framing,
    get_design_principles,
)
from mashbill.mcp_draft_tools import record_draft, resolve_draft
from mashbill.mcp_git_tools import delete_project_tag, list_project_tags, tag_project
from mashbill.mcp_project_tools import rename_project_with_draft
from mashbill.migrate import migrate_v01_to_v02
from mashbill.models import CanvasDoc, CanvasKind
from mashbill.models_foundation import PROJECT_ANCHOR_ID
from mashbill.node_search import search_nodes
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
        "git repo. Edits are never auto-committed — only the tag tools touch git."
    ),
)

for _tool in (
    get_design_principles,
    get_canvas_framing,
    record_draft,
    resolve_draft,
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
def publish_project_snapshot_tool(project_path: str, project_id: str) -> dict[str, Any]:
    """Freeze the project's shared structure (foundation / actors / entities)
    into a format F ``vP`` snapshot. Returns the manifest. (D-2026-06-22-D.)"""
    from mashbill.format_f import publish_project_snapshot

    plot_root = resolve_plot_root(project_path)
    return publish_project_snapshot(plot_root, project_id)


@mcp.tool()
def publish_service_tool(project_path: str, project_id: str, service_id: str) -> dict[str, Any]:
    """Freeze one service into a format F ``vS`` release (refs the latest ``vP``;
    bootstrap + refs-integrity gated). Returns the manifest. (D-2026-06-22-D.)"""
    from mashbill.format_f import publish_service

    plot_root = resolve_plot_root(project_path)
    return publish_service(plot_root, project_id, service_id)


@mcp.tool()
def rename_project(project_path: str, project_id: str, name: str) -> dict[str, Any]:
    """Update a project's ``name`` and mirror it onto the Core canvas's
    Project anchor label in one shot."""
    plot_root = resolve_plot_root(project_path)
    return rename_project_with_draft(plot_root, project_id, name).model_dump()


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


@mcp.tool()
def update_canvas(
    project_path: str,
    project_id: str,
    canvas: dict[str, Any],
    draft_id: str | None = None,
    chat_scope: str = "",
) -> dict[str, Any]:
    """Overwrite a canvas. Writing ``services`` auto-creates / archives
    Detail canvases so the Services overview and its feature Details stay
    1:1. The response reports the reconciliation. A supplied ``draft_id`` is
    confirmed; otherwise a content change records a confirmed fallback draft."""
    plot_root = resolve_plot_root(project_path)
    validated = CanvasDoc.model_validate(canvas)
    sync, warning = update_canvas_with_draft(plot_root, project_id, validated, draft_id, chat_scope)
    result: dict[str, Any] = {
        "canvas": validated.model_dump(by_alias=True),
        "sync": sync,
    }
    if warning is not None:
        result["draft_warning"] = warning
    return result


@mcp.tool()
def update_node(
    project_path: str,
    project_id: str,
    canvas_kind: CanvasKind,
    node_id: str,
    fields: dict[str, Any],
    service_id: str | None = None,
    draft_id: str | None = None,
    chat_scope: str = "",
) -> dict[str, Any]:
    """Save content into ONE node — the clobber-safe way to write a single node.

    Prefer this over ``update_canvas`` when the user has confirmed a value for the
    node they have selected: it patches only that node's *content* fields (its
    ``label`` plus the kind's typed text, e.g. a mission's ``statement`` /
    ``body``) and leaves every other node + edge untouched, so a concurrent edit
    elsewhere is never lost. ``fields`` is ``{<field name>: <value>}`` using the
    writable field names shown for the selected node. Visual / structural fields
    (position, size, colour, ``kind``, ``id``) are NOT writable here and are
    returned under ``rejected_fields``. ``canvas_kind`` ∈ ``foundation`` /
    ``actors`` / ``services`` / ``entities`` / ``feature``; ``service_id`` is
    required when ``canvas_kind == "feature"``. Errors if ``node_id`` is absent
    (the project anchor is not a node). Only call this after the user confirms —
    never to finalise something they haven't agreed to. Pass [Write target]
    ``chat_scope``; omitting ``draft_id`` records a confirmed fallback draft."""
    plot_root = resolve_plot_root(project_path)
    return update_node_with_draft(
        plot_root,
        project_id,
        canvas_kind,
        node_id,
        fields,
        service_id,
        draft_id,
        chat_scope,
    )


@mcp.tool()
def create_node(
    project_path: str,
    project_id: str,
    canvas_kind: CanvasKind,
    kind: str,
    fields: dict[str, Any] | None = None,
    service_id: str | None = None,
    near: str | None = None,
    draft_id: str | None = None,
    chat_scope: str = "",
) -> dict[str, Any]:
    """Add ONE new node to a canvas — the clobber-safe way to create a node.

    Use this (not ``update_canvas``) when the user has confirmed something
    genuinely NEW that is not yet on the canvas (a new core value, actor, entity,
    step, …). It appends a single node and leaves every other node + edge
    untouched, so it never clobbers a concurrent edit or drops a field on a large
    JSON round-trip. The id and position are minted **server-side** — do NOT pass
    them. ``kind`` is the new node's kind; ``fields`` is ``{<field>: <value>}``
    using the kind's writable field names (``label`` plus its typed text, e.g. a
    ``core_value``'s ``body`` — its name is ``label``) — structural / visual
    fields are rejected and returned under ``rejected_fields``.

    Creatable kinds per canvas: foundation → ``mission`` / ``core_value`` /
    ``identity``; actors → ``actor``; services → ``category`` / ``service`` /
    ``feature``; entities → ``entity``; feature → ``step`` / ``decision`` /
    ``rule`` / ``note`` / ``actor_ref``. The synthetic project anchor
    (``project``) is never a node, and a ``feature`` is never created on the
    feature canvas (its root already exists) — both raise. The node is added
    **bare** (no edges); draw any relationship separately. To reference something
    that lives on another canvas (an actor from a service), use the reference
    pick-or-create flow, not this. ``canvas_kind`` ∈ ``foundation`` / ``actors`` /
    ``services`` / ``entities`` / ``feature``; ``service_id`` is required when
    ``canvas_kind == "feature"``. Only call this after the user confirms the new
    node — never to add something they haven't agreed to.
    ``near`` places the new node beside an existing node (its parent's column)
    instead of the generic kind pile — pass the parent's id when registering a
    child (a feature near its service, a step near the previous step), so the
    canvas stays visually grouped (D-2026-07-02-L).
    Pass [Write target] ``chat_scope``; omitting ``draft_id`` records a confirmed fallback draft.
    Returns ``{"node": <new node dict>, "rejected_fields": [...]}``."""
    plot_root = resolve_plot_root(project_path)
    return create_node_with_draft(
        plot_root,
        project_id,
        canvas_kind,
        kind,
        fields,
        service_id,
        near,
        draft_id,
        chat_scope,
    )


@mcp.tool()
def create_edge(
    project_path: str,
    project_id: str,
    canvas_kind: CanvasKind,
    source_id: str,
    target_id: str,
    service_id: str | None = None,
    label: str = "",
    draft_id: str | None = None,
    chat_scope: str = "",
) -> dict[str, Any]:
    """Draw ONE directed line between two nodes — the clobber-safe way to
    connect what you just registered (D-2026-07-02-J).

    Call this in the SAME confirmed action as the ``create_node`` it belongs
    to: a feature under its service (source = the service, target = the
    feature), a step after another step. The user's one yes covers the node
    AND its line — a registered node must never float unconnected. Both
    endpoints must already exist on the canvas; the id and the edge's
    ``relation`` are minted server-side. Idempotent — an existing directed
    source→target line is returned, never duplicated. Every other node and
    edge is left untouched. Do NOT use ``update_canvas`` just to add a line.
    A supplied ``draft_id`` is confirmed; omitting it records a confirmed
    fallback draft.
    """
    plot_root = resolve_plot_root(project_path)
    return create_edge_with_draft(
        plot_root,
        project_id,
        canvas_kind,
        source_id,
        target_id,
        service_id,
        label,
        draft_id,
        chat_scope,
    )


@mcp.tool()
def set_node_references(
    project_path: str,
    project_id: str,
    canvas_kind: CanvasKind,
    node_id: str,
    refs: dict[str, list[str]],
    service_id: str | None = None,
    draft_id: str | None = None,
    chat_scope: str = "",
) -> dict[str, Any]:
    """Wire a node's REFERENCE slots to masters on other canvases
    (D-2026-07-02-N) — the only way to fill them (they are protected from
    free-text writes).

    ``refs`` maps a ref field to master ids, e.g. ``{"ref_actor_ids":
    ["actor_ab12"], "ref_value_ids": ["core_value_cd34"]}``. Allowed per kind:
    a ``service``'s ``ref_actor_ids`` (who takes part → actors canvas) /
    ``ref_value_ids`` (what's non-negotiable → core values) /
    ``ref_identity_ids`` (what tone → identities); a ``step``/``feature``'s
    ``ref_entity_ids`` (the data it touches → entities canvas). Every id must
    already exist on its home canvas — find them with get_canvas /
    search_project_nodes, or create the master first (create_master /
    create_node on its home canvas). Call this on the user's pick, same
    confirmation gate as every write. A supplied ``draft_id`` is confirmed;
    omitting it records a confirmed fallback draft.
    """
    plot_root = resolve_plot_root(project_path)
    return set_node_references_with_draft(
        plot_root,
        project_id,
        canvas_kind,
        node_id,
        refs,
        service_id,
        draft_id,
        chat_scope,
    )


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
