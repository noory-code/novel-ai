"""format F export (INT-2) — vP project snapshot + slug minting.

Walking-skeleton scope (docs/specs/format-f.md): the neutral published bundle
written alongside the existing per-node publish, not a replacement yet. Slugs
are minted into a per-project registry — explicit, stable, decoupled from label.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mashbill.folder_io import create_project, read_canvas
from mashbill.workspace import resolve_plot_root


@pytest.fixture
def plot_root(tmp_path: Path) -> Path:
    return resolve_plot_root(str(tmp_path))


def _plant_baseline(plot_root: Path, project_id: str = "alpha") -> None:
    """Blank-canvas start (D-2026-07-04-P): canvases are created EMPTY, so
    plant the classic content the old seeds used to provide — publish tests
    need a mission / core value / identity and two actors to render."""
    from mashbill.folder_io import write_canvas
    from mashbill.models import ActorNode, CoreValueNode, IdentityNode, MissionNode

    foundation = read_canvas(plot_root, project_id, "foundation")
    write_canvas(
        plot_root,
        project_id,
        foundation.model_copy(
            update={
                "nodes": [
                    MissionNode(id="mission", label="Mission"),
                    CoreValueNode(id="core-value-1", label="Core value"),
                    IdentityNode(id="identity", label="Voice"),
                ]
            }
        ),
    )
    actors = read_canvas(plot_root, project_id, "actors")
    write_canvas(
        plot_root,
        project_id,
        actors.model_copy(
            update={
                "nodes": [
                    ActorNode(id="operator", label="운영자"),
                    ActorNode(id="user", label="사용자"),
                ]
            }
        ),
    )


def test_publish_project_snapshot_writes_vp1(plot_root: Path) -> None:
    from mashbill.format_f import publish_project_snapshot

    create_project(plot_root, "alpha", "Alpha")
    _plant_baseline(plot_root)
    m = publish_project_snapshot(plot_root, "alpha")

    assert m["format_f_version"] == 1
    assert m["scope"] == "project"
    assert m["release"] == "vP1"
    ids = {e["id"] for e in m["elements"]}
    assert "mission" in ids
    assert any(i.startswith("core_value/") for i in ids)
    assert any(i.startswith("identity/") for i in ids)
    assert any(i.startswith("actor/") for i in ids)
    # every element carries a content hash (ID-diff input)
    assert all(e.get("hash") for e in m["elements"])

    vp = plot_root / "published" / "_project" / "vP1"
    assert (vp / "manifest.json").is_file()
    assert (vp / "design" / "foundation.md").is_file()
    assert (vp / "design" / "actors.md").is_file()


def test_foundation_design_renders_primary_statements(plot_root: Path) -> None:
    """The vP foundation rendering must carry each node's *primary* typed field
    (mission.statement / core_value.body / identity.description), not only an
    empty slot — that field is the actual essence the external agent reads."""
    from mashbill.folder_io import write_canvas
    from mashbill.format_f import publish_project_snapshot

    create_project(plot_root, "alpha", "Alpha")
    _plant_baseline(plot_root)
    foundation = read_canvas(plot_root, "alpha", "foundation")
    enriched = []
    for n in foundation.nodes:
        if n.kind == "mission":
            enriched.append(n.model_copy(update={"statement": "make writing effortless"}))
        elif n.kind == "core_value":
            enriched.append(n.model_copy(update={"body": "trust over growth"}))
        elif n.kind == "identity":
            enriched.append(n.model_copy(update={"description": "calm and clear"}))
        else:
            enriched.append(n)
    write_canvas(plot_root, "alpha", foundation.model_copy(update={"nodes": enriched}))
    publish_project_snapshot(plot_root, "alpha")

    md = (plot_root / "published" / "_project" / "vP1" / "design" / "foundation.md").read_text(
        encoding="utf-8"
    )
    assert "make writing effortless" in md
    assert "trust over growth" in md
    assert "calm and clear" in md


def test_foundation_hash_tracks_primary_statement(plot_root: Path) -> None:
    """Changing a mission statement must move its element hash (else the ID-diff
    misses an essence change)."""
    from mashbill.folder_io import write_canvas
    from mashbill.format_f import publish_project_snapshot

    create_project(plot_root, "alpha", "Alpha")
    _plant_baseline(plot_root)
    m1 = publish_project_snapshot(plot_root, "alpha")
    h1 = next(e["hash"] for e in m1["elements"] if e["id"] == "mission")

    foundation = read_canvas(plot_root, "alpha", "foundation")
    bumped = [
        n.model_copy(update={"statement": "a new mission"}) if n.kind == "mission" else n
        for n in foundation.nodes
    ]
    write_canvas(plot_root, "alpha", foundation.model_copy(update={"nodes": bumped}))
    m2 = publish_project_snapshot(plot_root, "alpha")
    h2 = next(e["hash"] for e in m2["elements"] if e["id"] == "mission")
    assert h1 != h2


def test_entity_design_renders_summary(plot_root: Path) -> None:
    """Entity rendering reads ``summary`` (the '무엇을 담나' line) — the old code
    read a non-existent ``body``, leaving entity files empty."""
    from mashbill.folder_io import write_canvas
    from mashbill.format_f import publish_project_snapshot
    from mashbill.models import EntityNode

    create_project(plot_root, "alpha", "Alpha")
    _plant_baseline(plot_root)
    entities = read_canvas(plot_root, "alpha", "entities")
    write_canvas(
        plot_root,
        "alpha",
        entities.model_copy(
            update={
                "nodes": [EntityNode(id="ent-post", label="Post", summary="a piece of writing")]
            }
        ),
    )
    m = publish_project_snapshot(plot_root, "alpha")

    post_slug = next(e["id"] for e in m["elements"] if e["kind"] == "entity")
    md = (
        plot_root
        / "published"
        / "_project"
        / "vP1"
        / "design"
        / "entities"
        / f"{post_slug.split('/')[-1]}.md"
    ).read_text(encoding="utf-8")
    assert "a piece of writing" in md
    # and the summary feeds the hash (ID-diff input)
    assert next(e["hash"] for e in m["elements"] if e["kind"] == "entity")


def test_actors_design_renders_relationships(plot_root: Path) -> None:
    """actors.md must render the give/receive relationships (spec §3 '주고받음'),
    not just the role list."""
    from mashbill.folder_io import write_canvas
    from mashbill.format_f import publish_project_snapshot
    from mashbill.models import SketchEdge

    create_project(plot_root, "alpha", "Alpha")
    _plant_baseline(plot_root)
    actors = read_canvas(plot_root, "alpha", "actors")
    write_canvas(
        plot_root,
        "alpha",
        actors.model_copy(
            update={
                "edges": [
                    SketchEdge(
                        id="rel",
                        source="operator",
                        target="user",
                        label="serves",
                        relation="inheritance",
                    )
                ]
            }
        ),
    )
    publish_project_snapshot(plot_root, "alpha")

    md = (plot_root / "published" / "_project" / "vP1" / "design" / "actors.md").read_text(
        encoding="utf-8"
    )
    assert "운영자" in md and "사용자" in md
    assert "serves" in md


def test_service_design_surfaces_refs(plot_root: Path) -> None:
    """service.md must surface what the service stands on in its vP (participating
    actors / protected values / identity tone), so the file reads standalone."""
    from mashbill.format_f import publish_project_snapshot, publish_service

    create_project(plot_root, "alpha", "Alpha")
    _plant_baseline(plot_root)
    _add_service_referencing_seeds(plot_root)
    publish_project_snapshot(plot_root, "alpha")
    m = publish_service(plot_root, "alpha", "svc-auth")

    md = (plot_root / "published" / "auth" / "vS1" / "design" / "service.md").read_text(
        encoding="utf-8"
    )
    assert any(a in md for a in m["refs"]["actors"])
    assert any(v in md for v in m["refs"]["anchors"]["core_values"])


def test_service_refs_anchor_to_project_mission(plot_root: Path) -> None:
    """Every service stands on the project's single mission — the essence (VISION).
    The vS refs must anchor to it so a mission change propagates to the services
    that realize it; refs is the propagation surface (format-f.md §5)."""
    from mashbill.format_f import publish_project_snapshot, publish_service

    create_project(plot_root, "alpha", "Alpha")
    _plant_baseline(plot_root)
    _add_service_referencing_seeds(plot_root)
    vp = publish_project_snapshot(plot_root, "alpha")
    assert any(e["id"] == "mission" for e in vp["elements"])  # mission lives in vP
    m = publish_service(plot_root, "alpha", "svc-auth")
    assert m["refs"]["anchors"]["mission"] == "mission"


def test_snapshot_release_bumps(plot_root: Path) -> None:
    from mashbill.format_f import publish_project_snapshot

    create_project(plot_root, "alpha", "Alpha")
    _plant_baseline(plot_root)
    assert publish_project_snapshot(plot_root, "alpha")["release"] == "vP1"
    assert publish_project_snapshot(plot_root, "alpha")["release"] == "vP2"


def _add_service_referencing_seeds(plot_root: Path) -> str:
    """Add a service that references the seeded actor + core_value + identity,
    returning the service node id."""
    from mashbill.folder_io import write_canvas
    from mashbill.models import ServiceNode

    foundation = read_canvas(plot_root, "alpha", "foundation")
    actors = read_canvas(plot_root, "alpha", "actors")
    cv = next(n for n in foundation.nodes if n.kind == "core_value")
    idn = next(n for n in foundation.nodes if n.kind == "identity")
    act = next(n for n in actors.nodes if n.kind == "actor")
    svc = ServiceNode(
        id="svc-auth",
        label="Auth",
        problem="users need to sign in",
        value_created="secure access to the product",
        ref_actor_ids=[act.id],
        ref_value_ids=[cv.id],
        ref_identity_ids=[idn.id],
    )
    services = read_canvas(plot_root, "alpha", "services")
    write_canvas(plot_root, "alpha", services.model_copy(update={"nodes": [svc]}))
    return "svc-auth"


def _add_service_with_features(plot_root: Path) -> str:
    """Add a service with two features nested via directed edges, each with a
    detail canvas carrying a small UX flow (step → decision → branches).
    Returns the service node id. Builds on the seeds the service refs."""
    from mashbill.folder_io import write_canvas
    from mashbill.models import (
        ActorRefNode,
        CanvasDoc,
        DecisionNode,
        FeatureNode,
        NoteNode,
        ServiceNode,
        SketchEdge,
        StepNode,
    )

    foundation = read_canvas(plot_root, "alpha", "foundation")
    actors = read_canvas(plot_root, "alpha", "actors")
    cv = next(n for n in foundation.nodes if n.kind == "core_value")
    idn = next(n for n in foundation.nodes if n.kind == "identity")
    act = next(n for n in actors.nodes if n.kind == "actor")

    svc = ServiceNode(
        id="svc-auth",
        label="Auth",
        problem="users need to sign in",
        value_created="secure access to the product",
        ref_actor_ids=[act.id],
        ref_value_ids=[cv.id],
        ref_identity_ids=[idn.id],
    )
    login = FeatureNode(id="feat-login", label="Login", proposed="자격으로 세션을 연다")
    signup = FeatureNode(id="feat-signup", label="Sign up", proposed="새 계정을 만든다")
    services = read_canvas(plot_root, "alpha", "services")
    write_canvas(
        plot_root,
        "alpha",
        services.model_copy(
            update={
                "nodes": [svc, login, signup],
                "edges": [
                    SketchEdge(id="e-login", source="svc-auth", target="feat-login"),
                    SketchEdge(id="e-signup", source="svc-auth", target="feat-signup"),
                ],
            }
        ),
    )

    # Login detail canvas: a real flow — input → verify branch → success/retry.
    login_detail = CanvasDoc(
        canvas_id="feat-login",
        canvas_kind="feature",
        feature_ref="feat-login",
        nodes=[
            FeatureNode(id="feat-login", label="Login", proposed="자격으로 세션을 연다"),
            ActorRefNode(
                id="feat-login-user-ref", label="→ User", ref_actor_id="user"
            ),
            StepNode(id="s-input", label="자격 입력", order=1, outcome="자격 제출"),
            DecisionNode(id="d-verify", label="검증 성공?"),
            StepNode(id="s-session", label="세션 생성", order=2, outcome="로그인됨"),
            StepNode(
                id="s-retry", label="재시도", order=3, outcome="다시 입력", polarity="negative"
            ),
            NoteNode(id="n-memo", label="모바일 우선", body="본문 500자"),
        ],
        edges=[
            SketchEdge(id="f-1", source="s-input", target="d-verify"),
            SketchEdge(id="f-2", source="d-verify", target="s-session", label="성공"),
            SketchEdge(id="f-3", source="d-verify", target="s-retry", label="실패"),
        ],
    )
    write_canvas(plot_root, "alpha", login_detail)
    return "svc-auth"


def test_publish_service_includes_feature_elements(plot_root: Path) -> None:
    from mashbill.format_f import publish_project_snapshot, publish_service

    create_project(plot_root, "alpha", "Alpha")
    _plant_baseline(plot_root)
    _add_service_with_features(plot_root)
    publish_project_snapshot(plot_root, "alpha")
    m = publish_service(plot_root, "alpha", "svc-auth")

    feature_els = [e for e in m["elements"] if e["kind"] == "feature"]
    assert len(feature_els) == 2
    assert all(e["id"].startswith("feature/") for e in feature_els)
    assert all(e.get("flow") is True for e in feature_els)
    assert all(e.get("hash") for e in feature_els)

    feats_dir = plot_root / "published" / "auth" / "vS1" / "design" / "features"
    assert feats_dir.is_dir()
    assert len(list(feats_dir.glob("*.md"))) == 2


def test_feature_design_renders_capability_and_flow(plot_root: Path) -> None:
    from mashbill.format_f import publish_project_snapshot, publish_service

    create_project(plot_root, "alpha", "Alpha")
    _plant_baseline(plot_root)
    _add_service_with_features(plot_root)
    publish_project_snapshot(plot_root, "alpha")
    m = publish_service(plot_root, "alpha", "svc-auth")

    login_slug = next(
        e["id"] for e in m["elements"] if e["kind"] == "feature" and "login" in e["id"]
    )
    md = (
        plot_root
        / "published"
        / "auth"
        / "vS1"
        / "design"
        / "features"
        / f"{login_slug.split('/')[-1]}.md"
    ).read_text(encoding="utf-8")

    # frontmatter pins id + kind for the reader
    assert f"id: {login_slug}" in md
    assert "kind: feature" in md
    # capability summary (proposed)
    assert "자격으로 세션을 연다" in md
    # UX flow content sourced from the detail canvas
    assert "자격 입력" in md
    assert "검증 성공?" in md  # decision
    assert "세션 생성" in md
    assert "성공" in md and "실패" in md  # branch labels
    assert "모바일 우선" in md  # ambient note


def test_feature_element_hash_tracks_flow_change(plot_root: Path) -> None:
    """The feature element hash is the ID-diff input — it must move when the
    UX flow changes so a republish surfaces the feature as ``changed``."""
    from mashbill.folder_io import write_canvas
    from mashbill.format_f import publish_project_snapshot, publish_service

    create_project(plot_root, "alpha", "Alpha")
    _plant_baseline(plot_root)
    _add_service_with_features(plot_root)
    publish_project_snapshot(plot_root, "alpha")
    m1 = publish_service(plot_root, "alpha", "svc-auth")
    h1 = next(e["hash"] for e in m1["elements"] if "login" in e["id"])

    detail = read_canvas(plot_root, "alpha", "feature", service_id="feat-login")
    bumped = [
        n.model_copy(update={"label": "자격 재입력"}) if n.id == "s-input" else n
        for n in detail.nodes
    ]
    write_canvas(plot_root, "alpha", detail.model_copy(update={"nodes": bumped}))
    m2 = publish_service(plot_root, "alpha", "svc-auth")
    h2 = next(e["hash"] for e in m2["elements"] if "login" in e["id"])
    assert h1 != h2


def test_service_entity_refs_collected_from_steps(plot_root: Path) -> None:
    """A feature's steps name the entities they act on (StepNode.ref_entity_ids);
    those roll up into the service release's ``refs.entities`` (resolved to vP
    slugs, not copied)."""
    from mashbill.folder_io import write_canvas
    from mashbill.format_f import publish_project_snapshot, publish_service
    from mashbill.models import EntityNode

    create_project(plot_root, "alpha", "Alpha")
    _plant_baseline(plot_root)
    entities = read_canvas(plot_root, "alpha", "entities")
    write_canvas(
        plot_root,
        "alpha",
        entities.model_copy(
            update={"nodes": [EntityNode(id="ent-session", label="Session", summary="a login")]}
        ),
    )
    _add_service_with_features(plot_root)
    # point the login flow's session step at the entity
    detail = read_canvas(plot_root, "alpha", "feature", service_id="feat-login")
    wired = [
        n.model_copy(update={"ref_entity_ids": ["ent-session"]}) if n.id == "s-session" else n
        for n in detail.nodes
    ]
    write_canvas(plot_root, "alpha", detail.model_copy(update={"nodes": wired}))

    publish_project_snapshot(plot_root, "alpha")
    m = publish_service(plot_root, "alpha", "svc-auth")
    assert m["refs"]["entities"]
    assert all(e.startswith("entity/") for e in m["refs"]["entities"])


def test_publish_service_with_dangling_entity_ref_is_rejected(plot_root: Path) -> None:
    """refs-integrity (§1.4) covers entity refs too: a step naming an entity
    absent from the based_on vP refuses the publish at the write boundary."""
    from mashbill.folder_io import write_canvas
    from mashbill.format_f import publish_project_snapshot, publish_service

    create_project(plot_root, "alpha", "Alpha")
    _plant_baseline(plot_root)
    _add_service_with_features(plot_root)
    detail = read_canvas(plot_root, "alpha", "feature", service_id="feat-login")
    wired = [
        n.model_copy(update={"ref_entity_ids": ["ghost-entity"]}) if n.id == "s-session" else n
        for n in detail.nodes
    ]
    write_canvas(plot_root, "alpha", detail.model_copy(update={"nodes": wired}))

    publish_project_snapshot(plot_root, "alpha")
    with pytest.raises(ValueError, match="refs|resolve"):
        publish_service(plot_root, "alpha", "svc-auth")


def test_publish_service_release_refs_into_vp(plot_root: Path) -> None:
    from mashbill.format_f import publish_project_snapshot, publish_service

    create_project(plot_root, "alpha", "Alpha")
    _plant_baseline(plot_root)
    _add_service_referencing_seeds(plot_root)
    publish_project_snapshot(plot_root, "alpha")  # vP1 (bootstrap)
    m = publish_service(plot_root, "alpha", "svc-auth")

    assert m["scope"] == "service"
    assert m["service"].startswith("service/")
    assert m["release"] == "vS1"
    assert m["based_on"] == "vP1"
    # the service element is owned by the release
    assert any(e["id"] == m["service"] for e in m["elements"])
    # refs point at vP slugs (not copies)
    assert m["refs"]["actors"] and all(a.startswith("actor/") for a in m["refs"]["actors"])
    assert all(v.startswith("core_value/") for v in m["refs"]["anchors"]["core_values"])

    vs = plot_root / "published" / "auth" / "vS1"
    assert (vs / "manifest.json").is_file()
    assert (vs / "design" / "service.md").is_file()


def test_publish_service_without_vp_is_rejected(plot_root: Path) -> None:
    """Bootstrap invariant: a service release needs a project snapshot first."""
    from mashbill.format_f import publish_service

    create_project(plot_root, "alpha", "Alpha")
    _plant_baseline(plot_root)
    _add_service_referencing_seeds(plot_root)
    with pytest.raises(ValueError, match="snapshot"):
        publish_service(plot_root, "alpha", "svc-auth")


def test_publish_service_with_dangling_ref_is_rejected(plot_root: Path) -> None:
    """refs-integrity gate: a ref that does not resolve in the based_on vP is
    refused at the write boundary."""
    from mashbill.folder_io import write_canvas
    from mashbill.format_f import publish_project_snapshot, publish_service
    from mashbill.models import ServiceNode

    create_project(plot_root, "alpha", "Alpha")
    _plant_baseline(plot_root)
    publish_project_snapshot(plot_root, "alpha")  # vP1 has the seeded actors only
    svc = ServiceNode(
        id="svc-x",
        label="X",
        problem="p",
        value_created="v",
        ref_actor_ids=["ghost-actor-id"],  # not in any canvas → not in vP
    )
    services = read_canvas(plot_root, "alpha", "services")
    write_canvas(plot_root, "alpha", services.model_copy(update={"nodes": [svc]}))
    with pytest.raises(ValueError, match="refs|resolve"):
        publish_service(plot_root, "alpha", "svc-x")


def test_manifest_contract_shape_is_pinned(plot_root: Path) -> None:
    """Cross-repo contract guard (INT-1c, write side): the manifests Novel emits
    carry exactly the keys Solera's reader expects. Pinned here so a producer
    change that drops a field fails before it reaches Solera. The version is
    pinned in lock-step with ``intake.SUPPORTED_FORMAT_F_VERSION``."""
    from mashbill.format_f import (
        FORMAT_F_VERSION,
        publish_project_snapshot,
        publish_service,
    )

    assert FORMAT_F_VERSION == 1

    create_project(plot_root, "alpha", "Alpha")
    _plant_baseline(plot_root)
    _add_service_referencing_seeds(plot_root)
    vp = publish_project_snapshot(plot_root, "alpha")
    assert set(vp) >= {"format_f_version", "scope", "release", "git_sha", "elements"}
    assert vp["format_f_version"] == FORMAT_F_VERSION
    assert all(set(e) >= {"id", "kind", "hash"} for e in vp["elements"])

    vs = publish_service(plot_root, "alpha", "svc-auth")
    assert set(vs) >= {
        "format_f_version",
        "scope",
        "service",
        "release",
        "based_on",
        "elements",
        "refs",
    }
    assert set(vs["refs"]) >= {"anchors", "actors", "entities"}


def test_publish_reachable_via_mcp_surface(tmp_path: Path) -> None:
    """format F is reachable on the MCP surface — the primary integration path
    per VISION ('주경로 = 사용자 에이전트가 MCP로 붙음'). The tools take a
    workspace path (not a plot_root)."""
    from mashbill.mcp_tools import (
        create_project_tool,
        publish_project_snapshot_tool,
        publish_service_tool,
    )

    create_project_tool(str(tmp_path), "alpha", "Alpha")
    vp = publish_project_snapshot_tool(str(tmp_path), "alpha")
    assert vp["scope"] == "project"
    assert vp["release"] == "vP1"
    assert callable(publish_service_tool)


def test_minted_slug_is_stable_across_label_change(plot_root: Path) -> None:
    """Explicit-slug invariant: once minted (keyed on node id), the slug does
    not move when the label changes — that is what makes it a stable contract."""
    from mashbill.format_f import mint_slug

    create_project(plot_root, "alpha", "Alpha")
    _plant_baseline(plot_root)
    foundation = read_canvas(plot_root, "alpha", "foundation")
    cv = next(n for n in foundation.nodes if n.kind == "core_value")
    s1 = mint_slug(plot_root, "alpha", cv)
    s2 = mint_slug(plot_root, "alpha", cv.model_copy(update={"label": "Totally Renamed"}))
    assert s1 == s2
    assert s1.startswith("core_value/")
