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
# The widest card each kind renders at (same source as _RENDER_HEIGHT).
_RENDER_WIDTH: dict[str, float] = {"actor_ref": 120.0, "step": 360.0}
_DEFAULT_RENDER_WIDTH = 340.0
# Space between stacked cards, and between a parent and its child column.
_STACK_GAP = 24.0
_CHILD_GAP = 40.0
# W-00000483 — entities are joined by named lines, so two stacked entities keep
# room for a line between them: its name (20 px tall) 2 px off each box and
# 18 px off each handle, where an arrowhead ends. Mirrors the viewer's line
# geometry (novel/viewer/src/canvases/edges/edgeGeometry.ts).
_ENTITY_GAP = 18.0 + 2.0 + 20.0 + 2.0 + 18.0
# The card title is not clamped: at the 340 px width cap it wraps about every
# 23 Korean characters, 20 px a line (measured: 20 chars → 96, 40 → 116,
# 80 → 156, 160 → 216 for an entity). Counting 18 per line stays on the safe side.
_TITLE_CHARS_PER_LINE = 18
_TITLE_LINE_HEIGHT = 20.0


def _expected_height(kind: str, label: str) -> float:
    """How tall a ``kind`` card titled ``label`` renders at most: the kind's
    one-line-title ceiling plus a line for each extra wrapped title line."""
    lines = max(1, -(-len(label) // _TITLE_CHARS_PER_LINE))
    base = _RENDER_HEIGHT.get(kind, _DEFAULT_RENDER_HEIGHT)
    return base + _TITLE_LINE_HEIGHT * (lines - 1)


def _rendered_height(node: SketchNode) -> float:
    """How tall ``node`` is on screen: its measured height, or what its kind
    and title render at while it still carries the stub height."""
    return max(node.height, _expected_height(node.kind, node.label or ""))


def _rendered_width(node: SketchNode) -> float:
    """How wide ``node`` is on screen, the same way as :func:`_rendered_height`."""
    return max(node.width, _RENDER_WIDTH.get(node.kind, _DEFAULT_RENDER_WIDTH))


def _bottom(node: SketchNode) -> float:
    return node.y + _rendered_height(node)


# (x, y, width, height) of a card the new node must not cover.
Rect = tuple[float, float, float, float]


def _first_free_y(
    existing: list[SketchNode],
    x: float,
    y: float,
    kind: str,
    label: str,
    obstacles: tuple[Rect, ...] = (),
    gap: float = _STACK_GAP,
) -> float:
    """Push ``y`` down until a ``kind`` card at ``(x, y)`` overlaps no card on
    the canvas — the guarantee W-00000451 adds on top of every heuristic. Cards
    beside the new one count too: a card renders up to 340 wide, so one a
    little to the side still covers the spot. ``obstacles`` are cards that are
    not canvas nodes, such as the project anchor the viewer draws. A card
    pushed past another keeps ``gap`` below it."""
    height = _expected_height(kind, label)
    width = _RENDER_WIDTH.get(kind, _DEFAULT_RENDER_WIDTH)
    rects = [(n.x, n.y, _rendered_width(n), _rendered_height(n)) for n in existing]
    rects.extend(obstacles)
    in_path = sorted((r for r in rects if r[0] < x + width and x < r[0] + r[2]), key=lambda r: r[1])
    moved = True
    while moved:
        moved = False
        for rx, ry, _rw, rh in in_path:
            if y < ry + rh and ry < y + height:
                y = ry + rh + gap
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
# W-00000451: core_value moved from x -340 to -455 so its 340 px card clears
# the default anchor (-75..75) by 40 px; mission and identity already clear it.
_FIRST_OF_KIND_XY: dict[str, tuple[float, float]] = {
    "mission": (-100.0, -220.0),
    "core_value": (-455.0, -40.0),
    "identity": (140.0, -45.0),
}


# The project anchor's card when the canvas hands in none: its default spot
# (``AnchorPlacement``) at the round card's 200 px render cap.
_DEFAULT_ANCHOR: Rect = (-75.0, -75.0, 200.0, 200.0)


def _compute_entity_position(
    existing: list[SketchNode], label: str, obstacles: tuple[Rect, ...]
) -> tuple[float, float]:
    """Where a new entity goes (W-00000483): in one of two columns flanking the
    project anchor, the shorter one (right first), under that column's lowest
    entity with room for a named line between them (``_ENTITY_GAP``).

    Every entity has a line from the anchor, and entities point at each other.
    In two short columns each box faces the anchor with a clear side, and a
    column is half as tall as one stack, so fewer lines between two of its
    boxes run behind the boxes in between. ``obstacles`` is the anchor's card
    (``storage.anchor_obstacles``); the first box of a column sits level with
    its middle."""
    ax, ay, aw, ah = obstacles[0] if obstacles else _DEFAULT_ANCHOR
    middle_x = ax + aw / 2
    entities = [n for n in existing if n.kind == "entity"]
    right = [n for n in entities if n.x + _rendered_width(n) / 2 >= middle_x]
    left = [n for n in entities if n.x + _rendered_width(n) / 2 < middle_x]
    on_right = len(right) <= len(left)
    column = right if on_right else left
    if column:
        x = min(n.x for n in column)
        y = max(_bottom(n) for n in column) + _ENTITY_GAP
    else:
        width = _RENDER_WIDTH.get("entity", _DEFAULT_RENDER_WIDTH)
        x = ax + aw + _CHILD_GAP if on_right else ax - _CHILD_GAP - width
        y = ay + ah / 2 - _expected_height("entity", label) / 2
    return x, _first_free_y(existing, x, y, "entity", label, obstacles, _ENTITY_GAP)


def _compute_fresh_position(
    existing: list[SketchNode], kind: str, label: str = "", obstacles: tuple[Rect, ...] = ()
) -> tuple[float, float]:
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
    limit, D-2026-06-27-B). Entities flank the anchor instead
    (:func:`_compute_entity_position`)."""
    if kind == "entity":
        return _compute_entity_position(existing, label, obstacles)
    same_kind = [n for n in existing if n.kind == kind]
    if same_kind:
        x = min(n.x for n in same_kind)
        y = max(_bottom(n) for n in same_kind) + _STACK_GAP
        return x, _first_free_y(existing, x, y, kind, label, obstacles)
    pinned = _FIRST_OF_KIND_XY.get(kind)
    if pinned is not None:
        return pinned[0], _first_free_y(existing, pinned[0], pinned[1], kind, label, obstacles)
    y = _FRESH_Y0 + _FRESH_DY * len(existing)
    return _FRESH_X, _first_free_y(existing, _FRESH_X, y, kind, label, obstacles)


# A child column belongs to ONE anchor: siblings stack from the anchor's y; a
# node further than this from the anchor's y is another anchor's child.
_NEAR_BAND = 400.0


def _compute_near_position(
    existing: list[SketchNode],
    anchor: SketchNode,
    kind: str,
    label: str = "",
    obstacles: tuple[Rect, ...] = (),
) -> tuple[float, float]:
    """Place a new node beside ``anchor``, stacked below earlier siblings.

    Canvas-drawing defect (D-2026-07-02-L, user report "캔버스는 잘 못그리네"):
    kind-clustering piled every feature of EVERY service into one global column.
    A child belongs beside ITS parent — one column per anchor (right of it),
    siblings stacking downward within the anchor's band."""
    # Right of the parent's rendered card (W-00000451), not a fixed offset
    # narrower than the card.
    child_x = anchor.x + _rendered_width(anchor) + _CHILD_GAP
    siblings = [
        n for n in existing if abs(n.x - child_x) < 1.0 and abs(n.y - anchor.y) < _NEAR_BAND
    ]
    y = max(_bottom(n) for n in siblings) + _STACK_GAP if siblings else anchor.y
    return child_x, _first_free_y(existing, child_x, y, kind, label, obstacles)


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
