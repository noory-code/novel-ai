"""Overview ↔ Detail auto-sync."""

from __future__ import annotations

from pathlib import Path

import pytest

from mashbill.folder_io import (
    create_project,
    list_feature_details,
    read_canvas,
    sync_details_with_overview,
    write_canvas,
)
from mashbill.models import CanvasDoc, CategoryNode, FeatureNode, ServiceNode, SketchNode
from mashbill.workspace import resolve_plot_root


@pytest.fixture
def plot_root(tmp_path: Path) -> Path:
    return resolve_plot_root(str(tmp_path))


def _overview_with(feature_labels: dict[str, str]) -> CanvasDoc:
    """v0.94+ (D-2026-06-17-D) — services canvas: features nested under a single
    default service under a single default category. Detail canvases now seed
    per **feature** (the drill target), not per service — selecting a service
    shows its inspector, clicking a feature drills into its detail."""
    nodes: list[SketchNode] = [
        CategoryNode(id="default-cat", label="Default"),
        ServiceNode(id="default-svc", parent_id="default-cat", label="Default service"),
    ]
    nodes.extend(
        FeatureNode(id=fid, parent_id="default-svc", label=label)
        for fid, label in feature_labels.items()
    )
    return CanvasDoc(
        canvas_id="services",
        canvas_kind="services",
        nodes=nodes,
    )


def test_sync_creates_detail_for_new_feature(plot_root: Path) -> None:
    create_project(plot_root, "alpha", "Alpha")
    write_canvas(plot_root, "alpha", _overview_with({"order": "주문"}))
    result = sync_details_with_overview(plot_root, "alpha")
    assert result["created"] == ["order"]
    assert list_feature_details(plot_root, "alpha") == ["order"]
    detail = read_canvas(plot_root, "alpha", "feature", service_id="order")
    assert detail.feature_ref == "order"
    assert any(n.id == "order" for n in detail.nodes)


def test_sync_archives_removed_feature(plot_root: Path) -> None:
    create_project(plot_root, "alpha", "Alpha")
    write_canvas(plot_root, "alpha", _overview_with({"order": "주문", "pay": "결제"}))
    sync_details_with_overview(plot_root, "alpha")
    # remove "pay" from overview
    write_canvas(plot_root, "alpha", _overview_with({"order": "주문"}))
    result = sync_details_with_overview(plot_root, "alpha")
    assert result["archived"] == ["pay"]
    # pay detail moved to _archive, no longer listed as a live detail
    assert "pay" not in list_feature_details(plot_root, "alpha")
    # v0.8: archived service folder moves to ``services/_archive/{sid}/``
    # with its ``detail.json`` (and any ``index.md``) intact.
    archive = plot_root / "services" / "_archive" / "pay" / "detail.json"
    assert archive.is_file()


def test_sync_is_noop_when_overview_matches(plot_root: Path) -> None:
    create_project(plot_root, "alpha", "Alpha")
    write_canvas(plot_root, "alpha", _overview_with({"order": "주문"}))
    sync_details_with_overview(plot_root, "alpha")
    again = sync_details_with_overview(plot_root, "alpha")
    assert again == {"created": [], "archived": [], "skipped_archive": []}


def test_sync_on_empty_overview_is_noop(plot_root: Path) -> None:
    create_project(plot_root, "alpha", "Alpha")
    result = sync_details_with_overview(plot_root, "alpha")
    assert result == {"created": [], "archived": [], "skipped_archive": []}


# v0.27.14 (D-2026-05-28-I) — data-loss guard: when a service disappears
# from the overview but its detail.json carries user-authored content
# (nodes beyond the default seeded feature_ref + 2 actor_refs, or any
# edges), the sync MUST NOT archive it silently. The user's 2026-05-27
# chrome-devtools session lost a root-service node + its detail because
# the previous sync wiped the folder without checking content; this test
# pins the protection so the regression can't recur.
def test_sync_skips_archive_when_detail_has_user_authored_nodes(
    plot_root: Path,
) -> None:
    from mashbill.folder_io import _canvas_file, _write_json

    create_project(plot_root, "alpha", "Alpha")
    write_canvas(plot_root, "alpha", _overview_with({"order": "주문"}))
    sync_details_with_overview(plot_root, "alpha")  # seeds order detail
    # Mutate the detail to include a user-authored extra node.
    detail = read_canvas(plot_root, "alpha", "feature", service_id="order")
    extra = detail.nodes[0].model_copy(
        update={"id": "user_authored_extra", "label": "added by user"}
    )
    detail = detail.model_copy(update={"nodes": list(detail.nodes) + [extra]})
    _write_json(
        _canvas_file(plot_root, "alpha", "feature", service_id="order"),
        detail.model_dump(by_alias=True),
    )
    # Now drop "order" from the overview.
    write_canvas(plot_root, "alpha", _overview_with({}))
    result = sync_details_with_overview(plot_root, "alpha")
    # Detail must NOT have been archived — user content was present.
    assert "order" not in result["archived"], "sync archived a detail with user-authored content"
    # The "skipped" key surfaces the protected services to the caller.
    assert result.get("skipped_archive") == ["order"], (
        "sync must report which detail folders were preserved against the "
        "overview's wishes so the caller can warn the user"
    )
    # Live detail still present on disk.
    live = plot_root / "services" / "order" / "detail.json"
    assert live.is_file()


def test_sync_skips_archive_when_detail_has_user_authored_edges(
    plot_root: Path,
) -> None:
    from mashbill.folder_io import _canvas_file, _write_json

    create_project(plot_root, "alpha", "Alpha")
    write_canvas(plot_root, "alpha", _overview_with({"order": "주문"}))
    sync_details_with_overview(plot_root, "alpha")
    # Add a user-drawn edge between the two seeded actor refs.
    detail = read_canvas(plot_root, "alpha", "feature", service_id="order")
    edge_doc = detail.model_dump(by_alias=True)
    edge_doc["edges"] = [
        {
            "id": "e1",
            "source": "order-operator-ref",
            "target": "order-user-ref",
            "sourceHandle": "r",
            "targetHandle": "l",
            "label": "",
            "style": "solid",
            "directed": True,
            "action_verb": None,
            "value_form": [],
        }
    ]
    _write_json(
        _canvas_file(plot_root, "alpha", "feature", service_id="order"),
        edge_doc,
    )
    write_canvas(plot_root, "alpha", _overview_with({}))
    result = sync_details_with_overview(plot_root, "alpha")
    assert "order" not in result["archived"]
    assert result.get("skipped_archive") == ["order"]


def test_sync_still_archives_an_empty_detail(plot_root: Path) -> None:
    # Default seeded detail (root service + 2 actor refs, no user nodes,
    # no edges) must still archive cleanly — the guard only protects
    # *user-authored* content.
    create_project(plot_root, "alpha", "Alpha")
    write_canvas(plot_root, "alpha", _overview_with({"trial": "trial"}))
    sync_details_with_overview(plot_root, "alpha")
    write_canvas(plot_root, "alpha", _overview_with({}))
    result = sync_details_with_overview(plot_root, "alpha")
    assert result["archived"] == ["trial"]
    assert result.get("skipped_archive", []) == []
