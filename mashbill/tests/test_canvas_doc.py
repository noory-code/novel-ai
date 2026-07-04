"""CanvasDoc + per-canvas-kind validators for Novel v0.2 multi-canvas split.

Each canvas enforces its own allowed ``NodeKind`` set and structural rules.
See the ``Target Data Model`` section of the v0.2 plan.
"""

from __future__ import annotations

import pytest

from mashbill.models import (
    ActorNode,
    ActorRefNode,
    CanvasDoc,
    CategoryNode,
    CoreValueNode,
    FeatureNode,
    IdentityNode,
    MissionNode,
    NoteNode,
    ProjectNode,
    RuleNode,
    ServiceNode,
    SketchEdge,
    SketchNode,
    SketchNodeAdapter,
    StepNode,
)

# ---------------------------------------------------------------------------
# core canvas
# ---------------------------------------------------------------------------


def _core_seed_nodes() -> list[SketchNode]:
    """Minimal valid core-canvas content: project anchor + 1 mission + 1 identity."""
    return [
        ProjectNode(id="project", label="Project", shape="circle"),
        MissionNode(id="mission", label="M"),
        IdentityNode(id="identity", label="Voice"),
    ]


def test_core_canvas_minimum_seed_ok() -> None:
    CanvasDoc(canvas_id="foundation", canvas_kind="foundation", nodes=_core_seed_nodes())


def test_core_canvas_multiple_core_values_ok() -> None:
    CanvasDoc(
        canvas_id="foundation",
        canvas_kind="foundation",
        nodes=[
            *_core_seed_nodes(),
            CoreValueNode(id="cv1", label="빠름"),
            CoreValueNode(id="cv2", label="정확함"),
        ],
    )


def test_core_canvas_multiple_missions_ok() -> None:
    """v0.5: Mission is 1..N (was exactly 1)."""
    CanvasDoc(
        canvas_id="foundation",
        canvas_kind="foundation",
        nodes=[
            *_core_seed_nodes(),
            MissionNode(id="m2", label="M2"),
            MissionNode(id="m3", label="M3"),
        ],
    )


def test_core_canvas_multiple_identities_ok() -> None:
    """v0.5: Identity is 1..N peers (was exactly 1 + facet children)."""
    CanvasDoc(
        canvas_id="foundation",
        canvas_kind="foundation",
        nodes=[
            *_core_seed_nodes(),
            IdentityNode(id="energy", label="Energy"),
            IdentityNode(id="speech", label="Speech style"),
        ],
    )


def test_core_canvas_missing_mission_rejected() -> None:
    with pytest.raises(ValueError, match="mission"):
        CanvasDoc(
            canvas_id="foundation",
            canvas_kind="foundation",
            nodes=[
                ProjectNode(id="project", label="Project", shape="circle"),
                IdentityNode(id="identity", label="I"),
            ],
        )


def test_core_canvas_missing_identity_rejected() -> None:
    with pytest.raises(ValueError, match="identity"):
        CanvasDoc(
            canvas_id="foundation",
            canvas_kind="foundation",
            nodes=[
                ProjectNode(id="project", label="Project", shape="circle"),
                MissionNode(id="mission", label="M"),
            ],
        )


def test_core_canvas_missing_project_accepted() -> None:
    """v0.13 Phase 0: project anchor moved to ProjectDoc.anchors.
    Foundation no longer requires a project node in nodes."""
    canvas = CanvasDoc(
        canvas_id="foundation",
        canvas_kind="foundation",
        nodes=[
            MissionNode(id="mission", label="M"),
            IdentityNode(id="identity", label="I"),
        ],
    )
    assert all(n.kind != "project" for n in canvas.nodes)


def test_core_canvas_two_projects_rejected() -> None:
    """v0.13 Phase 0: legacy project nodes tolerated for backwards compat
    but at most one (the eviction migrator removes them entirely)."""
    with pytest.raises(ValueError, match="legacy project"):
        CanvasDoc(
            canvas_id="foundation",
            canvas_kind="foundation",
            nodes=[
                *_core_seed_nodes(),
                ProjectNode(id="p2", label="P2", shape="circle"),
            ],
        )


