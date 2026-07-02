"""``update_node`` — granular, clobber-safe single-node content patch.

The in-app coach saves a confirmed value into the node the user has selected
(D-2026-06-26-D). ``update_node`` is the write primitive: read-modify-write of
ONE node's content fields (``label`` + the kind's typed text), re-validated
against its kind and written through ``write_canvas`` so every CanvasDoc
invariant still holds. Visual / structural / server fields are never patchable
(no silent move / recolour / restructure — Rule 7), and every other node is
left untouched (a concurrent user edit elsewhere is never clobbered).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mashbill.canvas_io import _WRITABLE_CONTENT_FIELDS
from mashbill.folder_io import (
    create_project,
    read_canvas,
    update_node,
    writable_node_fields,
    write_canvas,
)
from mashbill.models import (
    ActorRefNode,
    CanvasDoc,
    EntityNode,
    FeatureNode,
    IdentityNode,
    MissionNode,
    ServiceNode,
    SketchEdge,
    SketchNode,
    StepNode,
)
from mashbill.models_foundation import PROJECT_ANCHOR_ID
from mashbill.workspace import resolve_plot_root


def _mission_canvas() -> CanvasDoc:
    nodes: list[SketchNode] = [
        MissionNode(id="m1", label="Mission", statement="old statement", body="old body"),
        IdentityNode(id="i1", label="Identity"),
    ]
    return CanvasDoc(canvas_id="foundation", canvas_kind="foundation", nodes=nodes)


def _setup(tmp_path: Path) -> Path:
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    write_canvas(plot_root, "alpha", _mission_canvas())
    return plot_root


# --- writable_node_fields (the SSOT for "what a coach may patch") -----------


def test_writable_fields_are_label_plus_typed_text() -> None:
    fields = set(writable_node_fields(MissionNode(id="m", label="x")))
    assert fields == {"label", "statement", "body"}


def test_writable_fields_exclude_structural_and_server() -> None:
    fields = set(writable_node_fields(MissionNode(id="m", label="x")))
    for protected in ("id", "kind", "x", "y", "width", "height", "color", "shape", "version"):
        assert protected not in fields


def test_writable_fields_per_kind_are_prose_only() -> None:
    """Regression (D-2026-06-26-D red-team): the first cut deny-listed only base
    fields, so per-kind reference / lifecycle / structural fields leaked as
    writable. The allow-list must expose ONLY ``label`` + the kind's prose."""
    assert set(writable_node_fields(EntityNode(id="e", label="x"))) == {"label", "summary"}
    assert set(writable_node_fields(ServiceNode(id="s", label="x"))) == {
        "label",
        "problem",
        "value_created",
    }
    assert set(writable_node_fields(StepNode(id="st", label="x"))) == {"label", "outcome", "body"}
    # identity: prose only — NOT the derive→confirm lifecycle (status / provenance)
    idf = set(writable_node_fields(IdentityNode(id="i", label="x")))
    assert idf == {"label", "description", "body"}
    assert "status" not in idf and "provenance" not in idf
    # actor_ref is a read-only anchor — its master pointer + side are NOT writable
    arf = set(writable_node_fields(ActorRefNode(id="ar", label="x", ref_actor_id="a1")))
    assert arf == {"label"}
    assert "ref_actor_id" not in arf and "side" not in arf
    # service reference id arrays are NOT writable
    svc = set(writable_node_fields(ServiceNode(id="s2", label="x")))
    for ref in ("ref_actor_ids", "ref_value_ids", "ref_identity_ids"):
        assert ref not in svc


def test_writable_map_covers_every_union_kind() -> None:
    """Fail-safe guard: a new node kind added to the union without a writable
    classification fails here, forcing the content-vs-structural decision instead
    of silently leaking every new field as writable."""
    import typing

    from mashbill.models_union import SketchNode as _Union

    members = typing.get_args(typing.get_args(_Union)[0])
    kinds = {cls.model_fields["kind"].default for cls in members}
    assert kinds == set(_WRITABLE_CONTENT_FIELDS), (
        f"missing: {kinds - set(_WRITABLE_CONTENT_FIELDS)}, "
        f"extra: {set(_WRITABLE_CONTENT_FIELDS) - kinds}"
    )


# --- update_node: the happy path -------------------------------------------


