"""Where the engine puts a coach-created entity (W-00000483, O-00000153).

Entities are joined by named lines. Stacked 24 px apart in one column right of
the project anchor, a line between two boxes had no room for its name (20 px
tall) beside the arrowheads (18 px from each handle), and a line between two
boxes far apart in the column ran behind every box in between. The fixture
replays the twelve entities the coach made in newcomer walk 3, in the order it
made them, on that walk's anchor (152 px round card at -75, -75).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mashbill.folder_io import create_node, create_project, write_canvas
from mashbill.models import ActorNode, CanvasDoc, EntityNode
from mashbill.models_canvas import AnchorPlacement
from mashbill.storage import read_project, write_project
from mashbill.workspace import resolve_plot_root

WALK3_LABELS = (
    "회원권 종류",
    "회원이 구매한 회원권",
    "회원 정보",
    "수업",
    "예약",
    "출석",
    "강사비 정산",
    "강사님 정보",
    "대기 신청",
    "알림",
    "차감·복구 내역",
    "예약 제한 내역",
)

# The tallest entity card (placement._RENDER_HEIGHT) and the widest card.
ENTITY_HEIGHT = 96.0
CARD_WIDTH = 340.0
# A line between two stacked boxes runs across the gap between them. Its name
# is 20 px tall and must keep 18 px off each handle (the arrowhead) and 2 px
# off each box: 18 + 2 + 20 + 2 + 18.
LABELED_GAP = 60.0


def _project(tmp_path: Path, nodes: list[Any] | None = None) -> Path:
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "요가스튜디오 예약")
    project = read_project(plot_root, "alpha")
    anchors = dict(project.anchors)
    anchors["entities"] = AnchorPlacement(x=-75.0, y=-75.0, width=152.0, height=152.0)
    write_project(plot_root, project.model_copy(update={"anchors": anchors}))
    write_canvas(
        plot_root,
        "alpha",
        CanvasDoc(canvas_id="entities", canvas_kind="entities", nodes=nodes or []),
    )
    return plot_root


def _walk3(tmp_path: Path) -> list[dict[str, Any]]:
    plot_root = _project(tmp_path)
    return [
        create_node(plot_root, "alpha", "entities", "entity", {"label": label})["node"]
        for label in WALK3_LABELS
    ]


def _columns(nodes: list[dict[str, Any]]) -> dict[float, list[dict[str, Any]]]:
    columns: dict[float, list[dict[str, Any]]] = {}
    for n in nodes:
        columns.setdefault(n["x"], []).append(n)
    return {x: sorted(col, key=lambda n: n["y"]) for x, col in columns.items()}


def test_walk3_entities_flank_the_anchor_in_two_short_columns(tmp_path: Path) -> None:
    """One column right of the anchor and one left of it, filled in turn: each
    box keeps a clear side toward the anchor's line, and no column grows twice
    as tall as the walk's single column of twelve."""
    made = _walk3(tmp_path)
    columns = _columns(made)
    assert len(columns) == 2, sorted(columns)
    left_x, right_x = sorted(columns)
    anchor_left, anchor_right = -75.0, -75.0 + 200.0  # round card's 200 px render cap
    assert right_x >= anchor_right
    assert left_x + CARD_WIDTH <= anchor_left
    assert sorted(len(c) for c in columns.values()) == [6, 6]


def test_walk3_stacked_entities_leave_room_for_a_line_name_and_its_arrowheads(
    tmp_path: Path,
) -> None:
    made = _walk3(tmp_path)
    for col in _columns(made).values():
        for upper, lower in zip(col, col[1:]):
            gap = lower["y"] - (upper["y"] + ENTITY_HEIGHT)
            assert gap >= LABELED_GAP, (upper["label"], lower["label"], gap)


def test_the_first_entity_sits_level_with_the_anchor(tmp_path: Path) -> None:
    """The anchor's line to the first box runs straight across, not down."""
    first = _walk3(tmp_path)[0]
    anchor_middle = -75.0 + 200.0 / 2
    assert abs(first["y"] + ENTITY_HEIGHT / 2 - anchor_middle) < 1.0


def test_an_entity_joins_the_shorter_side_of_an_existing_canvas(tmp_path: Path) -> None:
    """Newcomer walk 2: five entities already stand in one column at x 160.
    The next one starts the other side instead of growing that column."""
    plot_root = _project(
        tmp_path,
        [
            EntityNode(id=f"e{i}", label=f"데이터 {i}", x=160.0, y=120.0 + 120.0 * i)
            for i in range(5)
        ],
    )
    nxt = create_node(plot_root, "alpha", "entities", "entity", {"label": "다음"})["node"]
    assert nxt["x"] + CARD_WIDTH <= -75.0


def test_an_entity_pushed_past_a_card_in_its_way_keeps_the_labeled_gap(tmp_path: Path) -> None:
    """A box dragged across the column's path pushes the new entity below it,
    with the same room for a line's name as between two stacked entities."""
    plot_root = _project(
        tmp_path,
        [
            EntityNode(id="r1", label="오른쪽", x=165.0, y=-23.0),
            EntityNode(id="l1", label="왼쪽", x=-455.0, y=-23.0),
            # Mostly left of the anchor's middle, but its 340 px card reaches
            # into the right column, just under where the next box would go.
            EntityNode(id="dragged", label="끌어 놓은 것", x=-160.0, y=150.0),
        ],
    )
    nxt = create_node(plot_root, "alpha", "entities", "entity", {"label": "다음"})["node"]
    assert nxt["x"] == 165.0
    assert nxt["y"] >= 150.0 + ENTITY_HEIGHT + LABELED_GAP, nxt["y"]


def test_other_kinds_still_stack_24_apart(tmp_path: Path) -> None:
    """Only entities change: an actor still stacks under its kind 24 px apart."""
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    write_canvas(
        plot_root,
        "alpha",
        CanvasDoc(
            canvas_id="actors",
            canvas_kind="actors",
            nodes=[ActorNode(id="a1", label="운영자", x=160.0, y=120.0)],
        ),
    )
    nxt = create_node(plot_root, "alpha", "actors", "actor", {"label": "회원"})["node"]
    assert (nxt["x"], nxt["y"]) == (160.0, 120.0 + 96.0 + 24.0)