def test_core_canvas_nested_project_rejected() -> None:
    """v0.26.0 (D-2026-05-25-A) — top-level project-node validator was
    parent_id-based and is gone. The doc constructs cleanly; project
    anchor's top-levelness is now implicit (no incoming directed edge)
    rather than a Pydantic-enforced invariant."""
    CanvasDoc(
        canvas_id="foundation",
        canvas_kind="foundation",
        nodes=[
            MissionNode(id="mission", label="M"),
            IdentityNode(id="identity", label="I"),
            ProjectNode(
                id="project",
                label="P",
                shape="circle",
            ),
        ],
    )


def test_mission_node_carries_statement_and_body() -> None:
    """v0.43.0 (D-2026-06-06-C): mission = ``statement`` (the declaration,
    display label "미션") + ``body``. The old what_we_do/why/direction
    fields were removed (mission is one declaration)."""
    n = MissionNode(
        id="mission-1",
        label="Mission",
        statement="누구나 히어로가 되는 일상을 만든다",
        body="## 스토리\n…",
    )
    assert n.statement.startswith("누구나 히어로")
    assert "스토리" in n.body


def test_actor_does_not_carry_foreign_typed_fields() -> None:
    """v0.15: per-kind classes own only their own typed fields. An
    ActorNode must not carry Mission's ``what_we_do`` or CoreValue's
    ``definition`` etc. — that god-pool pattern is gone."""
    n = ActorNode(id="x", label="User")
    for foreign in (
        "what_we_do",
        "why",
        "direction",
        "definition",
        "description",
        "do",
        "dont",
        "what",
        "value_created",
        "scope",
        "trigger",
        "how",
        "outcome",
        "theme",
        "target",
        "measurement",
        "policy",
        "enforcement",
        "actor_permissions",
        "format",
        "producer_actor_id",
        "consumer_actor_id",
    ):
        assert not hasattr(n, foreign), (
            f"ActorNode unexpectedly carries foreign field {foreign!r} (god-pool regression)"
        )


def test_core_value_carries_name_and_body() -> None:
    """v0.45 (D-2026-07-02-A): core_value = ``label`` (the value's name) +
    ``body`` (its meaning + tradeoff). definition/do/dont were removed."""
    n = CoreValueNode(
        id="cv-tolerance",
        label="관용",
        body="다름을 인정하고 있는 그대로 받아들임. 판단 기준: 상대를 이해하려 했는가?",
    )
    assert n.label == "관용"
    assert "다름을 인정" in n.body
    dumped = n.model_dump()
    assert "definition" not in dumped
    assert "do" not in dumped and "dont" not in dumped


def test_identity_carries_description_and_body() -> None:
    """B-15 (D-2026-07-03-S supersedes D-2026-06-06-B's split): description is
    identity's single prose field — a provided body folds into it on read."""
    n = IdentityNode(
        id="id-voice",
        label="Voice",
        description="따뜻하고 진솔한 1:1 대화처럼 말한다",
        body="이름을 부른다",
    )
    assert "따뜻하고" in n.description
    assert "이름을 부른다" in n.description
    assert n.body == ""
    assert "do" not in n.model_dump() and "dont" not in n.model_dump()


def test_value_and_identity_typed_fields_round_trip_in_canvas() -> None:
    """Foundation canvas serialises and parses Step 2 typed fields end-to-end."""
    doc = CanvasDoc(
        canvas_id="foundation",
        canvas_kind="foundation",
        nodes=[
            *_core_seed_nodes(),
            CoreValueNode(
                id="cv1",
                label="Trust",
                body="우리는 서로의 의도를 의심하지 않는다. 동기를 먼저 묻는다",
            ),
            IdentityNode(
                id="id1",
                label="Energy",
                description="조용하고 또렷하다",
                body="짧고 단단하게 말한다",
            ),
        ],
    )
    parsed = CanvasDoc.model_validate(doc.model_dump())
    cv = next(n for n in parsed.nodes if n.id == "cv1")
    ident = next(n for n in parsed.nodes if n.id == "id1")
    assert cv.body.startswith("우리는 서로")
    # B-15: identity body folds into description on read
    assert "조용하고 또렷하다" in ident.description
    assert "짧고 단단하게 말한다" in ident.description
    assert ident.body == ""


