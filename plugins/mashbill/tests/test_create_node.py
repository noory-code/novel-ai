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
from typing import get_args

import pytest

import mashbill.canvas_io as canvas_io
from mashbill.field_policy import CREATE_TIME_REFS
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
    ServiceNode,
    SketchEdge,
    StepNode,
)
from mashbill.models_canvas import CanvasKind
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
        plot_root,
        "alpha",
        "foundation",
        "core_value",
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
        plot_root,
        "alpha",
        "foundation",
        "core_value",
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
        plot_root,
        "alpha",
        CanvasDoc(
            canvas_id="svc1",
            canvas_kind="feature",
            feature_ref="svc1",
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
    assert isinstance(by_id["s1"], StepNode)
    assert by_id["s1"].outcome == "o"
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
        plot_root,
        "alpha",
        CanvasDoc(
            canvas_id="svc1",
            canvas_kind="feature",
            feature_ref="svc1",
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


# --- actor_ref: the create-time pick ----------------------------------------


def _feature_canvas_with_actor(plot_root: Path) -> None:
    """A feature canvas plus the actor master its anchor can point at."""
    write_canvas(
        plot_root,
        "alpha",
        CanvasDoc(
            canvas_id="actors",
            canvas_kind="actors",
            nodes=[ActorNode(id="actor_writer", label="Writer")],
        ),
    )
    write_canvas(
        plot_root,
        "alpha",
        CanvasDoc(
            canvas_id="svc1",
            canvas_kind="feature",
            feature_ref="svc1",
            nodes=[FeatureNode(id="svc1", label="Publishing", proposed="p")],
        ),
    )


_CANVAS_KINDS = get_args(CanvasKind)

_CREATABLE_NODE_CASES = [
    pytest.param(
        canvas_kind,
        node_kind,
        id=f"{canvas_kind}-{node_kind}",
    )
    for canvas_kind in _CANVAS_KINDS
    for node_kind in sorted(canvas_io.creatable_kinds(canvas_kind))
]


@pytest.mark.parametrize("canvas_kind", _CANVAS_KINDS)
def test_every_canvas_kind_has_a_creatable_node_kind(canvas_kind: CanvasKind) -> None:
    assert canvas_io.creatable_kinds(canvas_kind), (
        f"{canvas_kind!r} advertises no creatable node kinds"
    )


@pytest.mark.parametrize(("canvas_kind", "node_kind"), _CREATABLE_NODE_CASES)
def test_every_advertised_creatable_node_can_be_created(
    tmp_path: Path, canvas_kind: CanvasKind, node_kind: str
) -> None:
    # Sweep the advertised contract so another actor_ref-style create failure
    # cannot stay hidden while simulations keep selecting the broken kind.
    plot_root = _setup(tmp_path)
    create_time_ref = CREATE_TIME_REFS.get(node_kind)
    needs_feature_canvas = canvas_kind == "feature" or (
        create_time_ref is not None and create_time_ref[1] == "feature"
    )
    if needs_feature_canvas:
        _feature_canvas_with_actor(plot_root)
    service_id = "svc1" if canvas_kind == "feature" else None

    fields = {"label": f"Created {node_kind}"}
    if create_time_ref is not None:
        ref_field, home_canvas = create_time_ref
        ref_kind = ref_field.removeprefix("ref_").removesuffix("_id")
        home_service_id = service_id if home_canvas == "feature" else None
        home = read_canvas(plot_root, "alpha", home_canvas, home_service_id)
        target = next((node for node in home.nodes if node.kind == ref_kind), None)
        if target is None:
            target_out = create_node(
                plot_root,
                "alpha",
                home_canvas,
                ref_kind,
                {"label": f"Referenced {ref_kind}"},
                service_id=home_service_id,
            )
            target_id = target_out["node"]["id"]
        else:
            target_id = target.id
        fields[ref_field] = target_id

    out = create_node(
        plot_root,
        "alpha",
        canvas_kind,
        node_kind,
        fields,
        service_id=service_id,
    )

    assert out["node"]["kind"] == node_kind
    assert out["rejected_fields"] == []
    persisted = read_canvas(plot_root, "alpha", canvas_kind, service_id)
    match = next(
        (node for node in persisted.nodes if node.id == out["node"]["id"]),
        None,
    )
    assert match is not None, (
        f"created {canvas_kind}/{node_kind} node {out['node']['id']!r} was not persisted"
    )
    assert match.kind == node_kind


def test_create_node_takes_the_actor_pick_when_creating_an_actor_ref(tmp_path: Path) -> None:
    # ``actor_ref`` is advertised as creatable on the feature canvas, but the
    # anchor it needs (``ref_actor_id``) sat behind the writable-content
    # allow-list, so the seed never validated and EVERY create failed. The
    # protection exists to stop a coach REPOINTING an anchor after the fact
    # (D-2026-06-26-D); choosing the target while creating it is the pick that
    # protection assumed would happen elsewhere. Novel's flows carried no actor
    # at all because of this (novel-workspace O-25).
    plot_root = _setup(tmp_path)
    _feature_canvas_with_actor(plot_root)

    out = create_node(
        plot_root,
        "alpha",
        "feature",
        "actor_ref",
        {"label": "Writer", "ref_actor_id": "actor_writer"},
        service_id="svc1",
    )

    assert out["node"]["kind"] == "actor_ref"
    assert out["node"]["ref_actor_id"] == "actor_writer"
    assert out["rejected_fields"] == []
    canvas = read_canvas(plot_root, "alpha", "feature", "svc1")
    anchors = [n for n in canvas.nodes if n.kind == "actor_ref"]
    assert len(anchors) == 1 and anchors[0].ref_actor_id == "actor_writer"


def test_create_node_says_which_pick_is_missing_for_an_actor_ref(tmp_path: Path) -> None:
    # Without the pick the old code died inside a tagged-union validation dump —
    # unreadable to the coach, which then stopped trying.
    plot_root = _setup(tmp_path)
    _feature_canvas_with_actor(plot_root)

    with pytest.raises(ValueError) as exc:
        create_node(plot_root, "alpha", "feature", "actor_ref", {"label": "Writer"},
                    service_id="svc1")

    assert "ref_actor_id" in str(exc.value)


def test_create_node_refuses_an_actor_ref_pointing_at_no_actor(tmp_path: Path) -> None:
    # A pick names a master that exists; free text here would leave a dangling
    # anchor the viewer cannot resolve.
    plot_root = _setup(tmp_path)
    _feature_canvas_with_actor(plot_root)

    with pytest.raises(ValueError) as exc:
        create_node(
            plot_root, "alpha", "feature", "actor_ref",
            {"label": "Ghost", "ref_actor_id": "actor_missing"},
            service_id="svc1",
        )

    assert "actor_missing" in str(exc.value)
    canvas = read_canvas(plot_root, "alpha", "feature", "svc1")
    assert [n for n in canvas.nodes if n.kind == "actor_ref"] == []


def test_a_create_time_pick_does_not_open_repointing(tmp_path: Path) -> None:
    # The pinned protection is about CHANGING where an anchor points. Creating
    # one with its target must not reopen that.
    from mashbill.folder_io import update_node

    plot_root = _setup(tmp_path)
    _feature_canvas_with_actor(plot_root)
    write_canvas(
        plot_root,
        "alpha",
        CanvasDoc(
            canvas_id="actors",
            canvas_kind="actors",
            nodes=[ActorNode(id="actor_writer", label="Writer"),
                   ActorNode(id="actor_editor", label="Editor")],
        ),
    )
    created = create_node(
        plot_root, "alpha", "feature", "actor_ref",
        {"label": "Writer", "ref_actor_id": "actor_writer"}, service_id="svc1",
    )

    # Nothing in the patch is writable, so update_node refuses the whole call.
    with pytest.raises(ValueError) as exc:
        update_node(
            plot_root, "alpha", "feature", created["node"]["id"],
            {"ref_actor_id": "actor_editor"}, service_id="svc1",
        )

    assert "ref_actor_id" in str(exc.value)
    canvas = read_canvas(plot_root, "alpha", "feature", "svc1")
    anchor = next(n for n in canvas.nodes if n.kind == "actor_ref")
    assert anchor.ref_actor_id == "actor_writer"


def test_other_kinds_still_reject_a_stray_actor_reference(tmp_path: Path) -> None:
    # The create-time pick is scoped to the anchor kind that needs one; a step
    # carrying ref_actor_id is still a structural write and stays rejected.
    plot_root = _setup(tmp_path)
    _feature_canvas_with_actor(plot_root)

    out = create_node(
        plot_root, "alpha", "feature", "step",
        {"label": "Write it", "ref_actor_id": "actor_writer"}, service_id="svc1",
    )

    assert out["rejected_fields"] == ["ref_actor_id"]
    assert "ref_actor_id" not in out["node"]


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
        plot_root,
        "alpha",
        CanvasDoc(
            canvas_id="actors",
            canvas_kind="actors",
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
        plot_root,
        "alpha",
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
    assert props == {
        "project_path",
        "project_id",
        "canvas_kind",
        "kind",
        "fields",
        "service_id",
        "near",
    }
    assert set(tool.parameters["required"]) == {
        "project_path",
        "project_id",
        "canvas_kind",
        "kind",
    }


def test_create_node_docstring_creatable_kinds_match_runtime_contract() -> None:
    # The coach never calls ``creatable_kinds`` — it reads this docstring, so the
    # prose IS the contract it acts on. O-25 was in part prose drift: the actor
    # anchor was described as "read-only", which the coach read as "not mine to
    # make", and Novel's flows carried no actor for 100+ runs. The sweep above
    # only proves the code agrees with itself; this proves the sentence the coach
    # reads agrees with the code.
    from mashbill import mcp_tools

    docstring = mcp_tools.create_node.__doc__
    assert docstring is not None
    flattened = " ".join(docstring.split())
    start = "Creatable kinds per canvas: "
    end = ". The synthetic project anchor"
    assert start in flattened, f"create_node docstring is missing {start!r}"
    _, separator, remainder = flattened.partition(start)
    assert separator
    advertised_text, separator, _ = remainder.partition(end)
    assert separator, f"create_node docstring creatable list is missing terminator {end!r}"

    advertised: dict[str, set[str]] = {}
    for entry in advertised_text.split("; "):
        canvas_kind, separator, kinds_text = entry.partition(" → ")
        assert separator, f"cannot parse creatable canvas entry: {entry!r}"
        assert canvas_kind not in advertised, f"duplicate creatable canvas entry: {canvas_kind!r}"
        kind_tokens = kinds_text.split(" / ")
        assert all(token.startswith("``") and token.endswith("``") for token in kind_tokens), (
            f"cannot parse creatable kinds for {canvas_kind!r}: {kinds_text!r}"
        )
        advertised[canvas_kind] = {token[2:-2] for token in kind_tokens}

    assert set(advertised) == set(_CANVAS_KINDS)
    expected = {
        canvas_kind: canvas_io.creatable_kinds(canvas_kind) for canvas_kind in _CANVAS_KINDS
    }
    assert advertised == expected


def test_create_node_near_places_beside_the_parent(tmp_path: Path) -> None:
    """Canvas-drawing defect (user report 2026-07-02, "캔버스는 잘 못그리네"):
    kind-clustering piled every feature of EVERY service into one global
    feature column. A child node must sit beside ITS parent — ``near`` places
    the new node right of the anchor node, stacking below earlier siblings
    placed near the same anchor, and overrides the kind-cluster heuristic."""
    plot_root = _setup(tmp_path)
    write_canvas(
        plot_root,
        "alpha",
        CanvasDoc(
            canvas_id="services",
            canvas_kind="services",
            nodes=[
                ServiceNode(id="s1", label="송금", x=0.0, y=0.0),
                ServiceNode(id="s2", label="자산", x=0.0, y=600.0),
            ],
        ),
    )
    f1 = create_node(plot_root, "alpha", "services", "feature", {"label": "연락처 송금"}, near="s1")
    f2 = create_node(plot_root, "alpha", "services", "feature", {"label": "링크 송금"}, near="s1")
    g1 = create_node(plot_root, "alpha", "services", "feature", {"label": "대시보드"}, near="s2")
    # children sit right of their own parent, not in a global feature pile
    assert f1["node"]["x"] > 0.0 and abs(f1["node"]["y"] - 0.0) < 200.0
    assert g1["node"]["x"] > 0.0 and abs(g1["node"]["y"] - 600.0) < 200.0
    # siblings near the same parent stack, not overlap
    assert (f1["node"]["x"], f1["node"]["y"]) != (f2["node"]["x"], f2["node"]["y"])


def test_create_node_near_unknown_anchor_raises(tmp_path: Path) -> None:
    plot_root = _setup(tmp_path)
    _foundation(plot_root)
    with pytest.raises(ValueError, match="ghost"):
        create_node(plot_root, "alpha", "foundation", "core_value", {"label": "X"}, near="ghost")


def test_write_playbook_places_children_near_their_parent() -> None:
    from mashbill.chat_context import WRITE_PLAYBOOK

    assert "near" in WRITE_PLAYBOOK.lower()


def test_feature_created_via_mcp_seeds_its_detail_canvas(tmp_path: Path) -> None:
    """User report (2026-07-02): "기능 캔버스 뜨지 않네?" — detail canvases only
    seeded through the app's endpoint flow, so features registered by the coach
    (MCP path) had no drill-in canvas at all. Creating a feature on the services
    canvas via the MCP tool must seed its detail canvas like the app path does."""
    from mashbill import mcp_tools

    plot_root = _setup(tmp_path)
    write_canvas(
        plot_root,
        "alpha",
        CanvasDoc(
            canvas_id="services",
            canvas_kind="services",
            nodes=[ServiceNode(id="s1", label="송금", x=0.0, y=0.0)],
        ),
    )
    out = mcp_tools.create_node(
        str(tmp_path), "alpha", "services", "feature", {"label": "연락처 송금"}, near="s1"
    )
    fid = out["node"]["id"]
    from mashbill.folder_io import list_feature_details

    assert fid in list_feature_details(plot_root, "alpha")


def test_create_node_near_synthetic_anchor_uses_kind_cluster(tmp_path: Path) -> None:
    """B-14 (D-2026-07-03-T): with the anchor now the named foundation parent,
    the coach passes near=__project_anchor__ — a viewer-synthetic id with no
    node/position. That must NOT error and must NOT chain rightward: fall back
    to same-kind clustering so pillars stack with their siblings."""
    plot_root = _setup(tmp_path)
    first = create_node(
        plot_root, "alpha", "foundation", "core_value", {"label": "신뢰"}, near="__project_anchor__"
    )
    second = create_node(
        plot_root, "alpha", "foundation", "core_value", {"label": "속도"}, near="__project_anchor__"
    )
    f, s = first["node"], second["node"]
    assert s["x"] == f["x"]  # left-aligned to the kind cluster
    assert s["y"] > f["y"]  # stacked below, not marching right


def test_create_node_applies_the_kind_palette_color(tmp_path: Path) -> None:
    """B-23 (screenshot-verified, 2026-07-04): coach-created values were white
    while the seeded value is amber — same kind, different colors. create_node
    now applies the kind's default palette (mirroring the viewer stencil)
    when the caller doesn't pass a color; an explicit color still wins."""
    plot_root = _setup(tmp_path)
    v = create_node(plot_root, "alpha", "foundation", "core_value", {"label": "신뢰"})
    assert v["node"]["color"] == "#fde68a"
    a = create_node(plot_root, "alpha", "actors", "actor", {"label": "고객"})
    assert a["node"]["color"] == "#fecaca"
    # color is a STRUCTURAL field — callers can't set it (existing reject
    # guard); the palette is the single authority, so the attempt lands in
    # rejected_fields and the kind color still applies.
    custom = create_node(
        plot_root, "alpha", "foundation", "core_value", {"label": "속도", "color": "#123456"}
    )
    assert "color" in custom["rejected_fields"]
    assert custom["node"]["color"] == "#fde68a"


def test_fresh_foundation_pillars_start_on_their_pinned_side(tmp_path: Path) -> None:
    """D-2026-07-04-D — one side SSOT end to end: the first core value of a
    canvas starts LEFT (negative x, matching its pinned anchor-left spoke),
    identity starts RIGHT, so placement, pins, and layout agree instead of
    fighting ("정렬을 망가뜨렸는데" side-effect report)."""
    plot_root = _setup(tmp_path)
    # fresh canvas has seeds; remove reliance on them by checking side signs
    v = create_node(plot_root, "alpha", "foundation", "core_value", {"label": "1st"})
    i = create_node(plot_root, "alpha", "foundation", "identity", {"label": "면"})
    assert v["node"]["x"] < 0
    assert i["node"]["x"] > 0