def test_update_node_patches_typed_field(tmp_path: Path) -> None:
    plot_root = _setup(tmp_path)
    update_node(plot_root, "alpha", "foundation", "m1", {"statement": "new statement"})
    canvas = read_canvas(plot_root, "alpha", "foundation")
    mission = next(n for n in canvas.nodes if n.id == "m1")
    assert mission.statement == "new statement"  # type: ignore[attr-defined]


def test_update_node_merges_only_given_fields(tmp_path: Path) -> None:
    """Patching ``statement`` must leave ``body`` (and ``label``) intact."""
    plot_root = _setup(tmp_path)
    update_node(plot_root, "alpha", "foundation", "m1", {"statement": "fresh"})
    canvas = read_canvas(plot_root, "alpha", "foundation")
    mission = next(n for n in canvas.nodes if n.id == "m1")
    assert mission.statement == "fresh"  # type: ignore[attr-defined]
    assert mission.body == "old body"  # type: ignore[attr-defined]
    assert mission.label == "Mission"


def test_update_node_can_set_label(tmp_path: Path) -> None:
    plot_root = _setup(tmp_path)
    update_node(plot_root, "alpha", "foundation", "m1", {"label": "Renamed"})
    canvas = read_canvas(plot_root, "alpha", "foundation")
    mission = next(n for n in canvas.nodes if n.id == "m1")
    assert mission.label == "Renamed"


# --- clobber-safety ---------------------------------------------------------


def test_update_node_leaves_other_nodes_untouched(tmp_path: Path) -> None:
    plot_root = _setup(tmp_path)
    update_node(plot_root, "alpha", "foundation", "m1", {"statement": "x"})
    canvas = read_canvas(plot_root, "alpha", "foundation")
    # the identity node + its label survive unchanged
    assert any(n.id == "i1" and n.label == "Identity" for n in canvas.nodes)
    assert len(canvas.nodes) == 2


# --- guards: structural / server fields are never patchable -----------------


def test_update_node_ignores_structural_fields(tmp_path: Path) -> None:
    """Position / colour / kind must not change — a coach can't silently move,
    recolour, or retype a node (Rule 7). They are reported as rejected."""
    plot_root = _setup(tmp_path)
    result = update_node(
        plot_root,
        "alpha",
        "foundation",
        "m1",
        {"statement": "ok", "x": 999.0, "color": "#ff0000", "kind": "identity"},
    )
    canvas = read_canvas(plot_root, "alpha", "foundation")
    mission = next(n for n in canvas.nodes if n.id == "m1")
    assert mission.statement == "ok"  # type: ignore[attr-defined]
    assert mission.x == 0.0  # default, unchanged
    assert mission.color == "#ffffff"  # default, unchanged
    assert mission.kind == "mission"  # discriminator unchanged
    assert set(result["rejected_fields"]) == {"x", "color", "kind"}


def test_update_node_ignores_underscore_server_fields(tmp_path: Path) -> None:
    plot_root = _setup(tmp_path)
    result = update_node(
        plot_root, "alpha", "foundation", "m1", {"body": "b", "_publish_baseline": {"x": 1}}
    )
    assert "_publish_baseline" in result["rejected_fields"]


# --- guards: missing target -------------------------------------------------


def test_update_node_raises_for_absent_node(tmp_path: Path) -> None:
    plot_root = _setup(tmp_path)
    with pytest.raises(ValueError, match="not found"):
        update_node(plot_root, "alpha", "foundation", "ghost", {"statement": "x"})


def test_update_node_raises_for_project_anchor(tmp_path: Path) -> None:
    """The synthetic project anchor lives in ProjectDoc.anchors, not nodes —
    targeting it is an error, never a silent no-op or a stray node."""
    plot_root = _setup(tmp_path)
    with pytest.raises(ValueError, match="not found"):
        update_node(plot_root, "alpha", "foundation", PROJECT_ANCHOR_ID, {"statement": "x"})


# --- guards: empty / invalid patch ------------------------------------------


def test_update_node_raises_when_no_writable_field(tmp_path: Path) -> None:
    plot_root = _setup(tmp_path)
    with pytest.raises(ValueError, match="writable"):
        update_node(plot_root, "alpha", "foundation", "m1", {"x": 1.0, "color": "#000"})