def test_node_details_path_absolute_rejected() -> None:
    with pytest.raises(ValueError, match="relative"):
        MissionNode(id="n1", label="M", details_path="/etc/passwd")


def test_node_details_path_traversal_rejected() -> None:
    with pytest.raises(ValueError, match=r"\.\."):
        MissionNode(id="n1", label="M", details_path="workspace/../etc")


def test_node_details_path_blank_rejected() -> None:
    with pytest.raises(ValueError, match="blank"):
        MissionNode(id="n1", label="M", details_path="   ")


def test_node_details_path_valid() -> None:
    n = MissionNode(
        id="n1",
        label="M",
        details_path="workspace/core/mission-mission",
    )
    assert n.details_path == "workspace/core/mission-mission"


def test_core_canvas_actor_kind_rejected() -> None:
    with pytest.raises(ValueError, match="not allowed"):
        CanvasDoc(
            canvas_id="foundation",
            canvas_kind="foundation",
            nodes=[
                *_core_seed_nodes(),
                ActorNode(id="a1", label="Stray"),
            ],
        )


# ---------------------------------------------------------------------------
# actors canvas
# ---------------------------------------------------------------------------


def test_actors_canvas_two_actors_ok() -> None:
    """v0.11 — actors canvas requires ≥ 2 actor classes."""
    CanvasDoc(
        canvas_id="actors",
        canvas_kind="actors",
        nodes=[
            ActorNode(id="operator", label="운영자", side="operator"),
            ActorNode(id="user", label="사용자", side="user"),
        ],
    )


def test_actors_canvas_single_actor_rejected() -> None:
    """v0.11 — IDENTITY.md baseline: ≥ 2 actor classes required."""
    with pytest.raises(ValueError, match="2 actor"):
        CanvasDoc(
            canvas_id="actors",
            canvas_kind="actors",
            nodes=[ActorNode(id="user", label="사용자")],
        )


def test_actors_canvas_sub_actor_via_parent_id_ok() -> None:
    CanvasDoc(
        canvas_id="actors",
        canvas_kind="actors",
        nodes=[
            ActorNode(id="team", label="Team", side="user"),
            ActorNode(id="member", label="Member", side="user"),
        ],
    )


def test_actors_canvas_service_rejected() -> None:
    with pytest.raises(ValueError, match="not allowed"):
        CanvasDoc(
            canvas_id="actors",
            canvas_kind="actors",
            nodes=[
                ServiceNode(id="s1", label="Stray service"),
            ],
        )


def test_actors_canvas_actor_ref_rejected() -> None:
    with pytest.raises(ValueError, match="not allowed"):
        CanvasDoc(
            canvas_id="actors",
            canvas_kind="actors",
            nodes=[
                ActorRefNode(id="r1", ref_actor_id="user", label="ref"),
            ],
        )


# ---------------------------------------------------------------------------
# services canvas
# ---------------------------------------------------------------------------


def test_overview_top_level_services_ok() -> None:
    """v0.12 — services canvas: project + category + service (nested in category)."""
    CanvasDoc(
        canvas_id="services",
        canvas_kind="services",
        nodes=[
            CategoryNode(id="commerce", label="Commerce"),
            ServiceNode(id="order", label="주문"),
            ServiceNode(id="pay", label="결제"),
        ],
    )


def test_overview_service_without_category_parent_rejected() -> None:
    """v0.26.0 (D-2026-05-25-A) — service-must-have-category-parent
    invariant (formerly parent_id-based) is gone. The doc constructs
    cleanly; user expresses containment via a directed edge from a
    category to the service."""
    CanvasDoc(
        canvas_id="services",
        canvas_kind="services",
        nodes=[ServiceNode(id="order", label="주문")],
    )


