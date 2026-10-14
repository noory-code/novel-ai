"""Write-time canvas normalization helpers."""

from __future__ import annotations

from mashbill.edge_semantics import fold_endpoints
from mashbill.models import CanvasDoc
from mashbill.models_foundation import PROJECT_ANCHOR_ID
from mashbill.models_union import SketchEdge

# W-91: only kinds that may be roots on a primary canvas receive a missing
# project-anchor spoke. This is narrower than ``_ALLOWED_KINDS_BY_CANVAS``:
# Foundation's three essence pillars are peers; Actors has one kind whose
# inheritance edge distinguishes nested roles; Services allows category and
# service at top level (category is optional) while feature is always below a
# service; Entities is a flat concept map. Feature detail has no project anchor.
# Sources: models_canvas._ALLOWED_KINDS_BY_CANVAS, public canvas-behavior.md,
# concepts/kinds.md, and edge_semantics.fold_endpoints.
ROOT_KINDS_BY_CANVAS: dict[str, frozenset[str]] = {
    "foundation": frozenset({"mission", "core_value", "identity"}),
    "actors": frozenset({"actor"}),
    "services": frozenset({"category", "service"}),
    "entities": frozenset({"entity"}),
}


def anchor_spokes_retired_by(canvas: CanvasDoc, edge: SketchEdge) -> set[str]:
    """Ids of anchor spokes that ``edge`` makes obsolete by nesting its child.

    Canon (canvas-behavior.md): an actor with an inheritance parent, or a
    service under a group, is nested and has no anchor spoke. A node created
    before its parent line already got a spoke from the save-time sweep, so the
    hierarchy edge that nests it retires that spoke in the same write.
    """
    if canvas.canvas_kind not in ("actors", "services"):
        return set()
    hierarchy = fold_endpoints(edge, canvas.canvas_kind)
    if hierarchy is None or PROJECT_ANCHOR_ID in hierarchy:
        return set()
    parent_id, child_id = hierarchy
    if parent_id == child_id:  # a loop nests nothing; the node keeps its place
        return set()
    return {
        existing.id
        for existing in canvas.edges
        if {existing.source, existing.target} == {PROJECT_ANCHOR_ID, child_id}
    }


def retire_spokes_for_new_nesting(previous: CanvasDoc | None, incoming: CanvasDoc) -> CanvasDoc:
    """Drop the spokes that nesting lines new to ``incoming`` make obsolete.

    A whole-canvas write (the coach's ``update_canvas``) can nest a node the
    same way ``create_edge`` does; only a line absent from ``previous`` counts,
    so re-saving a canvas never strips a spoke beside a line already stored.
    """
    stored = {(e.source, e.target) for e in previous.edges} if previous else set()
    retired: set[str] = set()
    for edge in incoming.edges:
        if (edge.source, edge.target) not in stored:
            retired |= anchor_spokes_retired_by(incoming, edge)
    if not retired:
        return incoming
    kept = [e for e in incoming.edges if e.id not in retired]
    return incoming.model_copy(update={"edges": kept})


def attach_orphan_anchor_spokes(canvas: CanvasDoc) -> CanvasDoc:
    """Attach one canonical anchor spoke to each pure top-level orphan.

    A candidate is skipped when any existing edge already touches it and the
    synthetic anchor, or when a stored hierarchy edge gives it a parent. Actor
    inheritance stores child→parent; Services containment stores parent→child.
    Foundation pillars and Entities relationships have no containment parent.
    """
    root_kinds = ROOT_KINDS_BY_CANVAS.get(canvas.canvas_kind)
    if not root_kinds:
        return canvas

    anchor_connected = {
        edge.target if edge.source == PROJECT_ANCHOR_ID else edge.source
        for edge in canvas.edges
        if edge.source == PROJECT_ANCHOR_ID or edge.target == PROJECT_ANCHOR_ID
    }
    parented: set[str] = set()
    for edge in canvas.edges:
        if not edge.directed or PROJECT_ANCHOR_ID in (edge.source, edge.target):
            continue
        # Only Actors and Services define containment hierarchies. Entity flow
        # edges are conceptual relationships, not parents; Foundation injection
        # edges are essence overlays. Reuse the relation SSOT for the two
        # hierarchical canvases (including Actors' child→parent arrow).
        if canvas.canvas_kind in ("actors", "services"):
            hierarchy = fold_endpoints(edge, canvas.canvas_kind)
            if hierarchy is not None:
                _, child_id = hierarchy
                parented.add(child_id)

    orphan_ids = [
        node.id
        for node in canvas.nodes
        if node.kind in root_kinds and node.id not in anchor_connected and node.id not in parented
    ]
    if not orphan_ids:
        return canvas

    # Loaded lazily from canvas_io, after its read/write API exists; the builder
    # remains the create_edge SSOT for id, relation, and handle formatting.
    from mashbill.edge_io import _build_edge

    edges = [*canvas.edges]
    edges.extend(_build_edge(canvas, PROJECT_ANCHOR_ID, node_id) for node_id in orphan_ids)
    return CanvasDoc.model_validate(
        canvas.model_copy(update={"edges": edges}).model_dump(by_alias=True)
    )
