"""Participation chain (D-2026-07-05-E, user-pinned 2026-07-05).

Every layer of the services canvas names WHO participates: category(=접점,
touchpoint) and feature gain ``ref_actor_ids`` (service already carried it),
assignable through ``set_node_references`` with the same Fail-Fast id
validation. Narrowing (a service's participants stay within its touchpoint's,
a feature's within its service's) is coached/UI-soft — never a validator
(D-2026-07-04-P lesson: partial states must stay saveable).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mashbill.canvas_io import create_node
from mashbill.project_io import create_project
from mashbill.references import set_node_references
from mashbill.workspace import resolve_plot_root


@pytest.fixture
def plot_root(tmp_path: Path) -> Path:
    root = resolve_plot_root(str(tmp_path))
    create_project(root, "alpha", "Alpha")
    return root


def _actor(plot_root: Path, label: str) -> str:
    return create_node(plot_root, "alpha", "actors", "actor", {"label": label})["node"]["id"]


def test_category_takes_actor_participants(plot_root: Path) -> None:
    actor = _actor(plot_root, "고객")
    cat = create_node(plot_root, "alpha", "services", "category", {"label": "고객 앱"})["node"][
        "id"
    ]
    out = set_node_references(
        plot_root, "alpha", "services", cat, {"ref_actor_ids": [actor]}
    )
    assert out["node"]["ref_actor_ids"] == [actor]


def test_feature_takes_actor_participants(plot_root: Path) -> None:
    actor = _actor(plot_root, "고객")
    feat = create_node(plot_root, "alpha", "services", "feature", {"label": "주문하기"})["node"][
        "id"
    ]
    out = set_node_references(
        plot_root, "alpha", "services", feat, {"ref_actor_ids": [actor]}
    )
    assert out["node"]["ref_actor_ids"] == [actor]


def test_category_participant_must_exist_on_actors_canvas(plot_root: Path) -> None:
    cat = create_node(plot_root, "alpha", "services", "category", {"label": "고객 앱"})["node"][
        "id"
    ]
    with pytest.raises(ValueError, match="ref_actor_ids"):
        set_node_references(
            plot_root, "alpha", "services", cat, {"ref_actor_ids": ["ghost"]}
        )


def test_partial_participation_is_saveable(plot_root: Path) -> None:
    """Narrowing is SOFT: a feature may name a participant its service has
    not (yet) — mid-construction states never reject (D-2026-07-04-P)."""
    actor = _actor(plot_root, "라이더")
    feat = create_node(plot_root, "alpha", "services", "feature", {"label": "배차"})["node"]["id"]
    out = set_node_references(
        plot_root, "alpha", "services", feat, {"ref_actor_ids": [actor]}
    )
    assert out["node"]["ref_actor_ids"] == [actor]