def test_update_node_rejects_unknown_field_but_applies_known(tmp_path: Path) -> None:
    """A typo'd field name is reported (Fail Fast) rather than silently dropped,
    while a valid field in the same call still lands."""
    plot_root = _setup(tmp_path)
    result = update_node(
        plot_root, "alpha", "foundation", "m1", {"statement": "ok", "stetement": "typo"}
    )
    canvas = read_canvas(plot_root, "alpha", "foundation")
    mission = next(n for n in canvas.nodes if n.id == "m1")
    assert mission.statement == "ok"  # type: ignore[attr-defined]
    assert "stetement" in result["rejected_fields"]


def test_update_node_raises_on_wrong_field_type(tmp_path: Path) -> None:
    """Re-validation against the kind catches a type error (statement is text)."""
    plot_root = _setup(tmp_path)
    with pytest.raises(Exception):  # noqa: B017 — pydantic ValidationError or ValueError
        update_node(plot_root, "alpha", "foundation", "m1", {"statement": ["not", "text"]})


# --- guards: per-kind reference / lifecycle fields are rejected at write -----


def test_update_node_rejects_identity_lifecycle_fields(tmp_path: Path) -> None:
    """A coach must not lock the identity derive→confirm lifecycle or rewrite its
    derivation lineage via a content patch (D-2026-06-26-D red-team)."""
    plot_root = _setup(tmp_path)
    result = update_node(
        plot_root,
        "alpha",
        "foundation",
        "i1",
        {"description": "ok", "status": "confirmed", "provenance": ["forged"]},
    )
    canvas = read_canvas(plot_root, "alpha", "foundation")
    identity = next(n for n in canvas.nodes if n.id == "i1")
    assert identity.description == "ok"  # type: ignore[attr-defined]
    assert identity.status == "manual"  # type: ignore[attr-defined]  # unchanged default
    assert identity.provenance == []  # type: ignore[attr-defined]  # unchanged
    assert set(result["rejected_fields"]) == {"status", "provenance"}


def test_update_node_rejects_service_reference_arrays(tmp_path: Path) -> None:
    """A coach must not repoint a service's actor/value/identity references via a
    content patch — those are the pick-or-create flow's job."""
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    write_canvas(
        plot_root,
        "alpha",
        CanvasDoc(
            canvas_id="services",
            canvas_kind="services",
            nodes=[ServiceNode(id="svc1", label="Publish", problem="old")],
        ),
    )
    result = update_node(
        plot_root,
        "alpha",
        "services",
        "svc1",
        {"problem": "new", "ref_actor_ids": ["ghost"], "ref_value_ids": ["nope"]},
    )
    canvas = read_canvas(plot_root, "alpha", "services")
    svc = next(n for n in canvas.nodes if n.id == "svc1")
    assert svc.problem == "new"  # type: ignore[attr-defined]
    assert svc.ref_actor_ids == []  # type: ignore[attr-defined]  # not repointed
    assert set(result["rejected_fields"]) == {"ref_actor_ids", "ref_value_ids"}


# --- feature canvas (the only canvas needing service_id) + clobber-safety ----


def _feature_canvas() -> CanvasDoc:
    return CanvasDoc(
        canvas_id="svc1",
        canvas_kind="feature",
        feature_ref="svc1",
        nodes=[
            FeatureNode(id="svc1", label="Publishing", proposed="old proposed"),
            ActorRefNode(id="ar1", label="Writer", ref_actor_id="a1"),
            StepNode(id="s1", label="Write", outcome="old outcome"),
        ],
        edges=[SketchEdge(id="e1", source="svc1", target="s1")],
    )


def test_update_node_on_feature_canvas_threads_service_id(tmp_path: Path) -> None:
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    write_canvas(plot_root, "alpha", _feature_canvas())
    update_node(plot_root, "alpha", "feature", "s1", {"outcome": "new outcome"}, service_id="svc1")
    canvas = read_canvas(plot_root, "alpha", "feature", "svc1")
    step = next(n for n in canvas.nodes if n.id == "s1")
    assert step.outcome == "new outcome"  # type: ignore[attr-defined]
    # the edge survives the single-node patch (clobber-safety contract)
    assert [e.id for e in canvas.edges] == ["e1"]
    assert canvas.edges[0].source == "svc1" and canvas.edges[0].target == "s1"


def test_update_node_feature_without_service_id_does_not_patch(tmp_path: Path) -> None:
    """Omitting service_id must not silently land the write somewhere wrong."""
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    write_canvas(plot_root, "alpha", _feature_canvas())
    with pytest.raises(Exception):  # noqa: B017 — feature read needs a service_id
        update_node(plot_root, "alpha", "feature", "s1", {"outcome": "x"})


