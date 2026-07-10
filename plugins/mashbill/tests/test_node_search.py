"""Project-wide node name search — the "이름" context entry point (D-2026-06-20-P).

The context entry-point chain is selection → map → **name** → (last) semantic
search. Selection + map are per-turn injection; name search lets the agent jump
to a node it knows by name but isn't on the active canvas ("the comment
feature"). This is a title/id index over labels — NOT vector search (the data is
already a graph; D-2026-06-20-P §1.2). These tests pin the cross-canvas scan +
case-insensitive label match + bound.
"""

from __future__ import annotations

from pathlib import Path

from mashbill.folder_io import create_project, write_canvas
from mashbill.models import (
    ActorNode,
    ActorRefNode,
    CanvasDoc,
    CategoryNode,
    FeatureNode,
    IdentityNode,
    MissionNode,
    ServiceNode,
    SketchNode,
)
from mashbill.node_search import search_nodes
from mashbill.workspace import resolve_plot_root


def _foundation() -> CanvasDoc:
    nodes: list[SketchNode] = [
        MissionNode(id="m1", label="Our mission", statement="x"),
        IdentityNode(id="i1", label="Warm host"),
    ]
    return CanvasDoc(canvas_id="foundation", canvas_kind="foundation", nodes=nodes)


def _actors() -> CanvasDoc:
    nodes: list[SketchNode] = [
        ActorNode(id="a1", label="Operator"),
        ActorNode(id="a2", label="Reader"),
    ]
    return CanvasDoc(canvas_id="actors", canvas_kind="actors", nodes=nodes)


def _services() -> CanvasDoc:
    nodes: list[SketchNode] = [
        CategoryNode(id="c1", label="Default"),
        ServiceNode(id="s1", parent_id="c1", label="Commenting"),
        FeatureNode(id="f_comment", parent_id="s1", label="Post a comment"),
    ]
    return CanvasDoc(canvas_id="services", canvas_kind="services", nodes=nodes)


def _setup(tmp_path: Path) -> Path:
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    write_canvas(plot_root, "alpha", _foundation())
    write_canvas(plot_root, "alpha", _actors())
    write_canvas(plot_root, "alpha", _services())
    return plot_root


def test_search_finds_node_by_label_across_canvases(tmp_path: Path) -> None:
    plot_root = _setup(tmp_path)
    hits = search_nodes(plot_root, "alpha", "comment")
    labels = {h["label"] for h in hits}
    # both the "Commenting" service and the "Post a comment" feature match
    assert "Commenting" in labels
    assert "Post a comment" in labels


def test_search_is_case_insensitive(tmp_path: Path) -> None:
    plot_root = _setup(tmp_path)
    hits = search_nodes(plot_root, "alpha", "OPERATOR")
    assert any(h["label"] == "Operator" and h["kind"] == "actor" for h in hits)


def test_search_hit_carries_id_kind_label_canvas(tmp_path: Path) -> None:
    plot_root = _setup(tmp_path)
    hit = next(h for h in search_nodes(plot_root, "alpha", "Operator"))
    assert set(hit) >= {"id", "kind", "label", "canvas"}
    assert hit["canvas"] == "actors"


def test_search_includes_feature_detail_canvases(tmp_path: Path) -> None:
    plot_root = _setup(tmp_path)
    # seed a detail canvas with a step so the scan reaches feature details
    detail = CanvasDoc(
        canvas_id="f_comment",
        canvas_kind="feature",
        feature_ref="f_comment",
        nodes=[
            FeatureNode(id="f_comment", label="Post a comment", is_root=True),
            ActorRefNode(id="ar1", ref_actor_id="a2", label="Reader"),
        ],
    )
    write_canvas(plot_root, "alpha", detail)
    hits = search_nodes(plot_root, "alpha", "Post a comment")
    assert any(h["canvas"].startswith("feature:") for h in hits)


def test_empty_query_returns_nothing(tmp_path: Path) -> None:
    plot_root = _setup(tmp_path)
    assert search_nodes(plot_root, "alpha", "   ") == []


def test_search_is_bounded(tmp_path: Path) -> None:
    plot_root = _setup(tmp_path)
    hits = search_nodes(plot_root, "alpha", "o", limit=2)  # 'o' matches many
    assert len(hits) <= 2
