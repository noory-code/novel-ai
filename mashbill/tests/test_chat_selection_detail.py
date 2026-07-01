"""Lever 1a — inject the selected node's actual content into the chat context.

The per-turn context used to list only each selected node's kind / label / id
(``docs/idea/chat/00-problem.md``): "polish this mission" reached the agent
*without the mission text*, so it invented one. This renders the selected nodes'
typed text fields (statement / body / definition / …) by reading the canvas
engine-side — the SSOT both delivery layers share — keyed off the single project
under the data root (canonical one-project-per-root layout, D-2026-06-21-AB).
The renderer is generic (dump non-empty text fields, drop structural / visual /
server keys) so a new kind needs no per-kind branch.
"""

from __future__ import annotations

from pathlib import Path

from mashbill.chat_selection import (
    build_turn_preamble,
    render_canvas_map,
    render_cross_canvas_registry,
    render_node_content,
    render_selection_detail,
    render_write_target,
)
from mashbill.folder_io import create_project, write_canvas
from mashbill.models import (
    ActorNode,
    CanvasDoc,
    CoreValueNode,
    EntityNode,
    IdentityNode,
    MissionNode,
    ServiceNode,
    SketchNode,
)
from mashbill.workspace import resolve_plot_root

# --- pure renderer ---------------------------------------------------------


def test_render_node_content_keeps_typed_text_drops_structural() -> None:
    body = render_node_content(
        {
            "kind": "mission",
            "id": "m1",
            "label": "Our mission",
            "x": 10.0,
            "y": 20.0,
            "color": "#ffffff",
            "version": "v1.0",
            "statement": "Make planning effortless",
            "body": "We believe in clarity.",
        }
    )
    assert "Make planning effortless" in body
    assert "We believe in clarity." in body
    # structural / visual / server fields never leak into the body
    assert "10.0" not in body
    assert "#ffffff" not in body
    assert "v1.0" not in body
    # id + label belong to the header line, not the rendered body
    assert "m1" not in body


def test_render_node_content_empty_when_no_typed_text() -> None:
    assert render_node_content({"kind": "project", "id": "p", "label": "P", "x": 0.0}) == ""


def test_render_node_content_drops_underscore_server_keys() -> None:
    out = render_node_content(
        {"kind": "mission", "id": "m", "label": "L", "_dirty": True, "statement": "S"}
    )
    assert "S" in out
    assert "_dirty" not in out


# --- fs-backed selection detail --------------------------------------------


def _mission_canvas() -> CanvasDoc:
    nodes: list[SketchNode] = [
        MissionNode(
            id="m1",
            label="Our mission",
            statement="Make planning effortless",
            body="We believe in clarity.",
        ),
        # Foundation requires ≥1 identity node alongside the mission.
        IdentityNode(id="i1", label="Identity"),
    ]
    return CanvasDoc(canvas_id="foundation", canvas_kind="foundation", nodes=nodes)


def _setup(tmp_path: Path) -> Path:
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    write_canvas(plot_root, "alpha", _mission_canvas())
    return plot_root


def test_selection_detail_injects_node_body(tmp_path: Path) -> None:
    plot_root = _setup(tmp_path)
    out = render_selection_detail(
        plot_root, "foundation", [{"id": "m1", "kind": "mission", "label": "Our mission"}]
    )
    assert "Make planning effortless" in out
    assert "We believe in clarity." in out
    assert "m1" in out  # header still names the node


def test_selection_detail_empty_for_project_scope(tmp_path: Path) -> None:
    plot_root = _setup(tmp_path)
    out = render_selection_detail(
        plot_root, "project", [{"id": "m1", "kind": "mission", "label": "x"}]
    )
    assert out == ""


def test_selection_detail_graceful_when_node_absent(tmp_path: Path) -> None:
    plot_root = _setup(tmp_path)
    out = render_selection_detail(
        plot_root, "foundation", [{"id": "ghost", "kind": "mission", "label": "x"}]
    )
    assert out == ""


def test_selection_detail_empty_when_no_project(tmp_path: Path) -> None:
    plot_root = resolve_plot_root(str(tmp_path))  # no create_project
    out = render_selection_detail(
        plot_root, "foundation", [{"id": "m1", "kind": "mission", "label": "x"}]
    )
    assert out == ""


# --- active canvas map (Phase 2a) ------------------------------------------


def _two_value_canvas() -> CanvasDoc:
    nodes: list[SketchNode] = [
        MissionNode(id="m1", label="Our mission", statement="Make planning effortless"),
        IdentityNode(id="i1", label="Identity"),
        CoreValueNode(id="v1", label="Clarity", definition="Always favour the clear path"),
        CoreValueNode(id="v2", label="Trust", definition="Default to candour"),
    ]
    return CanvasDoc(canvas_id="foundation", canvas_kind="foundation", nodes=nodes)