def test_update_node_preserves_publish_baseline_on_all_nodes(tmp_path: Path) -> None:
    """A server-managed publish baseline on the patched node AND on other nodes
    survives the read-modify-write round-trip."""
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    write_canvas(
        plot_root,
        "alpha",
        CanvasDoc(
            canvas_id="foundation",
            canvas_kind="foundation",
            nodes=[
                MissionNode(id="m1", label="M", statement="s", publish_baseline={"statement": "s"}),
                IdentityNode(id="i1", label="I", publish_baseline={"description": "d"}),
            ],
        ),
    )
    update_node(plot_root, "alpha", "foundation", "m1", {"statement": "s2"})
    canvas = read_canvas(plot_root, "alpha", "foundation")
    by_id = {n.id: n for n in canvas.nodes}
    assert by_id["m1"].publish_baseline is not None  # type: ignore[attr-defined]
    assert by_id["i1"].publish_baseline is not None  # type: ignore[attr-defined]


# --- MCP surface ------------------------------------------------------------


def test_update_node_is_a_registered_mcp_tool() -> None:
    """The agent calls ``mcp__mashbill__update_node`` — it must be registered with the
    right call contract, else the write path is unreachable / mis-shaped."""
    import asyncio

    from mashbill.mcp_tools import mcp

    tool = asyncio.run(mcp.get_tool("update_node"))
    assert tool is not None
    assert tool.name == "update_node"
    props = set(tool.parameters["properties"])
    assert props == {"project_path", "project_id", "canvas_kind", "node_id", "fields", "service_id"}
    # service_id is the only optional arg
    assert set(tool.parameters["required"]) == {
        "project_path",
        "project_id",
        "canvas_kind",
        "node_id",
        "fields",
    }


# --- set_node_references (D-2026-07-02-N) ------------------------------------


def _ref_fixture(tmp_path: Path) -> Path:
    from mashbill.models import ActorNode, ServiceNode

    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    write_canvas(
        plot_root, "alpha",
        CanvasDoc(canvas_id="actors", canvas_kind="actors",
                  nodes=[ActorNode(id="a1", label="사장님"), ActorNode(id="a2", label="손님")]),
    )
    write_canvas(
        plot_root, "alpha",
        CanvasDoc(canvas_id="services", canvas_kind="services",
                  nodes=[ServiceNode(id="s1", label="주문")]),
    )
    return plot_root


def test_set_node_references_fills_service_actor_refs(tmp_path: Path) -> None:
    """Benchmark finding (2026-07-02): service reference slots stayed 0/N in
    every run — the playbook told the coach to fill them but ref_* fields are
    (rightly) protected from free-text update_node and NO tool could set them.
    ``set_node_references`` assigns them explicitly: allow-listed ref fields
    per kind, every referenced id validated on its home canvas."""
    from mashbill.references import set_node_references

    plot_root = _ref_fixture(tmp_path)
    out = set_node_references(
        plot_root, "alpha", "services", "s1", {"ref_actor_ids": ["a1", "a2"]}
    )
    assert out["node"]["ref_actor_ids"] == ["a1", "a2"]
    canvas = read_canvas(plot_root, "alpha", "services")
    svc = next(n for n in canvas.nodes if n.id == "s1")
    assert svc.ref_actor_ids == ["a1", "a2"]  # type: ignore[attr-defined]


def test_set_node_references_rejects_unknown_master(tmp_path: Path) -> None:
    from mashbill.references import set_node_references

    plot_root = _ref_fixture(tmp_path)
    with pytest.raises(ValueError, match="ghost"):
        set_node_references(plot_root, "alpha", "services", "s1", {"ref_actor_ids": ["ghost"]})


def test_set_node_references_rejects_non_ref_field(tmp_path: Path) -> None:
    from mashbill.references import set_node_references

    plot_root = _ref_fixture(tmp_path)
    with pytest.raises(ValueError, match="not a reference field"):
        set_node_references(plot_root, "alpha", "services", "s1", {"problem": "hijack"})


def test_write_playbook_mentions_set_node_references() -> None:
    from mashbill.chat_context import WRITE_PLAYBOOK

    assert "set_node_references" in WRITE_PLAYBOOK