def test_overview_nested_category_rejected() -> None:
    """v0.26.0 (D-2026-05-25-A) — categories-must-be-top-level
    invariant (formerly parent_id-based) is gone. Two categories with
    a directed edge between them are now expressible."""
    CanvasDoc(
        canvas_id="services",
        canvas_kind="services",
        nodes=[
            CategoryNode(id="parent", label="Parent"),
            CategoryNode(id="child", label="Child"),
        ],
    )


def test_overview_empty_canvas_ok() -> None:
    """An empty services canvas (no services yet) is fine."""
    CanvasDoc(canvas_id="services", canvas_kind="services", nodes=[])


def test_overview_nested_service_rejected() -> None:
    """v0.26.0 (D-2026-05-25-A) — services-nesting validator
    (formerly parent_id-based) is gone. Decomposition / nesting on the
    overview is now expressible; users still choose to keep decomposition
    in feature canvases per the docs guidance."""
    CanvasDoc(
        canvas_id="services",
        canvas_kind="services",
        nodes=[
            ServiceNode(id="order", label="주문"),
            ServiceNode(id="order-sub", label="Sub"),
        ],
    )


def test_overview_actor_rejected() -> None:
    with pytest.raises(ValueError, match="not allowed"):
        CanvasDoc(
            canvas_id="services",
            canvas_kind="services",
            nodes=[ActorNode(id="a1", label="Stray")],
        )


# ---------------------------------------------------------------------------
# feature canvas
# ---------------------------------------------------------------------------


def _detail_seed(canvas_id: str = "order") -> list[SketchNode]:
    """Minimum valid feature content: root feature (the drill
    target — D-2026-06-17-D) + two actor_refs (operator + user) to
    satisfy IDENTITY.md baseline."""
    return [
        FeatureNode(id=canvas_id, label="주문"),
        ActorRefNode(
            id=f"{canvas_id}-op-ref",
            label="→ operator",
            ref_actor_id="operator",
            side="operator",
        ),
        ActorRefNode(
            id=f"{canvas_id}-user-ref",
            label="→ user",
            ref_actor_id="user",
            side="user",
        ),
    ]


def test_detail_canvas_minimum_ok() -> None:
    CanvasDoc(
        canvas_id="order",
        canvas_kind="feature",
        feature_ref="order",
        nodes=_detail_seed(),
    )


def test_detail_canvas_zero_actor_refs_rejected() -> None:
    """v0.27.16 (D-2026-05-28-K) — feature still requires at least
    one actor_ref. ``≥ 0`` would let a canvas exist with no subject at
    all, which contradicts D-2026-05-28-J (every step's subject is an
    actor)."""
    with pytest.raises(ValueError, match="actor_ref"):
        CanvasDoc(
            canvas_id="order",
            canvas_kind="feature",
            feature_ref="order",
            nodes=[ServiceNode(id="order", label="주문")],
        )


def test_detail_canvas_one_user_actor_ref_ok() -> None:
    """v0.27.16 (D-2026-05-28-K) — per D-2026-05-28-J the operator side
    of a service is the *service itself*; only a user-side actor_ref is
    required. A single user-side actor_ref must produce a valid
    feature (the pre-v0.27.16 ``≥ 2`` rule rejected this and
    forced an Admin placeholder, which the user flagged as a category
    error on 2026-05-28)."""
    CanvasDoc(
        canvas_id="login",
        canvas_kind="feature",
        feature_ref="login",
        nodes=[
            FeatureNode(id="login", label="Login"),
            ActorRefNode(
                id="login-user",
                label="→ Bana",
                ref_actor_id="bana",
                side="user",
            ),
        ],
    )


