"""Dangling-edge drop-on-read (D-2026-06-21-X — read-path leniency).

The ``CanvasDoc`` validator hard-rejects a canvas whose edge points at a node
that is not present (``edges reference unknown nodes``). On the *write* path that
is correct — the viewer prunes dangling edges before save (D-2026-06-21-R), so a
PUT carrying one is a bug. But on the *read* path the same rejection wedges a
canvas that was already corrupted on disk (a node removed without its edges):
the GET 400s and the canvas never opens.

``canvas_io._drop_dangling_edges`` strips such edges on read so the canvas loads.
The synthetic project anchor (``PROJECT_ANCHOR_ID``) is a valid endpoint
(D-2026-05-04-B), so an edge to it survives. These tests pin the unit helper plus
the ``read_canvas`` integration.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mashbill.canvas_io import _drop_dangling_edges, read_canvas
from mashbill.folder_io import create_project
from mashbill.git_store import init_workspace_repo
from mashbill.models_foundation import PROJECT_ANCHOR_ID
from mashbill.storage import _canvas_file, _read_json, _write_json
from mashbill.workspace import resolve_plot_root


@pytest.fixture
def plot_root(tmp_path: Path) -> Path:
    init_workspace_repo(tmp_path)
    return resolve_plot_root(str(tmp_path))


def test_drop_dangling_edges_strips_edge_to_missing_node(plot_root: Path) -> None:
    raw = {
        "nodes": [{"id": "a1", "kind": "actor", "label": "User"}],
        "edges": [
            {"id": "e_ok", "source": "a1", "target": "a1"},
            {"id": "e_bad", "source": "a1", "target": "ghost"},
        ],
    }
    out = _drop_dangling_edges(plot_root, "alpha", "actors", None, raw)
    assert [e["id"] for e in out["edges"]] == ["e_ok"], "edge to missing node dropped"
    assert [n["id"] for n in out["nodes"]] == ["a1"], "nodes untouched"


def test_drop_dangling_edges_keeps_edge_to_project_anchor(plot_root: Path) -> None:
    raw = {
        "nodes": [{"id": "m1", "kind": "mission", "label": "M"}],
        "edges": [{"id": "e_anchor", "source": PROJECT_ANCHOR_ID, "target": "m1"}],
    }
    out = _drop_dangling_edges(plot_root, "alpha", "foundation", None, raw)
    assert [e["id"] for e in out["edges"]] == ["e_anchor"], "anchor edge survives"


def test_drop_dangling_edges_is_noop_when_clean(plot_root: Path) -> None:
    raw = {
        "nodes": [{"id": "a1", "kind": "actor"}],
        "edges": [{"id": "e1", "source": "a1", "target": "a1"}],
    }
    out = _drop_dangling_edges(plot_root, "alpha", "actors", None, raw)
    assert out == raw, "a canvas with no dangling edges is returned unchanged"


def test_read_canvas_loads_canvas_with_dangling_edge_on_disk(plot_root: Path) -> None:
    """End-to-end: a canvas.json corrupted with a dangling edge opens (no 400)."""
    create_project(plot_root, "alpha", "Alpha")
    # Blank-canvas start (D-2026-07-04-P): plant one actor, then corrupt the
    # canvas with a dangling edge on disk.
    path = _canvas_file(plot_root, "alpha", "actors", None)
    raw = _read_json(path)
    raw["nodes"] = [{"id": "a1", "kind": "actor", "label": "구매자", "x": 0, "y": 0}]
    raw["edges"] = [{"id": "e_bad", "source": "a1", "target": "ghost"}]
    _write_json(path, raw)

    loaded = read_canvas(plot_root, "alpha", "actors")
    assert loaded.edges == [], "dangling edge dropped on read instead of rejected"
    # Healed on disk (idempotent persist).
    assert _read_json(path)["edges"] == [], "corruption healed in the persisted file"