def test_canvas_map_lists_every_node(tmp_path: Path) -> None:
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    write_canvas(plot_root, "alpha", _two_value_canvas())
    out = render_canvas_map(plot_root, "foundation", [])
    # all four authored nodes appear by label
    for label in ("Our mission", "Identity", "Clarity", "Trust"):
        assert label in out
    assert "foundation" in out  # canvas named in the header


def test_canvas_map_marks_selected_nodes(tmp_path: Path) -> None:
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    write_canvas(plot_root, "alpha", _two_value_canvas())
    out = render_canvas_map(
        plot_root, "foundation", [{"id": "v1", "kind": "core_value", "label": "Clarity"}]
    )
    # the selected node carries a marker the others don't
    selected_line = next(line for line in out.splitlines() if "Clarity" in line)
    trust_line = next(line for line in out.splitlines() if "Trust" in line)
    assert "selected" in selected_line.lower()
    assert "selected" not in trust_line.lower()


def test_canvas_map_empty_for_project_scope(tmp_path: Path) -> None:
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    write_canvas(plot_root, "alpha", _two_value_canvas())
    assert render_canvas_map(plot_root, "project", []) == ""


def test_canvas_map_empty_when_no_project(tmp_path: Path) -> None:
    plot_root = resolve_plot_root(str(tmp_path))
    assert render_canvas_map(plot_root, "foundation", []) == ""


# --- cross-canvas registry (Phase 2b) --------------------------------------


def _actors_canvas() -> CanvasDoc:
    nodes: list[SketchNode] = [
        ActorNode(id="a1", label="Operator"),
        ActorNode(id="a2", label="Reader"),
    ]
    return CanvasDoc(canvas_id="actors", canvas_kind="actors", nodes=nodes)


def _entities_canvas() -> CanvasDoc:
    nodes: list[SketchNode] = [
        EntityNode(id="e1", label="Post", summary="A published article"),
    ]
    return CanvasDoc(canvas_id="entities", canvas_kind="entities", nodes=nodes)


def _setup_registry(tmp_path: Path) -> Path:
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    write_canvas(plot_root, "alpha", _actors_canvas())
    write_canvas(plot_root, "alpha", _entities_canvas())
    return plot_root


def test_registry_lists_actors_and_entities_on_feature_scope(tmp_path: Path) -> None:
    plot_root = _setup_registry(tmp_path)
    out = render_cross_canvas_registry(plot_root, "feature:svc1")
    assert "Operator" in out and "Reader" in out
    assert "Post" in out and "A published article" in out


def test_registry_lists_actors_on_services_scope(tmp_path: Path) -> None:
    plot_root = _setup_registry(tmp_path)
    out = render_cross_canvas_registry(plot_root, "services")
    assert "Operator" in out


def test_registry_empty_on_foundation_scope(tmp_path: Path) -> None:
    plot_root = _setup_registry(tmp_path)
    # foundation is about essence — it doesn't reference actors/entities.
    assert render_cross_canvas_registry(plot_root, "foundation") == ""


def test_registry_empty_when_no_project(tmp_path: Path) -> None:
    plot_root = resolve_plot_root(str(tmp_path))
    assert render_cross_canvas_registry(plot_root, "feature:x") == ""


def test_registry_lists_actors_on_service_scope(tmp_path: Path) -> None:
    """Per-service thread (D-2026-06-26-A): a ``service:<id>`` thread references
    its actors, so it gets the same registry as the ``services`` canvas."""
    plot_root = _setup_registry(tmp_path)
    out = render_cross_canvas_registry(plot_root, "service:svc1")
    assert "Operator" in out


def test_canvas_map_for_service_scope_reads_services_canvas(tmp_path: Path) -> None:
    """A ``service:<id>`` thread sits on the Services canvas, so its canvas map
    shows that canvas (the id names the selected service, not a sub-canvas)."""
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    write_canvas(
        plot_root,
        "alpha",
        CanvasDoc(
            canvas_id="services",
            canvas_kind="services",
            nodes=[ServiceNode(id="svc1", label="Publishing")],
        ),
    )
    out = render_canvas_map(plot_root, "service:svc1", [])
    assert "Publishing" in out


# --- context-provider seam (D-2026-06-17-L) --------------------------------


def test_turn_preamble_composes_map_registry_and_detail(tmp_path: Path) -> None:
    """The single per-turn assembly point: active-canvas map → cross-canvas
    registry → selected-node detail, in that order."""
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    write_canvas(plot_root, "alpha", _mission_canvas())
    write_canvas(plot_root, "alpha", _actors_canvas())
    sel = [{"id": "m1", "kind": "mission", "label": "Our mission"}]
    out = build_turn_preamble(plot_root, "services", sel)
    # registry (services scope) appears; for a feature/services scope the
    # actor registry is present, and the canvas map header leads.
    assert "[Canvas: services]" in out or "[Novel context]" in out
    assert "Existing actors" in out  # registry composed in