def test_detail_canvas_operator_side_only_still_ok_for_backwards_compat() -> None:
    """v0.27.16 — accept ``side="operator"`` actor_ref on its own too;
    don't silently break legacy docs that have only an operator actor.
    The minimum is *one* actor_ref of any side."""
    CanvasDoc(
        canvas_id="ops",
        canvas_kind="feature",
        feature_ref="ops",
        nodes=[
            FeatureNode(id="ops", label="Ops"),
            ActorRefNode(
                id="ops-op",
                label="→ Admin",
                ref_actor_id="admin",
                side="operator",
            ),
        ],
    )


def test_detail_canvas_feature_ref_must_match_canvas_id() -> None:
    with pytest.raises(ValueError, match="feature_ref"):
        CanvasDoc(
            canvas_id="order",
            canvas_kind="feature",
            feature_ref="pay",  # mismatch
            nodes=_detail_seed(),
        )


def test_detail_canvas_feature_ref_required() -> None:
    with pytest.raises(ValueError, match="feature_ref"):
        CanvasDoc(
            canvas_id="order",
            canvas_kind="feature",
            nodes=_detail_seed(),
        )


def test_detail_canvas_sub_features_rules_ok() -> None:
    # D-2026-06-17-D — the detail canvas drills into a feature; sub-features
    # + rules are legitimate extra nodes (``service`` is no longer allowed
    # here, so the former sub-service is now a sub-feature).
    CanvasDoc(
        canvas_id="order",
        canvas_kind="feature",
        feature_ref="order",
        nodes=[
            *_detail_seed(),
            FeatureNode(id="sub1", label="장바구니"),
            RuleNode(id="r1", label="가격 규칙"),
        ],
    )


def test_detail_canvas_actor_ref_ok() -> None:
    CanvasDoc(
        canvas_id="order",
        canvas_kind="feature",
        feature_ref="order",
        nodes=[
            *_detail_seed(),
            ActorRefNode(
                id="ref-user",
                ref_actor_id="user",  # references actor in actors canvas
                label="사용자",
            ),
        ],
    )


def test_detail_canvas_actor_ref_without_ref_id_rejected() -> None:
    with pytest.raises(ValueError, match="ref_actor_id"):
        CanvasDoc(
            canvas_id="order",
            canvas_kind="feature",
            feature_ref="order",
            nodes=[
                *_detail_seed(),
                ActorRefNode(id="bad-ref", label="Orphan"),
            ],
        )


# mission_ref / value_ref / identity_ref retired 2026-06-20 (D-2026-06-20-G):
# Foundation references are now the service-inspector chips, not standalone
# nodes. The Foundation-reference-kind tests were removed with the kinds.


def test_service_node_carries_5_fields() -> None:
    """D-2026-06-20-F — service = 2 typed (problem / value_created) + 3 ref-id
    arrays (Option B). The old 9 free-text fields are gone."""
    n = ServiceNode(
        id="auth",
        label="Auth",
        problem="외부 사용자가 자기 ID로 들어올 길이 없다",
        value_created="신원 확인된 세션",
        ref_actor_ids=["operator", "user"],
        ref_value_ids=["cv-trust"],
        ref_identity_ids=["id-secure"],
    )
    assert n.problem.startswith("외부 사용자")
    assert n.value_created == "신원 확인된 세션"
    assert n.ref_actor_ids == ["operator", "user"]
    assert n.ref_value_ids == ["cv-trust"]


def test_feature_refs_round_trip_through_canvas() -> None:
    """Service ref-id arrays persist + are readable by id after a CanvasDoc
    round-trip. ``service`` lives on the Services canvas (D-2026-06-17-D
    removed it from the feature-rooted feature), so the round-trip
    is exercised there."""
    services = CanvasDoc(
        canvas_id="services",
        canvas_kind="services",
        nodes=[
            ServiceNode(id="auth", label="Auth"),
            ServiceNode(
                id="login",
                label="Login",
                problem="로그인이 번거롭다",
                value_created="유효한 세션 토큰",
                ref_actor_ids=["user"],
            ),
        ],
    )
    parsed = CanvasDoc.model_validate(services.model_dump())
    login = next(n for n in parsed.nodes if n.id == "login")
    assert login.problem.startswith("로그인이")
    assert login.ref_actor_ids == ["user"]


