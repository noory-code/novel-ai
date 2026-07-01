"""Entity reverse-index — "어디서 쓰이나" back-reference (D-2026-06-20-Q).

The entity registry's value is letting the user see *where each data object is
used*. ``entity_usage`` derives that read-only: it scans every feature detail
canvas's ``step.ref_entity_ids`` for the entity id and returns the features
(and the referencing step labels) that use it. No data is authored here — it is
a pure projection over the steps the user / AI already wired.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mashbill.entity_refs import entity_usage
from mashbill.folder_io import create_project, read_canvas, sync_details_with_overview, write_canvas
from mashbill.models import CanvasDoc, CategoryNode, FeatureNode, ServiceNode, SketchNode, StepNode
from mashbill.workspace import resolve_plot_root


@pytest.fixture
def plot_root(tmp_path: Path) -> Path:
    return resolve_plot_root(str(tmp_path))


def _overview(feature_labels: dict[str, str]) -> CanvasDoc:
    nodes: list[SketchNode] = [
        CategoryNode(id="default-cat", label="Default"),
        ServiceNode(id="default-svc", parent_id="default-cat", label="Default service"),
    ]
    nodes.extend(
        FeatureNode(id=fid, parent_id="default-svc", label=label)
        for fid, label in feature_labels.items()
    )
    return CanvasDoc(canvas_id="services", canvas_kind="services", nodes=nodes)


def _add_step(plot_root: Path, project_id: str, feature_id: str, step: StepNode) -> None:
    detail = read_canvas(plot_root, project_id, "feature", service_id=feature_id)
    detail.nodes.append(step)
    write_canvas(plot_root, project_id, detail)


def _seed(plot_root: Path) -> None:
    create_project(plot_root, "alpha", "Alpha")
    write_canvas(
        plot_root, "alpha", _overview({"write": "글쓰기", "edit": "글편집", "pay": "결제"})
    )
    sync_details_with_overview(plot_root, "alpha")


def test_usage_lists_features_whose_steps_reference_the_entity(plot_root: Path) -> None:
    _seed(plot_root)
    _add_step(
        plot_root, "alpha", "write", StepNode(id="s1", label="작성", ref_entity_ids=["ent_post"])
    )
    _add_step(
        plot_root, "alpha", "edit", StepNode(id="s2", label="수정", ref_entity_ids=["ent_post"])
    )
    _add_step(
        plot_root, "alpha", "pay", StepNode(id="s3", label="결제", ref_entity_ids=["ent_payment"])
    )

    usage = entity_usage(plot_root, "alpha", "ent_post")
    by_feature = {u["feature_id"]: u for u in usage}
    assert set(by_feature) == {"write", "edit"}
    assert by_feature["write"]["feature_label"] == "글쓰기"
    assert by_feature["write"]["steps"] == ["작성"]


def test_usage_empty_when_unreferenced(plot_root: Path) -> None:
    _seed(plot_root)
    _add_step(
        plot_root, "alpha", "write", StepNode(id="s1", label="작성", ref_entity_ids=["ent_post"])
    )
    assert entity_usage(plot_root, "alpha", "ent_nobody") == []


def test_usage_collects_multiple_steps_in_one_feature(plot_root: Path) -> None:
    _seed(plot_root)
    _add_step(
        plot_root, "alpha", "write", StepNode(id="s1", label="초안", ref_entity_ids=["ent_post"])
    )
    _add_step(
        plot_root, "alpha", "write", StepNode(id="s2", label="발행", ref_entity_ids=["ent_post"])
    )
    usage = entity_usage(plot_root, "alpha", "ent_post")
    assert len(usage) == 1
    assert sorted(usage[0]["steps"]) == ["발행", "초안"]


def test_usage_endpoint_returns_envelope(tmp_path: Path) -> None:
    from starlette.testclient import TestClient

    from mashbill.broadcast import BroadcastHub
    from mashbill.git_store import init_workspace_repo
    from mashbill.http_app import create_http_app

    init_workspace_repo(tmp_path)
    plot_root = resolve_plot_root(str(tmp_path))
    _seed(plot_root)
    _add_step(
        plot_root, "alpha", "write", StepNode(id="s1", label="작성", ref_entity_ids=["ent_post"])
    )

    client = TestClient(create_http_app(hub=BroadcastHub(enable_watchers=False)))
    resp = client.get(
        "/api/projects/alpha/entities/ent_post/usage", params={"project_path": str(tmp_path)}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["entity_id"] == "ent_post"
    assert [u["feature_id"] for u in body["usages"]] == ["write"]
    assert body["usages"][0]["feature_label"] == "글쓰기"
