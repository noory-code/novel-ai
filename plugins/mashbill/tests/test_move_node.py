"""The MCP position write changes only one node's view entry."""

from __future__ import annotations

from pathlib import Path

import pytest

from mashbill import mcp_tools
from mashbill.canvas_view import view_file
from mashbill.models import CanvasKind
from mashbill.storage import _canvas_file, _project_dir
from mashbill.workspace import resolve_plot_root


@pytest.mark.parametrize("canvas_kind", ["services", "feature"])
def test_move_node_writes_only_target_position_to_view(
    tmp_path: Path, canvas_kind: CanvasKind
) -> None:
    ws = str(tmp_path)
    mcp_tools.create_project_tool(ws, "alpha", "Alpha")
    feature = mcp_tools.create_node(ws, "alpha", "services", "feature", {"label": "Feature"})[
        "node"
    ]
    service_id = feature["id"] if canvas_kind == "feature" else None
    if service_id is not None:
        target = mcp_tools.create_node(
            ws, "alpha", "feature", "step", {"label": "Step"}, service_id=service_id
        )["node"]
    else:
        target = feature
    other = mcp_tools.create_node(
        ws,
        "alpha",
        canvas_kind,
        "step" if service_id else "service",
        {"label": "Other"},
        service_id=service_id,
    )["node"]
    before = mcp_tools.get_canvas(ws, "alpha", canvas_kind, service_id)
    path = _canvas_file(resolve_plot_root(ws), "alpha", canvas_kind, service_id)
    canvas_bytes = path.read_bytes()
    view_bytes = view_file(path).read_bytes()

    result = mcp_tools.move_node(ws, "alpha", canvas_kind, target["id"], 123.5, -42.0, service_id)

    assert result == {"node_id": target["id"], "x": 123.5, "y": -42.0}
    assert path.read_bytes() == canvas_bytes
    assert view_file(path).read_bytes() != view_bytes
    after = mcp_tools.get_canvas(ws, "alpha", canvas_kind, service_id)
    before_nodes = {node["id"]: node for node in before["nodes"]}
    after_nodes = {node["id"]: node for node in after["nodes"]}
    assert after_nodes[target["id"]] == {**before_nodes[target["id"]], "x": 123.5, "y": -42.0}
    assert after_nodes[other["id"]] == before_nodes[other["id"]]
    assert after["edges"] == before["edges"]
    assert not (_project_dir(resolve_plot_root(ws), "alpha") / "drafts").exists()


def test_move_node_rejects_unknown_node_nonfinite_and_anchor(tmp_path: Path) -> None:
    ws = str(tmp_path)
    mcp_tools.create_project_tool(ws, "alpha", "Alpha")
    node_id = mcp_tools.create_node(ws, "alpha", "services", "service", {"label": "S"})["node"][
        "id"
    ]
    path = _canvas_file(resolve_plot_root(ws), "alpha", "services")
    before = (path.read_bytes(), view_file(path).read_bytes())

    with pytest.raises(ValueError, match="node not found on services canvas"):
        mcp_tools.move_node(ws, "alpha", "services", "missing", 1.0, 2.0)
    for value in (float("nan"), float("inf"), float("-inf")):
        with pytest.raises(ValueError, match="finite"):
            mcp_tools.move_node(ws, "alpha", "services", node_id, value, 2.0)
        with pytest.raises(ValueError, match="finite"):
            mcp_tools.move_node(ws, "alpha", "services", node_id, 1.0, value)
    with pytest.raises(ValueError, match="project anchor"):
        mcp_tools.move_node(ws, "alpha", "services", "__project_anchor__", 1.0, 2.0)
    with pytest.raises(FileNotFoundError):
        mcp_tools.move_node(ws, "alpha", "feature", node_id, 1.0, 2.0, "missing")
    assert (path.read_bytes(), view_file(path).read_bytes()) == before
