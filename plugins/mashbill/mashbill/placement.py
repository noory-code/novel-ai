"""Node placement policy — where a fresh node lands (D-2026-07-02-C/L).

Split from ``canvas_io`` (500-line rule): placement is policy, not IO.
Kind-clustering keeps same-kind nodes grouped; ``near`` placement puts a
child beside ITS parent (one column per anchor) so a service's features
never pile into a global heap.
"""

from __future__ import annotations

from mashbill.models_union import SketchNode

_FRESH_X = 160.0
_FRESH_Y0 = 120.0
_FRESH_DY = 80.0

# W-00000451 — the tallest card each kind renders at (text is line-clamped, so
# a kind's card has a ceiling). A node is stored at the stub height until the
# viewer measures it, so stacking by the stored height let a coach burst of ten
# entities render on top of each other. Measured from the walk and the sim
# corpus (canvas.view.json heights, max per kind).
_RENDER_HEIGHT: dict[str, float] = {
    "mission": 90.0,
    "core_value": 84.0,
    "identity": 108.0,
    "actor": 96.0,
    "category": 120.0,
    "service": 173.0,
    "feature": 169.0,
    "entity": 96.0,
    "actor_ref": 120.0,
    "step": 108.0,
    "decision": 124.0,
    "rule": 92.0,
    "note": 72.0,
}
_DEFAULT_RENDER_HEIGHT = 120.0
# Space between stacked cards.
_STACK_GAP = 24.0
# Nodes whose x differs by less than this share a column.
_COLUMN_TOLERANCE = 1.0


def _rendered_height(node: SketchNode) -> float:
    """How tall ``node`` is on screen: its measured height, or its kind's
    ceiling while it still carries the stub height."""
    return max(node.height, _RENDER_HEIGHT.get(node.kind, _DEFAULT_RENDER_HEIGHT))


def _bottom(node: SketchNode) -> float:
    return node.y + _rendered_height(node)


def _first_free_y(existing: list[SketchNode], x: float, y: float, kind: str) -> float:
    """Push ``y`` down until a ``kind`` card at ``(x, y)`` overlaps no card in
    its column — the guarantee W-00000451 adds on top of every heuristic."""
    height = _RENDER_HEIGHT.get(kind, _DEFAULT_RENDER_HEIGHT)
    column = sorted((n for n in existing if abs(n.x - x) < _COLUMN_TOLERANCE), key=lambda n: n.y)
    moved = True
    while moved:
        moved = False
        for n in column:
            if y < _bottom(n) and n.y < y + height:
                y = _bottom(n) + _STACK_GAP
                moved = True
    return y


# D-2026-07-04-D — one side SSOT: the FIRST foundation pillar of a kind starts
# on the side its anchor spoke pins to (``edge_io.anchor_side_by_kind``:
# mission top, core_value left, identity right), so placement, pins, and
# layout agree. The seeds used to anchor these clusters; with blank-canvas
# start (D-2026-07-04-P) the first-of-kind drop carries the side itself.
# Coordinates = the retired seeds' spots (the layout SSOT around the 0,0
# anchor). These kinds exist only on the foundation canvas, so keying on
# kind alone is safe.
_FIRST_OF_KIND_XY: dict[str, tuple[float, float]] = {
    "mission": (-100.0, -220.0),
    "core_value": (-340.0, -40.0),
    "identity": (140.0, -45.0),
}


def _compute_fresh_position(existing: list[SketchNode], kind: str) -> tuple[float, float]:
    """Where a new ``kind`` node is dropped on a canvas that already holds
    ``existing`` nodes.

    **Cluster with its own kind (D-2026-07-02-C).** Novel's essence is
    thinking-through-sight, so a new node must JOIN the visual group of its kind,
    not land at a fixed generic spot ignoring where the siblings actually sit.
    When same-kind nodes exist, left-align to that cluster and drop just below its
    lowest member (stacking the group downward). The first node of a kind
    (no siblings yet) starts on its pinned side when it has one
    (``_FIRST_OF_KIND_XY``), else uses the generic drop lane, staggered by total
    node count so distinct first-of-kind creates don't overlap. Best-effort —
    last-write-wins means two *concurrent* creates can still collide (named
    limit, D-2026-06-27-B)."""
    same_kind = [n for n in existing if n.kind == kind]
    if same_kind:
        x = min(n.x for n in same_kind)
        y = max(_bottom(n) for n in same_kind) + _STACK_GAP
        return x, _first_free_y(existing, x, y, kind)
    pinned = _FIRST_OF_KIND_XY.get(kind)
    if pinned is not None:
        return pinned[0], _first_free_y(existing, pinned[0], pinned[1], kind)
    y = _FRESH_Y0 + _FRESH_DY * len(existing)
    return _FRESH_X, _first_free_y(existing, _FRESH_X, y, kind)


# Child column offset for ``near`` placement — right of the anchor, wide enough
# to clear the default node width comfortably.
_NEAR_DX = 260.0
# A child column belongs to ONE anchor: siblings stack from the anchor's y; a
# node further than this from the anchor's y is another anchor's child.
_NEAR_BAND = 400.0


def _compute_near_position(
    existing: list[SketchNode], anchor: SketchNode, kind: str
) -> tuple[float, float]:
    """Place a new node beside ``anchor``, stacked below earlier siblings.

    Canvas-drawing defect (D-2026-07-02-L, user report "캔버스는 잘 못그리네"):
    kind-clustering piled every feature of EVERY service into one global column.
    A child belongs beside ITS parent — one column per anchor (right of it),
    siblings stacking downward within the anchor's band."""
    child_x = anchor.x + _NEAR_DX
    siblings = [
        n for n in existing if abs(n.x - child_x) < 1.0 and abs(n.y - anchor.y) < _NEAR_BAND
    ]
    y = max(_bottom(n) for n in siblings) + _STACK_GAP if siblings else anchor.y
    return child_x, _first_free_y(existing, child_x, y, kind)


# Kind default colors — MIRRORS the viewer stencil palette
# (novel/viewer/src/canvases/SketchStencil.tsx); B-23: coach-created nodes
# must look like their stencil siblings. Callers may still override.
KIND_COLORS: dict[str, str] = {
    "mission": "#fef3c7",
    "core_value": "#fde68a",
    "identity": "#fed7aa",
    "actor": "#fecaca",
    # D-2026-07-05-G — the services canvas' three kinds must read apart at a
    # glance (user: pale slate/sky/sky all blurred together): touchpoint
    # violet-200, service sky-200, feature green-200.
    "category": "#ddd6fe",
    "service": "#bae6fd",
    "note": "#fef9c3",
    "feature": "#bbf7d0",
    "entity": "#cffafe",
    "actor_ref": "#fce7f3",
    "step": "#e0e7ff",
    "decision": "#fde68a",
}