# ---------------------------------------------------------------------------
# v0.10 Step 5 — metric / step composition kinds
# ---------------------------------------------------------------------------


def test_step_node_carries_typed_fields() -> None:
    n = StepNode(
        id="s-verify",
        label="Verify credentials",
        order=2,
        outcome="세션 토큰 발급 OR 401 반환",
    )
    assert n.order == 2
    assert "세션 토큰" in n.outcome


def test_step_order_optional() -> None:
    """Unordered steps (parallel branches) leave ``order`` at ``None``."""
    n = StepNode(id="s-async", label="Send email")
    assert n.order is None


def test_feature_accepts_step() -> None:
    CanvasDoc(
        canvas_id="auth",
        canvas_kind="feature",
        feature_ref="auth",
        nodes=[
            FeatureNode(id="auth", label="Auth"),
            StepNode(
                id="s1",
                label="Verify credentials",
                order=1,
            ),
            ActorRefNode(id="ar-op", label="→ op", ref_actor_id="operator", side="operator"),
            ActorRefNode(id="ar-user", label="→ user", ref_actor_id="user", side="user"),
        ],
    )


def test_step_requires_service_parent() -> None:
    """v0.26.0 (D-2026-05-25-A) — same as ``test_metric_requires_service_parent``;
    parent_id validator removed; constraint moved out of the schema.
    Root is a feature (D-2026-06-17-D — the detail canvas drills into a
    feature)."""
    CanvasDoc(
        canvas_id="auth",
        canvas_kind="feature",
        feature_ref="auth",
        nodes=[
            FeatureNode(id="auth", label="Auth"),
            StepNode(id="s1", label="Stray"),
            ActorRefNode(id="ar-op", label="→ op", ref_actor_id="op", side="operator"),
            ActorRefNode(id="ar-u", label="→ u", ref_actor_id="u", side="user"),
        ],
    )


def test_services_canvas_rejects_step() -> None:
    """step belongs inside feature, not on the overview."""
    with pytest.raises(ValueError, match="not allowed"):
        CanvasDoc(
            canvas_id="services",
            canvas_kind="services",
            nodes=[
                ServiceNode(id="auth", label="Auth"),
                StepNode(id="s1", label="Stray"),
            ],
        )


# ---------------------------------------------------------------------------
# v0.10 Step 6 — rule + content typed-field polish
# ---------------------------------------------------------------------------


def test_rule_typed_fields_round_trip() -> None:
    n = RuleNode(
        id="r-pwd",
        label="Password policy",
        policy="비밀번호 8자 이상 + 숫자 + 특수문자",
        enforcement="가입 폼 + 비밀번호 변경 화면에서 검증",
        actor_permissions={"user": "RUD", "admin": "CRUD"},
    )
    assert n.policy.startswith("비밀번호 8자")
    assert n.enforcement.startswith("가입 폼")
    assert n.actor_permissions == {"user": "RUD", "admin": "CRUD"}


def test_actor_permissions_default_empty() -> None:
    """A RuleNode without actor_permissions still validates and serialises
    through the SketchNode discriminated union (TypeAdapter dispatch)."""
    n = RuleNode(id="r1", label="R")
    assert n.actor_permissions == {}
    parsed = SketchNodeAdapter.validate_python(n.model_dump())
    assert isinstance(parsed, RuleNode)
    assert parsed.actor_permissions == {}


def test_actor_permissions_round_trip_through_canvas() -> None:
    """Permission dict survives a full CanvasDoc serialise/parse cycle."""
    canvas = CanvasDoc(
        canvas_id="auth",
        canvas_kind="feature",
        feature_ref="auth",
        nodes=[
            FeatureNode(id="auth", label="Auth"),
            RuleNode(
                id="r1",
                label="Post permissions",
                policy="자기 글만 수정/삭제",
                actor_permissions={
                    "user": "RUD-self",
                    "admin": "CRUD-all",
                },
            ),
            ActorRefNode(id="ar-op", label="→ op", ref_actor_id="operator", side="operator"),
            ActorRefNode(id="ar-user", label="→ user", ref_actor_id="user", side="user"),
        ],
    )
    parsed = CanvasDoc.model_validate(canvas.model_dump())
    rule = next(n for n in parsed.nodes if n.id == "r1")
    assert rule.actor_permissions["user"] == "RUD-self"
    assert rule.actor_permissions["admin"] == "CRUD-all"


