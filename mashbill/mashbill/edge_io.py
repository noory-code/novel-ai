"""Edge append I/O — the clobber-safe single-edge write (D-2026-07-02-J).

Split from ``canvas_io`` (500-line rule): edge creation is its own
responsibility. Mirrors ``create_node``'s read → validate → append →
re-validate-whole-doc → atomic-write shape.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from mashbill.canvas_io import read_canvas, write_canvas
from mashbill.models import CanvasDoc, CanvasKind
from mashbill.models_union import SketchEdge


def create_edge(
    plot_root: Path,
    project_id: str,
    canvas_kind: CanvasKind,
    source_id: str,
    target_id: str,
    service_id: str | None = None,
    label: str = "",
) -> dict[str, Any]:
    """Append ONE directed edge — the clobber-safe way to draw a line
    (D-2026-07-02-J), mirroring :func:`create_node`.

    Benchmark finding (2026-07-02): every coach-registered feature floated
    unconnected — the coach had a safe node-append but only the clobber-unsafe
    whole-doc ``update_canvas`` for edges, so it never drew the service→feature
    line and the canvas degraded into a scatter (against thinking-through-sight).

    Validates both endpoints exist on the canvas (Fail Fast), mints the id
    server-side, classifies ``relation`` from canvas + source kind (the same
    SSOT the viewer uses, D-2026-05-31-C), appends the one edge, re-validates
    the whole ``CanvasDoc``, writes atomically. **Idempotent**: an existing
    directed ``source→target`` edge is returned as-is, never duplicated —
    a retried confirmation can't stripe the canvas with parallel lines.
    """
    from mashbill.edge_semantics import classify_edge

    canvas = read_canvas(plot_root, project_id, canvas_kind, service_id)
    nodes_by_id = {n.id: n for n in canvas.nodes}
    for endpoint in (source_id, target_id):
        if endpoint not in nodes_by_id:
            raise ValueError(f"edge endpoint not on the {canvas_kind!r} canvas: {endpoint!r}")
    for existing in canvas.edges:
        if existing.source == source_id and existing.target == target_id and existing.directed:
            return {"edge": existing.model_dump(by_alias=True), "existing": True}
    relation = classify_edge(canvas_kind, nodes_by_id[source_id].kind)
    edge = SketchEdge.model_validate(
        {
            "id": f"edge_{uuid4().hex[:8]}",
            "source": source_id,
            "target": target_id,
            "label": label,
            "directed": True,
            "relation": relation,
        }
    )
    updated = CanvasDoc.model_validate(
        canvas.model_copy(update={"edges": [*canvas.edges, edge]}).model_dump(by_alias=True)
    )
    write_canvas(plot_root, project_id, updated)
    return {"edge": edge.model_dump(by_alias=True), "existing": False}
