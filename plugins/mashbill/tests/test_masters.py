"""Create a lightweight upstream master from a downstream reference (D-2026-06-19-C).

When a service / feature references an actor / core_value / identity that doesn't
exist yet, the reference is **pick-OR-create**: rather than free-typing, a real
master node is created on its HOME canvas (name only, deepened later by the
home-canvas coach). These tests pin the home-canvas mapping + the create.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from starlette.testclient import TestClient

from mashbill.broadcast import BroadcastHub
from mashbill.folder_io import create_project, read_canvas, write_canvas
from mashbill.http_app import create_http_app
from mashbill.masters import create_master
from mashbill.models import (
    ActorNode,
    CanvasDoc,
    IdentityNode,
    MissionNode,
    SketchNode,
)
from mashbill.workspace import resolve_plot_root


def _foundation() -> CanvasDoc:
    nodes: list[SketchNode] = [
        MissionNode(id="m1", label="Mission", statement="x"),
        IdentityNode(id="i1", label="Identity"),
    ]
    return CanvasDoc(canvas_id="foundation", canvas_kind="foundation", nodes=nodes)


def _actors() -> CanvasDoc:
    nodes: list[SketchNode] = [
        ActorNode(id="a1", label="Operator"),
        ActorNode(id="a2", label="Reader"),
    ]
    return CanvasDoc(canvas_id="actors", canvas_kind="actors", nodes=nodes)


def _setup(tmp_path: Path) -> Path:
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    write_canvas(plot_root, "alpha", _foundation())
    write_canvas(plot_root, "alpha", _actors())
    return plot_root


def test_create_actor_lands_on_actors_canvas(tmp_path: Path) -> None:
    plot_root = _setup(tmp_path)
    new_id = create_master(plot_root, "alpha", "actor", "Moderator")
    actors = read_canvas(plot_root, "alpha", "actors")
    created = next(n for n in actors.nodes if n.id == new_id)
    assert created.kind == "actor"
    assert created.label == "Moderator"


def test_create_core_value_lands_on_foundation(tmp_path: Path) -> None:
    plot_root = _setup(tmp_path)
    new_id = create_master(plot_root, "alpha", "core_value", "Candour")
    foundation = read_canvas(plot_root, "alpha", "foundation")
    created = next(n for n in foundation.nodes if n.id == new_id)
    assert created.kind == "core_value"
    assert created.label == "Candour"


def test_create_identity_lands_on_foundation(tmp_path: Path) -> None:
    plot_root = _setup(tmp_path)
    new_id = create_master(plot_root, "alpha", "identity", "Warm host")
    foundation = read_canvas(plot_root, "alpha", "foundation")
    assert any(n.id == new_id and n.kind == "identity" for n in foundation.nodes)


def test_fresh_masters_are_staggered_not_stacked(tmp_path: Path) -> None:
    plot_root = _setup(tmp_path)
    id1 = create_master(plot_root, "alpha", "core_value", "One")
    id2 = create_master(plot_root, "alpha", "core_value", "Two")
    foundation = read_canvas(plot_root, "alpha", "foundation")
    n1 = next(n for n in foundation.nodes if n.id == id1)
    n2 = next(n for n in foundation.nodes if n.id == id2)
    assert (n1.x, n1.y) != (n2.x, n2.y)


def test_unknown_kind_is_rejected(tmp_path: Path) -> None:
    plot_root = _setup(tmp_path)
    # only actor / core_value / identity are referenceable masters; a service
    # is not created this way.
    with pytest.raises(ValueError):
        create_master(plot_root, "alpha", "service", "Nope")


def test_blank_label_is_rejected(tmp_path: Path) -> None:
    plot_root = _setup(tmp_path)
    with pytest.raises(ValueError):
        create_master(plot_root, "alpha", "core_value", "   ")


# --- HTTP endpoint ---------------------------------------------------------


def test_master_create_endpoint_creates_and_returns_id(tmp_path: Path) -> None:
    plot_root = _setup(tmp_path)
    client = TestClient(create_http_app(hub=BroadcastHub(enable_watchers=False)))
    resp = client.post(
        "/api/projects/alpha/masters",
        params={"project_path": str(tmp_path)},
        json={"kind": "core_value", "label": "Candour"},
    )
    assert resp.status_code == 201, resp.text
    new_id = resp.json()["id"]
    foundation = read_canvas(plot_root, "alpha", "foundation")
    assert any(n.id == new_id and n.label == "Candour" for n in foundation.nodes)


def test_master_create_endpoint_rejects_bad_kind(tmp_path: Path) -> None:
    _setup(tmp_path)
    client = TestClient(create_http_app(hub=BroadcastHub(enable_watchers=False)))
    resp = client.post(
        "/api/projects/alpha/masters",
        params={"project_path": str(tmp_path)},
        json={"kind": "service", "label": "Nope"},
    )
    assert resp.status_code == 400
