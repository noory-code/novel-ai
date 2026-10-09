"""Coach design-check state and automatic recheck transitions."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from mashbill import mcp_tools
from mashbill.broadcast import BroadcastHub
from mashbill.folder_io import (
    create_project,
    read_canvas,
    sync_details_with_overview,
    write_canvas,
)
from mashbill.http_app import create_http_app
from mashbill.models import (
    CanvasDoc,
    CategoryNode,
    DesignCheck,
    DesignCheckState,
    FeatureNode,
    ServiceNode,
    SketchEdge,
    StepNode,
)
from mashbill.storage import _canvas_file
from mashbill.workspace import resolve_plot_root


def _node(plot_root: Path, node_id: str) -> ServiceNode | FeatureNode:
    overview = read_canvas(plot_root, "alpha", "services")
    node = next(node for node in overview.nodes if node.id == node_id)
    assert isinstance(node, (ServiceNode, FeatureNode))
    return node


def _check(plot_root: Path, node_id: str) -> DesignCheck:
    check = _node(plot_root, node_id).design_check
    assert check is not None
    return check


def _setup_design(tmp_path: Path, *, with_detail_flow: bool = False) -> Path:
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    overview = CanvasDoc(
        canvas_id="services",
        canvas_kind="services",
        nodes=[
            ServiceNode(id="svc", label="Write together"),
            FeatureNode(id="feat", label="Draft"),
        ],
        edges=[SketchEdge(id="contains", source="svc", target="feat")],
    )
    write_canvas(plot_root, "alpha", overview)
    sync_details_with_overview(plot_root, "alpha")
    if with_detail_flow:
        detail = read_canvas(plot_root, "alpha", "feature", "feat")
        step = StepNode(id="step", label="Type")
        detail = CanvasDoc.model_validate(
            detail.model_copy(
                update={
                    "nodes": [*detail.nodes, step],
                    "edges": [SketchEdge(id="flow", source="feat", target="step")],
                }
            ).model_dump(by_alias=True)
        )
        write_canvas(plot_root, "alpha", detail)
    mcp_tools.set_design_check(str(tmp_path), "alpha", "svc", "checked", 2, 0)
    mcp_tools.set_design_check(str(tmp_path), "alpha", "feat", "checked", 3, 0)
    return plot_root


def _assert_recheck(plot_root: Path, *, service: bool = True, feature: bool = False) -> None:
    assert _check(plot_root, "svc").state == ("recheck" if service else "checked")
    assert _check(plot_root, "feat").state == ("recheck" if feature else "checked")


def test_design_check_round_trips_on_service_and_feature() -> None:
    check = DesignCheck(
        state="checked",
        found=4,
        remaining=1,
        updated_at="2026-10-05T12:34:56+00:00",
    )
    for node in (
        ServiceNode(id="svc", design_check=check),
        FeatureNode(id="feat", design_check=check),
    ):
        parsed = type(node).model_validate(node.model_dump())
        assert parsed.design_check == check
        assert parsed.model_dump()["design_check"] == {
            "state": "checked",
            "found": 4,
            "remaining": 1,
            "updated_at": "2026-10-05T12:34:56+00:00",
        }


@pytest.mark.parametrize("state", ["unchecked", "checking", "checked", "recheck"])
def test_design_check_accepts_exactly_the_four_states(state: DesignCheckState) -> None:
    check = DesignCheck(state=state, updated_at="2026-10-05T12:34:56+00:00")
    assert check.state == state


def test_old_canvas_without_design_check_loads_without_rewriting(tmp_path: Path) -> None:
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    path = _canvas_file(plot_root, "alpha", "services")
    path.write_text(
        """{
  "canvas_id": "services",
  "canvas_kind": "services",
  "nodes": [{"id": "svc", "kind": "service", "label": "Legacy"}],
  "edges": []
}""",
        encoding="utf-8",
    )
    before = path.read_bytes()

    loaded = read_canvas(plot_root, "alpha", "services")

    node = loaded.nodes[0]
    assert isinstance(node, ServiceNode)
    assert node.design_check is None
    assert path.read_bytes() == before


def test_set_design_check_sets_engine_timestamp_and_no_other_node_field(tmp_path: Path) -> None:
    plot_root = _setup_design(tmp_path)
    before = _node(plot_root, "svc").model_dump()

    out = mcp_tools.set_design_check(
        str(tmp_path), "alpha", "svc", "checking", found=5, remaining=2
    )

    after = _node(plot_root, "svc").model_dump(by_alias=True)
    assert out["node"] == after
    check = after.pop("design_check")
    before.pop("design_check")
    before["_publish_baseline"] = before.pop("publish_baseline")
    assert after == before
    assert check["state"] == "checking"
    assert check["found"] == 5
    assert check["remaining"] == 2
    assert datetime.fromisoformat(check["updated_at"]).tzinfo is not None


def test_set_design_check_rejects_non_service_or_feature_node(tmp_path: Path) -> None:
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    overview = read_canvas(plot_root, "alpha", "services")
    write_canvas(
        plot_root,
        "alpha",
        overview.model_copy(update={"nodes": [CategoryNode(id="cat", label="Group")]}),
    )
    with pytest.raises(ValueError, match="only supports service and feature"):
        mcp_tools.set_design_check(str(tmp_path), "alpha", "cat", "checking")


def test_set_design_check_does_not_reopen_itself(tmp_path: Path) -> None:
    plot_root = _setup_design(tmp_path)

    mcp_tools.set_design_check(str(tmp_path), "alpha", "svc", "checked", 7, 1)

    check = _check(plot_root, "svc")
    assert check.state == "checked"
    assert check.found == 7
    assert check.remaining == 1


def test_set_design_check_syncs_feature_overview_and_detail(tmp_path: Path) -> None:
    plot_root = _setup_design(tmp_path)

    mcp_tools.set_design_check(str(tmp_path), "alpha", "feat", "checking")

    assert _check(plot_root, "feat").state == "checking"
    detail = read_canvas(plot_root, "alpha", "feature", "feat")
    root = next(node for node in detail.nodes if node.id == "feat")
    assert isinstance(root, FeatureNode)
    assert root.design_check is not None
    assert root.design_check.state == "checking"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("label", "Renamed service"),
        ("problem", "A new problem"),
        ("value_created", "A new value"),
        ("ref_actor_ids", ["actor-2"]),
        ("ref_value_ids", ["value-2"]),
        ("ref_identity_ids", ["identity-2"]),
    ],
)
def test_service_content_change_reopens_service_check(
    tmp_path: Path, field: str, value: object
) -> None:
    plot_root = _setup_design(tmp_path)
    overview = read_canvas(plot_root, "alpha", "services")
    nodes = [
        node.model_copy(update={field: value}) if node.id == "svc" else node
        for node in overview.nodes
    ]

    write_canvas(plot_root, "alpha", overview.model_copy(update={"nodes": nodes}))

    _assert_recheck(plot_root)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("label", "Renamed feature"),
        ("proposed", "A different capability"),
        ("ref_actor_ids", ["actor-2"]),
    ],
)
def test_feature_content_change_reopens_feature_and_service_checks(
    tmp_path: Path, field: str, value: object
) -> None:
    plot_root = _setup_design(tmp_path)
    overview = read_canvas(plot_root, "alpha", "services")
    nodes = [
        node.model_copy(update={field: value}) if node.id == "feat" else node
        for node in overview.nodes
    ]

    write_canvas(plot_root, "alpha", overview.model_copy(update={"nodes": nodes}))

    _assert_recheck(plot_root, feature=True)


@pytest.mark.parametrize(
    ("source", "target", "service_rechecks"),
    [("svc", "feat", True), ("feat", "svc", False)],
)
def test_feature_change_only_reopens_service_for_outgoing_membership(
    tmp_path: Path, source: str, target: str, service_rechecks: bool
) -> None:
    plot_root = _setup_design(tmp_path)
    overview = read_canvas(plot_root, "alpha", "services")
    write_canvas(
        plot_root,
        "alpha",
        overview.model_copy(
            update={"edges": [SketchEdge(id="contains", source=source, target=target)]}
        ),
    )
    mcp_tools.set_design_check(str(tmp_path), "alpha", "svc", "checked", 2, 0)
    overview = read_canvas(plot_root, "alpha", "services")
    nodes = [
        node.model_copy(update={"proposed": "A different capability"})
        if node.id == "feat"
        else node
        for node in overview.nodes
    ]

    write_canvas(plot_root, "alpha", overview.model_copy(update={"nodes": nodes}))

    _assert_recheck(plot_root, service=service_rechecks, feature=True)


def test_feature_attachment_reopens_service_check(tmp_path: Path) -> None:
    plot_root = _setup_design(tmp_path)
    overview = read_canvas(plot_root, "alpha", "services")
    detached = overview.model_copy(
        update={"edges": [edge for edge in overview.edges if edge.id != "contains"]}
    )
    write_canvas(plot_root, "alpha", detached)
    mcp_tools.set_design_check(str(tmp_path), "alpha", "svc", "checked", 2, 0)

    write_canvas(plot_root, "alpha", overview)

    _assert_recheck(plot_root)


def test_feature_detachment_reopens_service_check(tmp_path: Path) -> None:
    plot_root = _setup_design(tmp_path)
    overview = read_canvas(plot_root, "alpha", "services")

    write_canvas(
        plot_root,
        "alpha",
        overview.model_copy(
            update={"edges": [edge for edge in overview.edges if edge.id != "contains"]}
        ),
    )

    _assert_recheck(plot_root)


def test_feature_addition_reopens_its_service_check(tmp_path: Path) -> None:
    plot_root = _setup_design(tmp_path)
    overview = read_canvas(plot_root, "alpha", "services")

    write_canvas(
        plot_root,
        "alpha",
        overview.model_copy(
            update={
                "nodes": [*overview.nodes, FeatureNode(id="feat-2", label="Review")],
                "edges": [
                    *overview.edges,
                    SketchEdge(id="contains-2", source="svc", target="feat-2"),
                ],
            }
        ),
    )

    _assert_recheck(plot_root)


def test_feature_removal_reopens_its_service_check(tmp_path: Path) -> None:
    plot_root = _setup_design(tmp_path)
    overview = read_canvas(plot_root, "alpha", "services")

    write_canvas(
        plot_root,
        "alpha",
        overview.model_copy(
            update={
                "nodes": [node for node in overview.nodes if node.id != "feat"],
                "edges": [
                    edge
                    for edge in overview.edges
                    if edge.source != "feat" and edge.target != "feat"
                ],
            }
        ),
    )

    assert _check(plot_root, "svc").state == "recheck"


@pytest.mark.parametrize(
    "mutation",
    ["node_create", "node_update", "node_delete", "edge_create", "edge_update", "edge_delete"],
)
def test_any_feature_detail_mutation_reopens_feature_and_service_checks(
    tmp_path: Path, mutation: str
) -> None:
    plot_root = _setup_design(tmp_path, with_detail_flow=True)
    detail = read_canvas(plot_root, "alpha", "feature", "feat")
    if mutation == "node_create":
        detail = detail.model_copy(
            update={"nodes": [*detail.nodes, StepNode(id="step-2", label="Review")]}
        )
    elif mutation == "node_update":
        detail = detail.model_copy(
            update={
                "nodes": [
                    node.model_copy(update={"x": node.x + 1}) if node.id == "step" else node
                    for node in detail.nodes
                ]
            }
        )
    elif mutation == "node_delete":
        detail = detail.model_copy(
            update={
                "nodes": [node for node in detail.nodes if node.id != "step"],
                "edges": [],
            }
        )
    elif mutation == "edge_create":
        detail = detail.model_copy(
            update={
                "nodes": [*detail.nodes, StepNode(id="step-2", label="Review")],
                "edges": [
                    *detail.edges,
                    SketchEdge(id="flow-2", source="step", target="step-2"),
                ],
            }
        )
    elif mutation == "edge_update":
        detail = detail.model_copy(
            update={
                "edges": [
                    edge.model_copy(update={"label": "then"}) if edge.id == "flow" else edge
                    for edge in detail.edges
                ]
            }
        )
    else:
        detail = detail.model_copy(update={"edges": []})

    write_canvas(plot_root, "alpha", CanvasDoc.model_validate(detail.model_dump(by_alias=True)))

    _assert_recheck(plot_root, feature=True)
    detail_after = read_canvas(plot_root, "alpha", "feature", "feat")
    root = next(node for node in detail_after.nodes if node.id == "feat")
    assert isinstance(root, FeatureNode)
    assert root.design_check is not None
    assert root.design_check.state == "recheck"


def test_feature_detail_change_does_not_reopen_reverse_edge_service_check(
    tmp_path: Path,
) -> None:
    plot_root = _setup_design(tmp_path, with_detail_flow=True)
    overview = read_canvas(plot_root, "alpha", "services")
    write_canvas(
        plot_root,
        "alpha",
        overview.model_copy(
            update={"edges": [SketchEdge(id="contains", source="feat", target="svc")]}
        ),
    )
    mcp_tools.set_design_check(str(tmp_path), "alpha", "svc", "checked", 2, 0)
    detail = read_canvas(plot_root, "alpha", "feature", "feat")
    nodes = [
        node.model_copy(update={"label": "Changed step"}) if node.id == "step" else node
        for node in detail.nodes
    ]

    write_canvas(plot_root, "alpha", detail.model_copy(update={"nodes": nodes}))

    _assert_recheck(plot_root, service=False, feature=True)


def test_unchecked_checks_stay_unchecked_when_upstream_changes(tmp_path: Path) -> None:
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    overview = CanvasDoc(
        canvas_id="services",
        canvas_kind="services",
        nodes=[ServiceNode(id="svc"), FeatureNode(id="feat")],
        edges=[SketchEdge(id="contains", source="svc", target="feat")],
    )
    write_canvas(plot_root, "alpha", overview)
    sync_details_with_overview(plot_root, "alpha")

    renamed = overview.model_copy(
        update={
            "nodes": [
                node.model_copy(update={"label": "Changed"}) if node.id == "feat" else node
                for node in overview.nodes
            ]
        }
    )
    write_canvas(plot_root, "alpha", renamed)
    detail = read_canvas(plot_root, "alpha", "feature", "feat")
    write_canvas(
        plot_root,
        "alpha",
        detail.model_copy(update={"nodes": [*detail.nodes, StepNode(id="step")]}),
    )

    assert _node(plot_root, "svc").design_check is None
    assert _node(plot_root, "feat").design_check is None


def test_services_visual_only_change_does_not_reopen_checks(tmp_path: Path) -> None:
    plot_root = _setup_design(tmp_path)
    overview = read_canvas(plot_root, "alpha", "services")
    moved = overview.model_copy(
        update={
            "nodes": [
                node.model_copy(update={"x": node.x + 10}) if node.id == "svc" else node
                for node in overview.nodes
            ]
        }
    )

    write_canvas(plot_root, "alpha", moved)

    _assert_recheck(plot_root, service=False)


@pytest.mark.parametrize("state", ["unchecked", "recheck"])
def test_unchecked_and_recheck_states_do_not_transition_again(
    tmp_path: Path, state: DesignCheckState
) -> None:
    plot_root = _setup_design(tmp_path)
    mcp_tools.set_design_check(str(tmp_path), "alpha", "svc", state)
    before = _check(plot_root, "svc")
    overview = read_canvas(plot_root, "alpha", "services")
    changed = overview.model_copy(
        update={
            "nodes": [
                node.model_copy(update={"problem": "Changed"}) if node.id == "svc" else node
                for node in overview.nodes
            ]
        }
    )

    write_canvas(plot_root, "alpha", changed)

    assert _check(plot_root, "svc") == before


def test_recheck_keeps_last_check_counts(tmp_path: Path) -> None:
    plot_root = _setup_design(tmp_path)
    before = _check(plot_root, "svc")
    overview = read_canvas(plot_root, "alpha", "services")
    changed = overview.model_copy(
        update={
            "nodes": [
                node.model_copy(update={"problem": "Changed"}) if node.id == "svc" else node
                for node in overview.nodes
            ]
        }
    )

    write_canvas(plot_root, "alpha", changed)

    after = _check(plot_root, "svc")
    assert (after.found, after.remaining) == (before.found, before.remaining)
    assert after.updated_at != before.updated_at


def test_checking_state_transitions_to_recheck(tmp_path: Path) -> None:
    plot_root = _setup_design(tmp_path)
    mcp_tools.set_design_check(str(tmp_path), "alpha", "svc", "checking", 1, 1)
    overview = read_canvas(plot_root, "alpha", "services")
    changed = overview.model_copy(
        update={
            "nodes": [
                node.model_copy(update={"value_created": "Changed"}) if node.id == "svc" else node
                for node in overview.nodes
            ]
        }
    )

    write_canvas(plot_root, "alpha", changed)

    assert _check(plot_root, "svc").state == "recheck"


def test_mcp_node_writer_goes_through_recheck_boundary(tmp_path: Path) -> None:
    plot_root = _setup_design(tmp_path)

    mcp_tools.update_node(str(tmp_path), "alpha", "services", "feat", {"proposed": "Reframed"})

    _assert_recheck(plot_root, feature=True)


def test_http_canvas_writer_goes_through_recheck_boundary(tmp_path: Path) -> None:
    plot_root = _setup_design(tmp_path)
    overview = read_canvas(plot_root, "alpha", "services").model_dump(by_alias=True)
    for node in overview["nodes"]:
        node.pop("design_check", None)  # old viewer does not know the additive field
        if node["id"] == "svc":
            node["problem"] = "Changed through HTTP"
    client = TestClient(create_http_app(hub=BroadcastHub(enable_watchers=False)))

    response = client.put(
        "/api/projects/alpha/canvases/services",
        params={"project_path": str(tmp_path)},
        json=overview,
    )

    assert response.status_code == 200, response.text
    assert _check(plot_root, "svc").state == "recheck"


def test_old_client_omission_preserves_check_when_content_is_unchanged(tmp_path: Path) -> None:
    plot_root = _setup_design(tmp_path)
    overview = read_canvas(plot_root, "alpha", "services")
    raw = overview.model_dump(by_alias=True)
    for node in raw["nodes"]:
        node.pop("design_check", None)

    write_canvas(plot_root, "alpha", CanvasDoc.model_validate(raw))

    _assert_recheck(plot_root, service=False)
