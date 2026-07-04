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


def _compute_fresh_position(existing: list[SketchNode], kind: str) -> tuple[float, float]:
    """Where a new ``kind`` node is dropped on a canvas that already holds
    ``existing`` nodes.

    **Cluster with its own kind (D-2026-07-02-C).** Novel's essence is
    thinking-through-sight, so a new node must JOIN the visual group of its kind,
    not land at a fixed generic spot ignoring where the siblings actually sit.
    When same-kind nodes exist, left-align to that cluster and drop just below its
    lowest member (stacking the group downward). Only the first node of a kind
    (no siblings yet) uses the generic drop lane, staggered by total node count so
    distinct first-of-kind creates don't overlap. Best-effort — last-write-wins
    means two *concurrent* creates can still collide (named limit, D-2026-06-27-B)."""
    same_kind = [n for n in existing if n.kind == kind]
    if same_kind:
        x = min(n.x for n in same_kind)
        y = max(n.y for n in same_kind) + _FRESH_DY
        return x, y
    return _FRESH_X, _FRESH_Y0 + _FRESH_DY * len(existing)


# Child column offset for ``near`` placement — right of the anchor, wide enough
# to clear the default node width comfortably.
_NEAR_DX = 260.0
# A child column belongs to ONE anchor: siblings stack from the anchor's y; a
# node further than this from the anchor's y is another anchor's child.
_NEAR_BAND = 400.0


def _compute_near_position(existing: list[SketchNode], anchor: SketchNode) -> tuple[float, float]:
    """Place a new node beside ``anchor``, stacked below earlier siblings.

    Canvas-drawing defect (D-2026-07-02-L, user report "캔버스는 잘 못그리네"):
    kind-clustering piled every feature of EVERY service into one global column.
    A child belongs beside ITS parent — one column per anchor (right of it),
    siblings stacking downward within the anchor's band."""
    child_x = anchor.x + _NEAR_DX
    siblings = [
        n for n in existing if abs(n.x - child_x) < 1.0 and abs(n.y - anchor.y) < _NEAR_BAND
    ]
    return child_x, anchor.y + _FRESH_DY * len(siblings)


# Kind default colors — MIRRORS the viewer stencil palette
# (novel/viewer/src/canvases/SketchStencil.tsx); B-23: coach-created nodes
# must look like their stencil siblings. Callers may still override.
KIND_COLORS: dict[str, str] = {
    "mission": "#fef3c7",
    "core_value": "#fde68a",
    "identity": "#fed7aa",
    "actor": "#fecaca",
    "category": "#e2e8f0",
    "service": "#bae6fd",
    "note": "#fef9c3",
    "feature": "#e0f2fe",
    "entity": "#cffafe",
    "actor_ref": "#fce7f3",
    "step": "#e0e7ff",
    "decision": "#fde68a",
}