def test_detail_canvas_actor_kind_rejected() -> None:
    """Raw actors belong in the Actor canvas, not Detail."""
    with pytest.raises(ValueError, match="not allowed"):
        CanvasDoc(
            canvas_id="order",
            canvas_kind="feature",
            feature_ref="order",
            nodes=[
                *_detail_seed(),
                ActorNode(id="a1", label="Raw actor"),
            ],
        )


def test_detail_canvas_missing_root_feature_rejected() -> None:
    # D-2026-06-17-D — the detail canvas drills into a root *feature*; an
    # empty (or root-less) canvas is rejected for lacking it.
    with pytest.raises(ValueError, match="root feature"):
        CanvasDoc(
            canvas_id="order",
            canvas_kind="feature",
            feature_ref="order",
            nodes=[],
        )


# ---------------------------------------------------------------------------
# shared validators (edges + parent_id) still apply
# ---------------------------------------------------------------------------


def test_edges_referencing_unknown_nodes_rejected() -> None:
    with pytest.raises(ValueError, match="unknown nodes"):
        CanvasDoc(
            canvas_id="actors",
            canvas_kind="actors",
            nodes=[ActorNode(id="user", label="U")],
            edges=[SketchEdge(id="e1", source="user", target="ghost")],
        )


# ---------------------------------------------------------------------------
# v0.16.37 — D-2026-05-13-M (anchor edge 422 reject fix)
# ---------------------------------------------------------------------------


def test_edge_from_synthetic_anchor_to_user_node_accepted() -> None:
    """D-2026-05-04-B SPEC mandate: user may draw edges from / to the
    synthetic project anchor like any other node. The anchor itself
    lives in ``ProjectDoc.anchors``, not in ``canvas.nodes`` — the
    validator must whitelist its id so anchor edges don't 422 reject.
    Regression for D-2026-05-13-M (user complaint
    *"새로 고침하면 연결선이 사라지죠"*)."""
    from mashbill.models import PROJECT_ANCHOR_ID

    doc = CanvasDoc(
        canvas_id="actors",
        canvas_kind="actors",
        nodes=[
            ActorNode(id="operator", label="Op"),
            ActorNode(id="user", label="U"),
        ],
        edges=[
            SketchEdge(
                id="e_anchor_to_user",
                source=PROJECT_ANCHOR_ID,
                target="user",
            ),
        ],
    )
    assert doc.edges[0].source == PROJECT_ANCHOR_ID
    assert doc.edges[0].target == "user"


def test_edge_from_user_node_to_synthetic_anchor_accepted() -> None:
    """Direction-symmetric companion of the above — D-2026-05-04-B's
    *"from / to the anchor"* covers both directions."""
    from mashbill.models import PROJECT_ANCHOR_ID

    doc = CanvasDoc(
        canvas_id="actors",
        canvas_kind="actors",
        nodes=[
            ActorNode(id="operator", label="Op"),
            ActorNode(id="user", label="U"),
        ],
        edges=[
            SketchEdge(
                id="e_user_to_anchor",
                source="user",
                target=PROJECT_ANCHOR_ID,
            ),
        ],
    )
    assert doc.edges[0].target == PROJECT_ANCHOR_ID


