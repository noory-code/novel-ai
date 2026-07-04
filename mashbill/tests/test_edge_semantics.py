"""Edge semantic classifier — v0.30.0 (D-2026-05-31-C).

The truth table here is the byte-for-byte mirror of
``viewer/src/flow/edgeSemantics.ts`` (and its vitest
``tests/edge-semantics.test.ts``). Keeping the two identical is what
lets the stored ``relation`` field be assigned consistently whether an
edge is created in the viewer or migrated on the server.
"""

from __future__ import annotations

import pytest

from mashbill.edge_semantics import classify_edge, fold_endpoints
from mashbill.models import SketchEdge

# (canvas_kind, source_kind) -> expected relation. Mirror of the TS
# vitest cases exactly.
_CASES = [
    # actors canvas: every edge is inheritance (single edge type)
    ("actors", "actor", "inheritance"),
    ("actors", "project", "inheritance"),
    # foundation essence masters -> injection
    ("foundation", "mission", "injection"),
    ("foundation", "core_value", "injection"),
    ("foundation", "identity", "injection"),
    # (mission_ref / value_ref / identity_ref retired 2026-06-20 — D-2026-06-20-G)
    # actor_ref (the subject) is flow, not injection
    ("feature", "actor_ref", "flow"),
    # step / decision / service / category -> flow
    ("feature", "step", "flow"),
    ("feature", "decision", "flow"),
    ("services", "service", "flow"),
    ("services", "category", "flow"),
    # entity↔entity rough relationship (entities canvas) -> flow
    # (D-2026-06-20-Q step 7 / D-2026-06-17-J)
    ("entities", "entity", "flow"),
    # unknown / None sources -> flow
    ("foundation", None, "flow"),
    ("services", "bogus", "flow"),
]


@pytest.mark.parametrize("canvas_kind,source_kind,expected", _CASES)
def test_classify_edge(canvas_kind: str, source_kind: str | None, expected: str) -> None:
    assert classify_edge(canvas_kind, source_kind) == expected


def test_actors_labeled_edge_is_a_value_flow() -> None:
    """B-35 (user live-watch 2026-07-04): the actors canvas has TWO edge
    meanings since the hierarchy rounds — taxonomy lines (family ← concrete,
    no label) and value-flow lines (giver → receiver, label = what moves:
    돈, 신뢰, 콘텐츠). The v0.30.0 "single edge type" table stamped BOTH as
    inheritance, so flow lines polluted the fold hierarchy (fold buttons on
    leaves, collapsing hid trade partners). A label at creation is the
    discriminator; unlabeled user-drawn lines keep today's default."""
    assert classify_edge("actors", "actor", label="돈") == "flow"
    assert classify_edge("actors", "actor", label=None) == "inheritance"
    assert classify_edge("actors", "actor", label="") == "inheritance"


def test_entity_edges_default_to_flow() -> None:
    """D-2026-06-20-Q step 7 — an entity↔entity edge is a rough, directed
    conceptual link (flow), editable; never a meaningless / FK / cardinality
    line. Pins the documented fallthrough so a future classify change can't
    silently re-route entity edges."""
    assert classify_edge("entities", "entity") == "flow"


def test_relation_value_set_is_the_pinned_three() -> None:
    """SSOT guard for the engine half of ``SketchEdge.relation``.

    The stored ``relation`` field is read on both sides (D-2026-05-31-C).
    After the open-core cut (D-2026-06-20-L / -M) the viewer ``EdgeRelation``
    union moved to the app repo, so the former cross-repo regex parity is
    re-homed in the app's vitest (``edge-semantics.test.ts``). This pins the
    engine value set explicitly so neither half can quietly drift from the
    agreed three relations."""
    import typing

    from mashbill.models import SketchEdge

    py_values = set(typing.get_args(SketchEdge.model_fields["relation"].annotation))
    assert py_values == {"flow", "injection", "inheritance"}


# --- fold_endpoints: the parent/child the fold + publish hierarchy walks ------
#
# fold_endpoints derives (parent, child) from the edge's STORED relation. It is
# the server-side mirror of viewer/src/flow/foldHierarchy.ts::foldEndpoints and
# feeds fold + publish MINOR-bump propagation. A silent break here inverts or
# drops a hierarchy edge → wrong fold / wrong publish baseline, with no error.


def _edge(source: str, target: str, **kw: object) -> SketchEdge:
    return SketchEdge(id=f"{source}->{target}", source=source, target=target, **kw)


def test_fold_flow_source_is_parent() -> None:
    # flow: the source is the parent (source → target).
    assert fold_endpoints(_edge("p", "c", relation="flow")) == ("p", "c")


def test_fold_inheritance_is_inverted_target_is_parent() -> None:
    # inheritance: the arrow points child → superclass, so the *target* is the
    # parent. This inversion is the easy thing to regress.
    assert fold_endpoints(_edge("child", "super", relation="inheritance")) == (
        "super",
        "child",
    )


def test_fold_actors_flow_edge_defines_no_hierarchy() -> None:
    """B-35 mirror of viewer foldHierarchy: an actors-canvas flow edge is a
    peer value exchange (giver → receiver), never containment."""
    e = _edge(source="seller", target="buyer", relation="flow")
    assert fold_endpoints(e, canvas_kind="actors") is None
    assert fold_endpoints(e, canvas_kind="services") == ("seller", "buyer")
    assert fold_endpoints(e) == ("seller", "buyer")


def test_fold_injection_defines_no_hierarchy() -> None:
    # injection: an essence overlay does not contain its target → no hierarchy.
    assert fold_endpoints(_edge("mission", "svc", relation="injection")) is None


def test_fold_undirected_edge_defines_no_hierarchy() -> None:
    assert fold_endpoints(_edge("a", "b", relation="flow", directed=False)) is None


def test_fold_defaults_to_flow_hierarchy() -> None:
    # A bare edge (relation defaulting on the model) folds as flow (source parent),
    # so a created-but-unclassified edge still participates correctly.
    e = _edge("a", "b")
    assert fold_endpoints(e) == ("a", "b")
