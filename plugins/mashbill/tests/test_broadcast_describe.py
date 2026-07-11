"""``_describe_change`` — map a changed file under a Novel data root to the
``{project_id, canvas_kind?, service_id?}`` descriptor the viewer keys its
refetch on.

Regression: D-2026-06-21-AB flattened the on-disk layout to
``.noory/plot/{canvas_kind}/canvas.json`` (one project per root, no
``{project_id}`` path segment), but ``_describe_change`` kept assuming the
legacy ``{plot_root}/{project_id}/{canvas_kind}/canvas.json`` shape and read
``parts[0]`` as the project id. On the flat layout that makes
``project_id == "<canvas_kind>"`` and drops ``canvas_kind`` entirely — so the
viewer treats every external write as "some other project changed" and skips
the canvas refetch. The bug had ZERO test coverage, which is why it shipped.
"""

from __future__ import annotations

from pathlib import Path

from mashbill.broadcast import _describe_change
from mashbill.folder_io import create_project, write_canvas
from mashbill.models import CanvasDoc, IdentityNode, MissionNode
from mashbill.workspace import resolve_plot_root


def _setup(tmp_path: Path, project_id: str = "alpha") -> Path:
    """Flat layout: ``{tmp}/.noory/plot/`` with ``project.json`` +
    ``foundation/canvas.json`` directly under it (no project_id segment)."""
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, project_id, "Alpha")
    write_canvas(
        plot_root,
        project_id,
        CanvasDoc(
            canvas_id="foundation",
            canvas_kind="foundation",
            nodes=[
                MissionNode(id="m1", label="Mission", statement="s", body="b"),
                IdentityNode(id="i1", label="Identity"),
            ],
        ),
    )
    write_canvas(
        plot_root,
        project_id,
        CanvasDoc(canvas_id="services", canvas_kind="services", nodes=[]),
    )
    return plot_root


def test_singleton_canvas_change_carries_real_project_id_and_kind(tmp_path: Path) -> None:
    plot_root = _setup(tmp_path)
    changed = plot_root / "foundation" / "canvas.json"

    d = _describe_change(plot_root, changed)

    assert d is not None
    # project_id must be the real project ("alpha"), NOT the canvas kind.
    assert d["project_id"] == "alpha"
    # canvas_kind must be present so the viewer refetches that canvas.
    assert d["canvas_kind"] == "foundation"


def test_services_canvas_change_maps_to_services_kind(tmp_path: Path) -> None:
    plot_root = _setup(tmp_path)
    changed = plot_root / "services" / "canvas.json"

    d = _describe_change(plot_root, changed)

    assert d is not None
    assert d["project_id"] == "alpha"
    assert d["canvas_kind"] == "services"


def test_feature_detail_change_maps_to_feature_kind_with_service_id(tmp_path: Path) -> None:
    plot_root = _setup(tmp_path)
    changed = plot_root / "services" / "order" / "detail.json"

    d = _describe_change(plot_root, changed)

    assert d is not None
    assert d["project_id"] == "alpha"
    assert d["canvas_kind"] == "feature"
    assert d["service_id"] == "order"


def test_project_json_change_is_project_level_without_canvas_kind(tmp_path: Path) -> None:
    plot_root = _setup(tmp_path)
    changed = plot_root / "project.json"

    d = _describe_change(plot_root, changed)

    assert d is not None
    assert d["project_id"] == "alpha"
    assert "canvas_kind" not in d


def test_foundation_per_node_md_reloads_foundation(tmp_path: Path) -> None:
    plot_root = _setup(tmp_path)
    changed = plot_root / "foundation" / "mission-m1.md"

    d = _describe_change(plot_root, changed)

    assert d is not None
    assert d["project_id"] == "alpha"
    assert d["canvas_kind"] == "foundation"


def test_unrelated_path_outside_root_is_none(tmp_path: Path) -> None:
    plot_root = _setup(tmp_path)
    assert _describe_change(plot_root, Path("/etc/hosts")) is None