def test_dangling_edge_error_message_reports_missing_endpoint_not_edge_id() -> None:
    """v0.16.37 bug fix: prior to D-2026-05-13-M, the validator's error
    message reported *edge ids* (``e_<timestamp>_<rand>``) as if they
    were missing node ids. This sent D-2026-05-13-I diagnosis down a
    wrong path. The fixed message reports the actual missing endpoint
    id."""
    with pytest.raises(ValueError, match=r"'ghost_node'") as exc:
        CanvasDoc(
            canvas_id="actors",
            canvas_kind="actors",
            nodes=[ActorNode(id="user", label="U")],
            edges=[
                SketchEdge(
                    id="e_mp2vvxg9_k9cq",  # edge id — must NOT appear in msg
                    source="user",
                    target="ghost_node",
                ),
            ],
        )
    # Edge id must not be in the error message (the old bug).
    assert "e_mp2vvxg9_k9cq" not in str(exc.value)


def test_dangling_edge_reports_multiple_missing_endpoints_sorted() -> None:
    """When multiple edges have different missing endpoints, the error
    message lists each distinct missing id (sorted), not duplicates."""
    with pytest.raises(ValueError, match="unknown nodes") as exc:
        CanvasDoc(
            canvas_id="actors",
            canvas_kind="actors",
            nodes=[ActorNode(id="user", label="U")],
            edges=[
                SketchEdge(id="e1", source="user", target="ghost_a"),
                SketchEdge(id="e2", source="ghost_b", target="user"),
                SketchEdge(id="e3", source="user", target="ghost_a"),
            ],
        )
    msg = str(exc.value)
    assert "ghost_a" in msg
    assert "ghost_b" in msg
    # 'user' is a valid node — must NOT be in the error.
    assert "'user'" not in msg
    # Edge ids must NOT appear.
    assert "'e1'" not in msg
    assert "'e2'" not in msg


def test_edge_with_one_anchor_one_ghost_endpoint_reports_only_ghost() -> None:
    """Anchor id is whitelisted; if only the *other* endpoint is
    missing, only that endpoint must appear in the error message."""
    from mashbill.models import PROJECT_ANCHOR_ID

    with pytest.raises(ValueError, match="unknown nodes") as exc:
        CanvasDoc(
            canvas_id="actors",
            canvas_kind="actors",
            nodes=[ActorNode(id="user", label="U")],
            edges=[
                SketchEdge(
                    id="e_mixed",
                    source=PROJECT_ANCHOR_ID,
                    target="ghost_x",
                ),
            ],
        )
    msg = str(exc.value)
    assert "ghost_x" in msg
    assert PROJECT_ANCHOR_ID not in msg


def test_parent_cycle_rejected() -> None:
    """v0.26.0 (D-2026-05-25-A) — parent_id cycle validator removed
    alongside the field. Directed-edge cycles are now expressible in
    canvas.json; the propagation walk's visited-set is the runtime
    guard. The test stays as a marker (the prior parent_id chain that
    triggered cycle rejection no longer exists)."""
    CanvasDoc(
        canvas_id="actors",
        canvas_kind="actors",
        nodes=[
            ActorNode(id="a", label="A"),
            ActorNode(id="b", label="B"),
        ],
    )


# ---------------------------------------------------------------------------
# note edgeless invariant (D-2026-06-17-F)
# ---------------------------------------------------------------------------


def _detail_with_note(edges: list[SketchEdge]) -> CanvasDoc:
    """A minimal valid feature canvas carrying a note node."""
    return CanvasDoc(
        canvas_id="svc1",
        canvas_kind="feature",
        feature_ref="svc1",
        nodes=[
            FeatureNode(id="svc1", label="S"),
            ActorRefNode(id="ar1", label="→A", ref_actor_id="a1"),
            NoteNode(id="n1", label="ctx", body="mobile-first, body ≤ 500 chars"),
        ],
        edges=edges,
    )


def test_note_without_edges_is_valid() -> None:
    _detail_with_note(edges=[])  # no raise


def test_note_as_edge_target_is_rejected() -> None:
    with pytest.raises(ValueError, match="note nodes must be edgeless"):
        _detail_with_note(edges=[SketchEdge(id="e1", source="ar1", target="n1")])


def test_note_as_edge_source_is_rejected() -> None:
    with pytest.raises(ValueError, match="note nodes must be edgeless"):
        _detail_with_note(edges=[SketchEdge(id="e1", source="n1", target="ar1")])
