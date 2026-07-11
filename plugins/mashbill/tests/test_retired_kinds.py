"""Retired-kind drop-on-read (D-2026-06-19-H — `group` retirement, 2026-06-20).

When a kind leaves the palette its discriminant is removed from the
``SketchNode`` union, so a node of that kind in an older ``canvas.json`` would
fail ``CanvasDoc.model_validate``. ``canvas_io._drop_retired_kinds`` strips such
nodes (and any edge incident to them) on read — loss-free for surviving content
(retiring ``group`` drops only the container, never its member step/decision
nodes). These tests pin that behaviour at the unit level (the read_canvas wiring
is one call; the full suite guards no-regression).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mashbill.canvas_io import RETIRED_KINDS, _drop_retired_kinds
from mashbill.git_store import init_workspace_repo
from mashbill.workspace import resolve_plot_root


@pytest.fixture
def plot_root(tmp_path: Path) -> Path:
    init_workspace_repo(tmp_path)
    return resolve_plot_root(str(tmp_path))


def test_group_is_a_retired_kind() -> None:
    """`group` retired 2026-06-20 (D-2026-06-19-H — chunking = feature level;
    folding a flow is a view affordance, not a node kind)."""
    assert "group" in RETIRED_KINDS


def test_drop_retired_kinds_strips_group_and_incident_edges(plot_root: Path) -> None:
    raw = {
        "nodes": [
            {"id": "s1", "kind": "step", "label": "do"},
            {"id": "g1", "kind": "group", "label": "chunk", "member_ids": ["s1"]},
        ],
        "edges": [{"id": "e1", "source": "g1", "target": "s1"}],
    }
    out = _drop_retired_kinds(plot_root, "alpha", "feature", "svc1", raw)
    assert "group" not in {n["kind"] for n in out["nodes"]}, "retired group node dropped"
    assert [n["id"] for n in out["nodes"]] == ["s1"], "member step survives (loss-free)"
    assert out["edges"] == [], "edge incident to the dropped group is removed"


def test_drop_retired_kinds_is_noop_without_retired_nodes(plot_root: Path) -> None:
    raw = {"nodes": [{"id": "s1", "kind": "step"}], "edges": []}
    out = _drop_retired_kinds(plot_root, "alpha", "feature", "svc1", raw)
    assert out == raw, "a canvas with no retired kinds is returned unchanged"


@pytest.mark.parametrize("kind", sorted(RETIRED_KINDS))
def test_every_retired_kind_is_dropped_on_read(plot_root: Path, kind: str) -> None:
    """Every member of ``RETIRED_KINDS`` — not only ``group`` — is stripped on read,
    with surrounding live content (and only the incident edge) removed. Parametrising
    over the set itself means a future retirement is covered the moment the kind is
    added to ``RETIRED_KINDS``."""
    raw = {
        "nodes": [
            {"id": "live", "kind": "step", "label": "keep"},
            {"id": "dead", "kind": kind, "label": "retired"},
        ],
        "edges": [{"id": "e1", "source": "dead", "target": "live"}],
    }
    out = _drop_retired_kinds(plot_root, "alpha", "feature", "svc1", raw)
    surviving = {n["id"] for n in out["nodes"]}
    assert "dead" not in surviving, f"retired kind {kind!r} not dropped on read"
    assert surviving == {"live"}, "live content survives (loss-free)"
    assert out["edges"] == [], "edge incident to the dropped node is removed"


def test_retired_kinds_membership_is_pinned() -> None:
    """The retired set must not silently *shrink* — re-admitting a kind to the live
    union without a deliberate un-retirement would let old canvases fail validation
    again. Parametrising over the set (above) cannot catch a kind dropped FROM it, so
    pin the known retirements explicitly. Adding a new retirement = update this set +
    this assertion together (intentional friction, mirrors the kind-count guards)."""
    assert RETIRED_KINDS == frozenset(
        {"group", "mission_ref", "value_ref", "identity_ref", "metric", "content"}
    )