def test_turn_preamble_empty_for_project_scope_without_selection(tmp_path: Path) -> None:
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    write_canvas(plot_root, "alpha", _mission_canvas())
    assert build_turn_preamble(plot_root, "project", []) == ""


def test_turn_preamble_includes_selected_detail(tmp_path: Path) -> None:
    plot_root = _setup(tmp_path)  # foundation with the mission node
    sel = [{"id": "m1", "kind": "mission", "label": "Our mission"}]
    out = build_turn_preamble(plot_root, "foundation", sel)
    assert "Make planning effortless" in out  # the selected node's body


# --- writable-field schema (D-2026-06-26-D) --------------------------------


def test_selection_detail_lists_writable_fields(tmp_path: Path) -> None:
    """The agent must know which fields it can write into the selected node."""
    plot_root = _setup(tmp_path)
    out = render_selection_detail(
        plot_root, "foundation", [{"id": "m1", "kind": "mission", "label": "Our mission"}]
    )
    assert "writable" in out.lower()
    assert "statement" in out and "body" in out


def test_selection_detail_shows_empty_node_writable_fields(tmp_path: Path) -> None:
    """A BLANK selected node (the exact 'mission won't fill' case) renders no
    content, but must still announce its writable fields so the coach can fill
    it — otherwise the agent has no field names to write to."""
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    write_canvas(
        plot_root,
        "alpha",
        CanvasDoc(
            canvas_id="foundation",
            canvas_kind="foundation",
            nodes=[
                MissionNode(id="m1", label=""),  # blank mission
                IdentityNode(id="i1", label="Identity"),
            ],
        ),
    )
    out = render_selection_detail(
        plot_root, "foundation", [{"id": "m1", "kind": "mission", "label": ""}]
    )
    assert "m1" in out  # the blank node still appears
    assert "statement" in out and "body" in out  # its writable fields are named


# --- write target (D-2026-06-26-D) -----------------------------------------


def test_turn_preamble_write_target_carries_ids(tmp_path: Path) -> None:
    plot_root = _setup(tmp_path)
    sel = [{"id": "m1", "kind": "mission", "label": "Our mission"}]
    out = build_turn_preamble(plot_root, "foundation", sel, project_path=str(tmp_path))
    assert "[Write target]" in out
    assert "update_node" in out


def test_write_target_block_names_each_id(tmp_path: Path) -> None:
    """Scope the id assertions to the write-target block itself — a substring
    check over the whole preamble would also pass on the canvas-map header, so it
    couldn't catch the block dropping an id."""
    plot_root = _setup(tmp_path)
    block = render_write_target(plot_root, "foundation", str(tmp_path))
    assert block.startswith("[Write target]")
    assert "project_id='alpha'" in block
    assert "canvas_kind='foundation'" in block
    assert f"project_path={str(tmp_path)!r}" in block


def test_render_write_target_bare_feature_is_empty(tmp_path: Path) -> None:
    """Bare ``feature`` (no service_id) names no canvas — emit nothing rather than
    an instruction update_node would reject."""
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    assert render_write_target(plot_root, "feature", str(tmp_path)) == ""


def test_render_write_target_feature_scope_includes_service_id(tmp_path: Path) -> None:
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    block = render_write_target(plot_root, "feature:svc1", str(tmp_path))
    assert "canvas_kind='feature'" in block
    assert "service_id='svc1'" in block


def test_turn_preamble_write_target_absent_without_project_path(tmp_path: Path) -> None:
    """No project_path passed (e.g. older caller) → no write-target block, never
    a half-formed one the agent can't use."""
    plot_root = _setup(tmp_path)
    sel = [{"id": "m1", "kind": "mission", "label": "Our mission"}]
    out = build_turn_preamble(plot_root, "foundation", sel)
    assert "[Write target]" not in out


def test_turn_preamble_write_target_absent_on_project_scope(tmp_path: Path) -> None:
    """The cross-canvas project scope has no single target canvas."""
    plot_root = _setup(tmp_path)
    out = build_turn_preamble(plot_root, "project", [], project_path=str(tmp_path))
    assert "[Write target]" not in out


def test_turn_preamble_write_target_feature_scope_has_service_id(tmp_path: Path) -> None:
    """A feature canvas write needs service_id; the parametric scope carries it."""
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    out = build_turn_preamble(plot_root, "feature:svc1", [], project_path=str(tmp_path))
    assert "[Write target]" in out
    assert "feature" in out
    assert "svc1" in out  # service_id
