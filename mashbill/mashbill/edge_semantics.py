"""Edge semantic taxonomy — default assigner for ``SketchEdge.relation``.

v0.30.0 (D-2026-05-31-C). ``relation`` ("flow" | "injection" |
"inheritance") is STORED on the edge — the one wire SSOT read by both
the viewer (fold / layout / styling) and the server
(``propagation.py`` publish MINOR-bump). A viewer-only derivation would
drift from the server's independent directed-edge hierarchy walk
(mashbill-design-red-team A8).

``classify_edge`` only decides the DEFAULT when an edge is drawn or
migrated; once stored, ``edge.relation`` is authoritative. This is the
Python mirror of ``viewer/src/flow/edgeSemantics.ts::classifyEdge`` — a
parity test (``tests/test_edge_semantics.py``) keeps the two truth
tables byte-identical.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mashbill.models import SketchEdge

# Essence kinds whose outgoing edges inject essence into the target: the
# foundation masters and their consumer-plane refs. ``actor_ref`` is
# deliberately excluded — it is the sequence *subject*, not an overlay
# (mirrors ``foundationRefKinds.FOUNDATION_REF_KINDS`` on the viewer).
# mission_ref / value_ref / identity_ref retired 2026-06-20 (D-2026-06-20-G):
# the masters (mission / core_value / identity) remain essence sources; the
# standalone ref nodes are gone (Foundation refs are service-inspector chips).
ESSENCE_SOURCE_KINDS: frozenset[str] = frozenset(
    {
        "mission",
        "core_value",
        "identity",
    }
)


def classify_edge(canvas_kind: str, source_kind: str | None, label: str | None = None) -> str:
    """Default relation for an edge, from its canvas + source-node kind
    (+ creation-time label on the actors canvas).

    Order matters: actors-canvas edges are inheritance UNLESS a label
    arrives at creation — a labeled actors edge is a value flow
    (giver → receiver, label = what moves: 돈, 신뢰, 콘텐츠 — B-35,
    user live-watch 2026-07-04; unlabeled user-drawn lines keep the
    v0.30.0 single-type default). Then essence sources are injection,
    else flow.

    Entity↔entity edges (entities canvas, D-2026-06-20-Q step 7 / D-2026-06-17-J)
    intentionally take the ``flow`` fallthrough: a rough, directed conceptual
    link (사용자 —쓴다→ 글) — NO normalisation / FK / cardinality (below
    altitude, D-2026-06-17-I). The user may edit / delete it; it is never
    meaningless or silently uneditable (D-2026-06-20-J). Pinned by
    ``tests/test_edge_semantics.py::test_entity_edges_default_to_flow``.
    """
    if canvas_kind == "actors":
        return "flow" if label else "inheritance"
    if source_kind is not None and source_kind in ESSENCE_SOURCE_KINDS:
        return "injection"
    return "flow"


def fold_endpoints(edge: SketchEdge, canvas_kind: str | None = None) -> tuple[str, str] | None:
    """``(parent, child)`` for the fold / publish-propagation hierarchy,
    per the edge's stored ``relation`` — or ``None`` if the edge defines
    no hierarchy. Mirror of
    ``viewer/src/flow/foldHierarchy.ts::foldEndpoints``:

      - flow        → (source, target)            — source is parent;
                      EXCEPT the actors canvas (B-35, 2026-07-04), where
                      a flow edge is a peer value exchange
                      (giver → receiver) and never containment.
      - inheritance → (target, source)  INVERTED  — the arrow points
                      child→superclass, so the *target* is the parent.
      - injection   → None                        — an essence overlay
                      doesn't contain its target.

    Undirected edges (``directed is False``) define no hierarchy.
    """
    if not getattr(edge, "directed", True):
        return None
    relation = getattr(edge, "relation", "flow")
    if relation == "injection":
        return None
    if relation == "inheritance":
        return (edge.target, edge.source)
    if canvas_kind == "actors":
        return None
    return (edge.source, edge.target)
