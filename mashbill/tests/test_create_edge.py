"""``create_edge`` — clobber-safe single-edge append (D-2026-07-02-J).

Benchmark finding (2026-07-02): every coach-registered feature floated
unconnected — 0 service→feature edges across the batch — because the coach had
a safe way to add nodes (``create_node``) but no safe way to draw the line
(only the clobber-unsafe whole-doc ``update_canvas``). ``create_edge`` mirrors
``create_node``: validate both endpoints exist, mint the id server-side,
classify the relation from canvas + source kind, append the ONE edge,
re-validate the whole doc, write atomically. Idempotent: an existing directed
source→target edge is returned, never duplicated.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mashbill.folder_io import create_edge, create_node, create_project, read_canvas
from mashbill.workspace import resolve_plot_root


def _setup(tmp_path: Path) -> Path:
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    return plot_root


def _services_pair(plot_root: Path) -> tuple[str, str]:
    """A service + feature on the services canvas; returns their ids."""
    svc = create_node(plot_root, "alpha", "services", "service", {"label": "Compose"})
    feat = create_node(plot_root, "alpha", "services", "feature", {"label": "Draft together"})
    return svc["node"]["id"], feat["node"]["id"]


def test_create_edge_connects_service_to_feature(tmp_path: Path) -> None:
    plot_root = _setup(tmp_path)
    sid, fid = _services_pair(plot_root)
    out = create_edge(plot_root, "alpha", "services", sid, fid)
    edge = out["edge"]
    assert edge["source"] == sid and edge["target"] == fid
    assert edge["directed"] is True
    assert edge["relation"] == "flow"  # services canvas, non-essence source
    canvas = read_canvas(plot_root, "alpha", "services")
    assert len(canvas.edges) == 1


def test_create_edge_missing_endpoint_raises(tmp_path: Path) -> None:
    plot_root = _setup(tmp_path)
    sid, _ = _services_pair(plot_root)
    with pytest.raises(ValueError, match="ghost"):
        create_edge(plot_root, "alpha", "services", sid, "ghost")


def test_create_edge_is_idempotent(tmp_path: Path) -> None:
    plot_root = _setup(tmp_path)
    sid, fid = _services_pair(plot_root)
    first = create_edge(plot_root, "alpha", "services", sid, fid)
    second = create_edge(plot_root, "alpha", "services", sid, fid)
    assert second["edge"]["id"] == first["edge"]["id"]
    canvas = read_canvas(plot_root, "alpha", "services")
    assert len(canvas.edges) == 1  # no duplicate line


def test_create_edge_actors_canvas_classifies_inheritance(tmp_path: Path) -> None:
    plot_root = _setup(tmp_path)
    a = create_node(plot_root, "alpha", "actors", "actor", {"label": "Host"})
    b = create_node(plot_root, "alpha", "actors", "actor", {"label": "Superhost"})
    out = create_edge(plot_root, "alpha", "actors", b["node"]["id"], a["node"]["id"])
    assert out["edge"]["relation"] == "inheritance"


def test_write_playbook_connects_registered_features() -> None:
    """The prompt must tell the coach to draw the line in the same confirmed
    action as the node it registered — one yes covers the feature AND its
    connection to the service."""
    from mashbill.chat_context import WRITE_PLAYBOOK

    p = WRITE_PLAYBOOK.lower()
    assert "create_edge" in p
    assert "connect" in p


def test_create_edge_accepts_the_synthetic_anchor(tmp_path: Path) -> None:
    """B-14 root cause (user live-watch 2026-07-03, D-2026-07-03-T): the
    project anchor is viewer-synthetic — not a node in the doc — so
    create_edge's both-endpoints-exist check rejected every anchor spoke and
    coach-registered foundation pillars floated forever. The anchor id is a
    valid endpoint (canvas_io doc validation already says so); relation
    mirrors the seed spokes (flow)."""
    plot_root = _setup(tmp_path)
    cv = create_node(plot_root, "alpha", "foundation", "core_value", {"label": "신뢰"})
    cvid = cv["node"]["id"]
    out = create_edge(plot_root, "alpha", "foundation", "__project_anchor__", cvid)
    assert out["existing"] is False
    assert out["edge"]["source"] == "__project_anchor__"
    assert out["edge"]["relation"] == "flow"
    # idempotent like any other edge
    again = create_edge(plot_root, "alpha", "foundation", "__project_anchor__", cvid)
    assert again["existing"] is True
