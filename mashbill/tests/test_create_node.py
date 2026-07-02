"""``create_node`` — clobber-safe single-node append (D-2026-06-27-B).

The in-app coach ADDS a node the user confirms is new. ``create_node`` is the
add primitive and the single SSOT for node creation: validate the kind is
creatable on the canvas, mint the id + auto-position server-side, apply only the
kind's writable content fields, append the one node, re-validate the whole
CanvasDoc, write atomically — every other node + edge left untouched. It
generalises the former ``create_master`` (now a thin reference-flow wrapper).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mashbill.folder_io import (
    create_node,
    create_project,
    read_canvas,
    write_canvas,
)
from mashbill.masters import create_master
from mashbill.models import (
    ActorNode,
    ActorRefNode,
    CanvasDoc,
    CoreValueNode,
    FeatureNode,
    IdentityNode,
    MissionNode,
    SketchEdge,
    StepNode,
)
from mashbill.workspace import resolve_plot_root


def _setup(tmp_path: Path) -> Path:
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    return plot_root


def _foundation(plot_root: Path) -> None:
    write_canvas(
        plot_root,
        "alpha",
        CanvasDoc(
            canvas_id="foundation",
            canvas_kind="foundation",
            nodes=[
                MissionNode(id="m1", label="Mission", statement="s"),
                IdentityNode(id="i1", label="Identity"),
            ],
        ),
    )


# --- happy path: append + return shape --------------------------------------


def test_create_node_appends_a_core_value(tmp_path: Path) -> None:
    plot_root = _setup(tmp_path)
    _foundation(plot_root)
    out = create_node(
        plot_root, "alpha", "foundation", "core_value",
        {"label": "정직 (Honesty)", "body": "tell the truth"},
    )
    node = out["node"]
    assert node["kind"] == "core_value"
    assert node["id"].startswith("core_value")
    assert node["label"] == "정직 (Honesty)"
    assert node["body"] == "tell the truth"
    assert "definition" not in node  # v0.45 (D-2026-07-02-A): name + body only
    assert out["rejected_fields"] == []
    canvas = read_canvas(plot_root, "alpha", "foundation")
    kinds = sorted(n.kind for n in canvas.nodes)
    assert kinds == ["core_value", "identity", "mission"]


def test_create_node_returns_node_and_rejected_fields_shape(tmp_path: Path) -> None:
    """Same {node, rejected_fields} contract as update_node; structural / wrong-kind
    fields are rejected, never silently applied (Rule 7)."""
    plot_root = _setup(tmp_path)
    _foundation(plot_root)
    out = create_node(
        plot_root, "alpha", "foundation", "core_value",
        {"label": "관용", "x": 999, "statement": "mission-only field"},
    )
    assert set(out) == {"node", "rejected_fields"}
    # x (structural) + statement (a mission field, not a core_value field) rejected
    assert out["rejected_fields"] == ["statement", "x"]
    # position is server-assigned, NOT the LLM-supplied 999
    assert out["node"]["x"] != 999
    assert "statement" not in out["node"]


# --- clobber-safety ---------------------------------------------------------


def test_create_node_leaves_other_nodes_and_edges_untouched(tmp_path: Path) -> None:
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    write_canvas(
        plot_root, "alpha",
        CanvasDoc(
            canvas_id="svc1", canvas_kind="feature", feature_ref="svc1",
            nodes=[
                FeatureNode(id="svc1", label="Publishing", proposed="p"),
                ActorRefNode(id="ar1", label="Writer", ref_actor_id="a1"),
                StepNode(id="s1", label="Write", outcome="o"),
            ],
            edges=[SketchEdge(id="e1", source="svc1", target="s1")],
        ),
    )
    create_node(plot_root, "alpha", "feature", "step", {"label": "Review"}, service_id="svc1")
    canvas = read_canvas(plot_root, "alpha", "feature", "svc1")
    by_id = {n.id: n for n in canvas.nodes}
    assert by_id["s1"].outcome == "o"  # type: ignore[attr-defined]
    assert [e.id for e in canvas.edges] == ["e1"]
    assert sum(1 for n in canvas.nodes if n.kind == "step") == 2


# --- kind / canvas validation ----------------------------------------------


def test_create_node_rejects_kind_not_creatable_on_canvas(tmp_path: Path) -> None:
    plot_root = _setup(tmp_path)
    _foundation(plot_root)
    with pytest.raises(ValueError):
        create_node(plot_root, "alpha", "foundation", "actor", {"label": "Reader"})


def test_create_node_rejects_project_anchor_kind(tmp_path: Path) -> None:
    """The synthetic project anchor lives in ProjectDoc.anchors — never mint it as
    a node, even though 'project' sits in the foundation allow-list vestigially."""
    plot_root = _setup(tmp_path)
    _foundation(plot_root)
    with pytest.raises(ValueError):
        create_node(plot_root, "alpha", "foundation", "project", {"label": "X"})


def test_create_node_rejects_feature_on_feature_canvas(tmp_path: Path) -> None:
    """The feature canvas's root feature is bootstrapped exogenously; a second
    feature node is never appended here."""
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    write_canvas(
        plot_root, "alpha",
        CanvasDoc(
            canvas_id="svc1", canvas_kind="feature", feature_ref="svc1",
            nodes=[
                FeatureNode(id="svc1", label="Publishing", proposed="p"),
                ActorRefNode(id="ar1", label="Writer", ref_actor_id="a1"),
            ],
        ),
    )
    with pytest.raises(ValueError):
        create_node(
            plot_root, "alpha", "feature", "feature", {"label": "Another"}, service_id="svc1"
        )


# --- position auto-stagger --------------------------------------------------


def test_create_node_staggers_successive_positions(tmp_path: Path) -> None:
    plot_root = _setup(tmp_path)
    _foundation(plot_root)
    a = create_node(plot_root, "alpha", "foundation", "core_value", {"label": "A"})
    b = create_node(plot_root, "alpha", "foundation", "core_value", {"label": "B"})
    # two creates of the same kind must not stack at the identical spot
    assert (a["node"]["x"], a["node"]["y"]) != (b["node"]["x"], b["node"]["y"])


def test_create_node_clusters_with_same_kind_siblings(tmp_path: Path) -> None:
    """B-3 (regression, user report 2026-07-02): a new node must join the visual
    cluster of its OWN kind — not drop at a fixed generic spot ignoring where the
    siblings actually are. Novel's essence is thinking-through-sight, so scattering
    same-kind nodes breaks the tool's whole point. Here an existing core_value
    cluster sits far left; the new core_value must land WITH it, not at the drop lane."""
    plot_root = _setup(tmp_path)
    write_canvas(
        plot_root,
        "alpha",
        CanvasDoc(
            canvas_id="foundation",
            canvas_kind="foundation",
            nodes=[
                MissionNode(id="m1", label="Mission", statement="s"),
                IdentityNode(id="i1", label="Identity"),
                CoreValueNode(id="cv1", label="장인정신", x=-500.0, y=100.0),
                CoreValueNode(id="cv2", label="명료함", x=-500.0, y=200.0),
            ],
        ),
    )
    out = create_node(plot_root, "alpha", "foundation", "core_value", {"label": "흐름"})
    nx, ny = out["node"]["x"], out["node"]["y"]
    assert nx == -500.0  # aligned to the sibling cluster's x, not the generic drop lane
    assert ny > 200.0  # dropped just below the lowest existing sibling
    # a different kind with no siblings still uses the generic lane (unclustered ok)
    ident = create_node(plot_root, "alpha", "foundation", "identity", {"label": "Voice"})
    assert ident["node"]["x"] != -500.0


# --- other canvases ---------------------------------------------------------


def test_create_node_on_actors_canvas(tmp_path: Path) -> None:
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    write_canvas(
        plot_root, "alpha",
        CanvasDoc(
            canvas_id="actors", canvas_kind="actors",
            nodes=[ActorNode(id="a1", label="Operator"), ActorNode(id="a2", label="User")],
        ),
    )
    out = create_node(plot_root, "alpha", "actors", "actor", {"label": "Reviewer"})
    assert out["node"]["kind"] == "actor"
    canvas = read_canvas(plot_root, "alpha", "actors")
    assert sum(1 for n in canvas.nodes if n.kind == "actor") == 3


def test_create_node_on_entities_canvas(tmp_path: Path) -> None:
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    write_canvas(
        plot_root, "alpha",
        CanvasDoc(canvas_id="entities", canvas_kind="entities", nodes=[]),
    )
    out = create_node(
        plot_root, "alpha", "entities", "entity", {"label": "Article", "summary": "a post"}
    )
    assert out["node"]["kind"] == "entity"
    assert out["node"]["summary"] == "a post"


# --- create_master still works (generalisation regression) ------------------


def test_create_master_still_appends_to_home_canvas(tmp_path: Path) -> None:
    """create_master is now a thin wrapper over create_node — its contract
    (returns an id, drops the master on its home canvas) must be unchanged."""
    plot_root = _setup(tmp_path)
    _foundation(plot_root)
    nid = create_master(plot_root, "alpha", "core_value", "Curiosity")
    assert isinstance(nid, str) and nid
    canvas = read_canvas(plot_root, "alpha", "foundation")
    match = next(n for n in canvas.nodes if n.id == nid)
    assert match.kind == "core_value"
    assert match.label == "Curiosity"


def test_create_master_still_rejects_non_master_kind(tmp_path: Path) -> None:
    plot_root = _setup(tmp_path)
    _foundation(plot_root)
    with pytest.raises(ValueError):
        create_master(plot_root, "alpha", "mission", "X")


# --- MCP surface ------------------------------------------------------------


def test_create_node_is_a_registered_mcp_tool() -> None:
    import asyncio

    from mashbill.mcp_tools import mcp

    tool = asyncio.run(mcp.get_tool("create_node"))
    assert tool is not None
    assert tool.name == "create_node"
    props = set(tool.parameters["properties"])
    assert props == {"project_path", "project_id", "canvas_kind", "kind", "fields", "service_id"}
    assert set(tool.parameters["required"]) == {
        "project_path",
        "project_id",
        "canvas_kind",
        "kind",
    }
