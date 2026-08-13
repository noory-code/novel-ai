"""Write-time project-anchor orphan sweep (W-91)."""

from __future__ import annotations

from pathlib import Path

from mashbill.folder_io import create_edge, create_node, create_project, read_canvas, write_canvas
from mashbill.models import (
    CanvasDoc,
    CanvasKind,
    CategoryNode,
    EntityNode,
    ServiceNode,
    SketchEdge,
)
from mashbill.models_foundation import PROJECT_ANCHOR_ID
from mashbill.workspace import resolve_plot_root


def _setup(tmp_path: Path) -> Path:
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    return plot_root


def test_write_canvas_adds_anchor_spoke_to_orphan_service(tmp_path: Path) -> None:
    plot_root = _setup(tmp_path)
    write_canvas(
        plot_root,
        "alpha",
        CanvasDoc(
            canvas_id="services",
            canvas_kind="services",
            nodes=[ServiceNode(id="svc", label="Payments")],
        ),
    )

    saved = read_canvas(plot_root, "alpha", "services")
    assert [(edge.source, edge.target, edge.relation) for edge in saved.edges] == [
        (PROJECT_ANCHOR_ID, "svc", "flow")
    ]


def test_entities_wired_only_to_each_other_still_reach_the_anchor(tmp_path: Path) -> None:
    # The Entities canvas is a flat concept map: its edges are relationships
    # between entities, never containment. Left alone, a coach that draws only
    # those relationships produces a cluster with no tie to the project — it
    # floats beside the anchor while every other canvas roots into it, and the
    # reader cannot see which design the entities serve (novel-workspace O-9).
    # The sweep must reach entities, and it must not disturb the relationships.
    plot_root = _setup(tmp_path)
    write_canvas(
        plot_root,
        "alpha",
        CanvasDoc(
            canvas_id="entities",
            canvas_kind="entities",
            nodes=[EntityNode(id="order", label="Order"), EntityNode(id="store", label="Store")],
            edges=[SketchEdge(id="rel", source="order", target="store", directed=True)],
        ),
    )

    saved = read_canvas(plot_root, "alpha", "entities")
    spokes = {edge.target for edge in saved.edges if edge.source == PROJECT_ANCHOR_ID}
    assert spokes == {"order", "store"}
    relationships = [
        (edge.source, edge.target)
        for edge in saved.edges
        if PROJECT_ANCHOR_ID not in (edge.source, edge.target)
    ]
    assert relationships == [("order", "store")]


def test_write_canvas_skips_nested_service_with_parent_edge(tmp_path: Path) -> None:
    plot_root = _setup(tmp_path)
    write_canvas(
        plot_root,
        "alpha",
        CanvasDoc(
            canvas_id="services",
            canvas_kind="services",
            nodes=[
                CategoryNode(id="cat", label="Customer app"),
                ServiceNode(id="svc", label="Payments"),
            ],
            edges=[
                SketchEdge(
                    id="edge_cat_svc",
                    source="cat",
                    target="svc",
                    directed=True,
                    relation="flow",
                )
            ],
        ),
    )

    saved = read_canvas(plot_root, "alpha", "services")
    assert any(edge.source == PROJECT_ANCHOR_ID and edge.target == "cat" for edge in saved.edges)
    assert not any(
        edge.source == PROJECT_ANCHOR_ID and edge.target == "svc" for edge in saved.edges
    )


def test_write_canvas_does_not_duplicate_existing_anchor_spoke(tmp_path: Path) -> None:
    plot_root = _setup(tmp_path)
    canvas = CanvasDoc(
        canvas_id="services",
        canvas_kind="services",
        nodes=[ServiceNode(id="svc", label="Payments")],
        edges=[
            SketchEdge(
                id="edge_anchor_svc",
                source=PROJECT_ANCHOR_ID,
                target="svc",
                directed=True,
                relation="flow",
            )
        ],
    )

    write_canvas(plot_root, "alpha", canvas)
    write_canvas(plot_root, "alpha", read_canvas(plot_root, "alpha", "services"))

    saved = read_canvas(plot_root, "alpha", "services")
    spokes = [
        edge
        for edge in saved.edges
        if edge.source == PROJECT_ANCHOR_ID and edge.target == "svc" and edge.directed
    ]
    assert [edge.id for edge in spokes] == ["edge_anchor_svc"]


def test_existing_foundation_and_entity_anchor_edges_keep_create_edge_format(
    tmp_path: Path,
) -> None:
    plot_root = _setup(tmp_path)

    value = create_node(plot_root, "alpha", "foundation", "core_value", {"label": "Trust"})["node"]
    foundation_spoke = create_edge(
        plot_root, "alpha", "foundation", PROJECT_ANCHOR_ID, value["id"]
    )["edge"]
    entity = create_node(plot_root, "alpha", "entities", "entity", {"label": "Order"})["node"]
    entity_spoke = create_edge(plot_root, "alpha", "entities", PROJECT_ANCHOR_ID, entity["id"])[
        "edge"
    ]

    assert foundation_spoke["relation"] == "flow"
    assert foundation_spoke["sourceHandle"] == "l"
    assert foundation_spoke["targetHandle"] == "r"
    assert entity_spoke["relation"] == "flow"
    assert entity_spoke["sourceHandle"] is None
    assert entity_spoke["targetHandle"] is None
    canvases: tuple[tuple[CanvasKind, str], ...] = (
        ("foundation", value["id"]),
        ("entities", entity["id"]),
    )
    for canvas_kind, target_id in canvases:
        canvas = read_canvas(plot_root, "alpha", canvas_kind)
        assert (
            sum(
                edge.source == PROJECT_ANCHOR_ID and edge.target == target_id
                for edge in canvas.edges
            )
            == 1
        )


def test_write_canvas_hands_back_what_it_saved(tmp_path: Path) -> None:
    # The sweep rebinds a local name, so the caller kept the pre-sweep document
    # and the PUT response carried a canvas with no anchor spoke. The viewer
    # therefore drew nothing until a full reload, and the node the user had just
    # placed looked unattached (novel-workspace O-00000047).
    plot_root = _setup(tmp_path)
    sent = CanvasDoc(
        canvas_id="services",
        canvas_kind="services",
        nodes=[ServiceNode(id="svc", label="Payments")],
    )

    saved = write_canvas(plot_root, "alpha", sent)

    assert [(edge.source, edge.target) for edge in saved.edges] == [(PROJECT_ANCHOR_ID, "svc")]
    assert saved.edges == read_canvas(plot_root, "alpha", "services").edges
    # The caller's own object is untouched — the sweep is not a mutation.
    assert sent.edges == []
