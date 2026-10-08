"""Outermost MCP canvas write tools with simulator logging."""

from __future__ import annotations

from typing import Any

from mashbill.mcp_canvas_write_tools import (
    create_edge_with_draft,
    create_node_with_draft,
    set_node_references_with_draft,
    update_canvas_with_draft,
    update_node_with_draft,
)
from mashbill.models import CanvasDoc, CanvasKind
from mashbill.tool_log import record_tool_call
from mashbill.workspace import resolve_plot_root


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
    confirmed when it matches; writes without one do not create a draft."""
    plot_root = resolve_plot_root(project_path)
    validated = CanvasDoc.model_validate(canvas)
    sync, warning = update_canvas_with_draft(plot_root, project_id, validated, draft_id, chat_scope)
    result: dict[str, Any] = {
        "canvas": validated.model_dump(by_alias=True),
        "sync": sync,
    }
    if warning is not None:
        result["draft_warning"] = warning
    record_tool_call(
        "update_canvas",
        project_id=project_id,
        canvas=validated.canvas_kind,
        service_id=validated.feature_ref if validated.canvas_kind == "feature" else None,
        node_ids=[str(node.id) for node in validated.nodes],
        draft_id=draft_id,
    )
    return result


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
    ``chat_scope``; omitting ``draft_id`` does not create a draft."""
    plot_root = resolve_plot_root(project_path)
    result = update_node_with_draft(
        plot_root,
        project_id,
        canvas_kind,
        node_id,
        fields,
        service_id,
        draft_id,
        chat_scope,
    )
    record_tool_call(
        "update_node",
        project_id=project_id,
        canvas=canvas_kind,
        service_id=service_id,
        node_id=node_id,
        draft_id=draft_id,
    )
    return result


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
    Pass [Write target] ``chat_scope``; omitting ``draft_id`` does not create a draft.
    Returns ``{"node": <new node dict>, "rejected_fields": [...]}``."""
    plot_root = resolve_plot_root(project_path)
    result = create_node_with_draft(
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
    record_tool_call(
        "create_node",
        project_id=project_id,
        canvas=canvas_kind,
        service_id=service_id,
        node_id=result["node"]["id"],
        draft_id=draft_id,
    )
    return result


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
    A matching supplied ``draft_id`` is confirmed; omitting it does not create
    a draft.
    """
    plot_root = resolve_plot_root(project_path)
    result = create_edge_with_draft(
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
    record_tool_call(
        "create_edge",
        project_id=project_id,
        canvas=canvas_kind,
        service_id=service_id,
        node_ids=[source_id, target_id],
        draft_id=draft_id,
    )
    return result


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
    confirmation gate as every write. A matching supplied ``draft_id`` is
    confirmed; omitting it does not create a draft.
    """
    plot_root = resolve_plot_root(project_path)
    result = set_node_references_with_draft(
        plot_root,
        project_id,
        canvas_kind,
        node_id,
        refs,
        service_id,
        draft_id,
        chat_scope,
    )
    record_tool_call(
        "set_node_references",
        project_id=project_id,
        canvas=canvas_kind,
        service_id=service_id,
        node_id=node_id,
        draft_id=draft_id,
    )
    return result
