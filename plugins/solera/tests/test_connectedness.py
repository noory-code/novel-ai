"""Starting work stays connected to an imported format F design."""

from pathlib import Path

import pytest

from solera.errors import OrderError
from solera.graph import load_items, reaches_design_node
from solera.planning import create_item
from solera.supervisor import BlockedLeaf, find_next_open, ready_leaves, start_next
from solera.workspace import Workspace


def _workspace(tmp_path: Path) -> Workspace:
    return Workspace(tmp_path / ".noory" / "solera")


def _mark_imported_design(ws: Workspace) -> None:
    """Leave the two manifests that a completed format F import contains."""
    release = ws.spec_dir("auth")
    (release / "service").mkdir(parents=True)
    (release / "project").mkdir()
    (release / "service" / "manifest.json").write_text("{}")
    (release / "project" / "manifest.json").write_text("{}")


def test_reaches_design_node_through_self_or_ancestor(tmp_path: Path) -> None:
    ws = _workspace(tmp_path)
    disconnected_parent = create_item(ws, "story", "Disconnected")
    disconnected = create_item(
        ws, "action", "Disconnected leaf", gate="true", parent=disconnected_parent.id
    )
    connected_parent = create_item(ws, "story", "Connected", realizes=["feature/login"])
    inherited = create_item(ws, "action", "Inherited leaf", gate="true", parent=connected_parent.id)
    direct_parent = create_item(ws, "story", "Direct")
    direct = create_item(
        ws,
        "action",
        "Direct leaf",
        gate="true",
        realizes=["feature/signup"],
        parent=direct_parent.id,
    )

    items = load_items(ws)

    assert reaches_design_node(items, disconnected.id) is False
    assert reaches_design_node(items, inherited.id) is True
    assert reaches_design_node(items, direct.id) is True


def test_imported_design_blocks_only_disconnected_todo_leaves(tmp_path: Path) -> None:
    ws = _workspace(tmp_path)
    _mark_imported_design(ws)
    disconnected_parent = create_item(ws, "story", "Disconnected")
    disconnected = create_item(
        ws, "action", "Disconnected leaf", gate="true", parent=disconnected_parent.id
    )
    connected_parent = create_item(ws, "story", "Connected", realizes=["feature/login"])
    inherited = create_item(ws, "action", "Inherited leaf", gate="true", parent=connected_parent.id)
    direct_parent = create_item(ws, "story", "Direct")
    direct = create_item(
        ws,
        "action",
        "Direct leaf",
        gate="true",
        realizes=["feature/signup"],
        parent=direct_parent.id,
    )

    ready, blocked = ready_leaves(ws)

    assert ready == [inherited.id, direct.id]
    assert blocked == [
        BlockedLeaf(
            leaf_id=disconnected.id,
            waiting_on=(),
            names_no_design_node=True,
        )
    ]
    assert find_next_open(ws) == inherited.id


def test_workspace_without_imported_design_starts_disconnected_leaf(tmp_path: Path) -> None:
    ws = _workspace(tmp_path)
    leaf = create_item(ws, "action", "Standalone", gate="true")

    assert ready_leaves(ws) == ([leaf.id], [])
    assert find_next_open(ws) == leaf.id


def test_incomplete_import_marker_does_not_enable_connectedness_rule(
    tmp_path: Path,
) -> None:
    ws = _workspace(tmp_path)
    service = ws.spec_dir("auth") / "service"
    service.mkdir(parents=True)
    (service / "manifest.json").write_text("{}")
    leaf = create_item(ws, "action", "Standalone", gate="true")

    assert find_next_open(ws) == leaf.id


def test_doing_disconnected_leaf_is_resumed_with_imported_design(tmp_path: Path) -> None:
    ws = _workspace(tmp_path)
    _mark_imported_design(ws)
    leaf = create_item(ws, "action", "Already started", gate="true")
    ws.write_item(leaf.model_copy(update={"status": "doing"}))

    assert start_next(ws) == leaf.id
    assert ws.load_item(leaf.id).status == "doing"


def test_leaf_can_be_blocked_by_order_and_missing_design_node(tmp_path: Path) -> None:
    ws = _workspace(tmp_path)
    _mark_imported_design(ws)
    predecessor = create_item(ws, "story", "Not done")
    leaf = create_item(ws, "action", "Blocked twice", gate="true", after=[predecessor.id])

    assert ready_leaves(ws) == (
        [],
        [
            BlockedLeaf(
                leaf_id=leaf.id,
                waiting_on=(predecessor.id,),
                names_no_design_node=True,
            )
        ],
    )
    with pytest.raises(OrderError) as exc_info:
        start_next(ws)
    message = str(exc_info.value)
    assert f"waits for {predecessor.id}" in message
    assert "leaf" in message
    assert "ancestors" in message
    assert "realize no design slug" in message
    assert "`realizes`" in message
    assert "`feature/login`" in message
