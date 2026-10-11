"""The feature coach hands a flow draft to the engine and the engine draws exactly it.

propose_flow checks that every line names its target, that notes stay edgeless, and
that every numbered item of the feature description is placed, left open, or
explicitly omitted. draw_proposed_flow then writes only the proposed nodes and lines
in one canvas write (novel-workspace W-00000423).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mashbill import mcp_tools
from mashbill.folder_io import create_project, read_canvas, write_canvas
from mashbill.models import CanvasDoc, FeatureNode
from mashbill.workspace import resolve_plot_root

_DESCRIPTION = (
    "사용자는 흐름을 정한다. "
    "정보가 부족하면 한 가지 더 답하거나 나중에 이어 간다. "
    "그린 선을 고칠 수 있다."
)


def _project(tmp_path: Path, proposed: str = _DESCRIPTION) -> str:
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    write_canvas(
        plot_root,
        "alpha",
        CanvasDoc(
            canvas_id="services",
            canvas_kind="services",
            nodes=[FeatureNode(id="feature_x", label="흐름 그리기", proposed=proposed)],
        ),
    )
    write_canvas(
        plot_root,
        "alpha",
        CanvasDoc(
            canvas_id="feature_x",
            canvas_kind="feature",
            feature_ref="feature_x",
            nodes=[FeatureNode(id="feature_x", label="흐름 그리기")],
        ),
    )
    return str(tmp_path)


def _canvas(project_path: str) -> CanvasDoc:
    return read_canvas(resolve_plot_root(project_path), "alpha", "feature", "feature_x")


def _nodes() -> list[dict[str, Any]]:
    return [
        {"key": "1", "kind": "step", "label": "흐름을 정한다", "covers": [1]},
        {"key": "2", "kind": "decision", "label": "정보가 충분한가?", "covers": [2]},
        {"key": "3", "kind": "step", "label": "한 가지 더 답한다"},
        {"key": "4", "kind": "step", "label": "나중에 이어 간다"},
        {"key": "5", "kind": "step", "label": "선을 고친다", "covers": [3]},
        {"key": "r1", "kind": "rule", "label": "액터는 읽기 전용이다"},
        {"key": "n1", "kind": "note", "label": "세부로 내려가면 되돌린다"},
    ]


def _edges() -> list[dict[str, Any]]:
    return [
        {"source": "feature_x", "target": "1"},
        {"source": "1", "target": "2"},
        {"source": "2", "target": "3", "label": "부족하다"},
        {"source": "3", "target": "2"},
        {"source": "2", "target": "4", "label": "나중에"},
        {"source": "2", "target": "5", "label": "충분하다"},
    ]


def _propose(project_path: str, **overrides: Any) -> dict[str, Any]:
    args: dict[str, Any] = {
        "nodes": _nodes(),
        "edges": _edges(),
        "open_items": [{"at": "4", "question": "돌아오면 무엇이 남는지"}],
    }
    args.update(overrides)
    return mcp_tools.propose_flow(project_path, "alpha", "feature_x", **args)


def test_propose_returns_a_rendering_of_every_node_line_and_open_item(tmp_path: Path) -> None:
    project_path = _project(tmp_path)

    rendered = _propose(project_path)["rendered"]

    for text in ("흐름을 정한다", "◇ 정보가 충분한가?", "한 가지 더 답한다", "선을 고친다"):
        assert text in rendered
    assert "→ [3] 한 가지 더 답한다 (부족하다)" in rendered
    assert "→ [2] 정보가 충분한가?" in rendered
    assert "… 돌아오면 무엇이 남는지" in rendered
    assert "액터는 읽기 전용이다" in rendered and "세부로 내려가면 되돌린다" in rendered
    # Proposing draws nothing.
    assert [node.id for node in _canvas(project_path).nodes] == ["feature_x"]


def test_propose_rejects_a_line_to_an_unknown_target(tmp_path: Path) -> None:
    project_path = _project(tmp_path)
    edges = [*_edges(), {"source": "3", "target": "하던 단계"}]

    with pytest.raises(ValueError, match="하던 단계"):
        _propose(project_path, edges=edges)


def test_propose_rejects_a_line_touching_a_note(tmp_path: Path) -> None:
    project_path = _project(tmp_path)
    edges = [*_edges(), {"source": "1", "target": "n1"}]

    with pytest.raises(ValueError, match="note"):
        _propose(project_path, edges=edges)


def test_propose_rejects_an_open_item_without_a_known_step(tmp_path: Path) -> None:
    project_path = _project(tmp_path)

    with pytest.raises(ValueError, match="nowhere"):
        _propose(project_path, open_items=[{"at": "nowhere", "question": "무엇이 남나"}])


def test_propose_rejects_keys_that_repeat_or_reuse_a_canvas_id(tmp_path: Path) -> None:
    project_path = _project(tmp_path)

    with pytest.raises(ValueError, match="'1'"):
        _propose(project_path, nodes=[*_nodes(), {"key": "1", "kind": "step", "label": "x"}])
    with pytest.raises(ValueError, match="feature_x"):
        _propose(
            project_path, nodes=[*_nodes(), {"key": "feature_x", "kind": "step", "label": "x"}]
        )


def test_propose_names_description_items_left_unplaced(tmp_path: Path) -> None:
    project_path = _project(tmp_path)
    nodes = [{**node, "covers": []} if node["key"] == "2" else node for node in _nodes()]

    with pytest.raises(ValueError) as raised:
        _propose(project_path, nodes=nodes)

    message = str(raised.value)
    assert "2." in message and "나중에 이어 간다" in message
    assert "1." not in message.split("\n", 1)[-1]


def test_an_open_item_or_a_stated_omission_accounts_for_a_description_item(
    tmp_path: Path,
) -> None:
    project_path = _project(tmp_path)
    nodes = [{**node, "covers": []} if node["key"] in {"2", "5"} else node for node in _nodes()]

    rendered = _propose(
        project_path,
        nodes=nodes,
        open_items=[{"at": "1", "question": "정보가 부족하면 어디로 가나", "covers": [2]}],
        omitted=[{"item": 3, "reason": "사람이 따로 된 기능으로 빼기로 했다"}],
    )["rendered"]

    assert "3. 그린 선을 고칠 수 있다." in rendered
    assert "사람이 따로 된 기능으로 빼기로 했다" in rendered


def test_draw_writes_exactly_the_proposed_nodes_and_lines(tmp_path: Path) -> None:
    project_path = _project(tmp_path)
    _propose(project_path)

    result = mcp_tools.draw_proposed_flow(project_path, "alpha", "feature_x")

    canvas = _canvas(project_path)
    ids = result["node_ids"]
    labels = {node.id: node.label for node in canvas.nodes}
    assert sorted(labels.values()) == sorted(["흐름 그리기", *(n["label"] for n in _nodes())])
    drawn = {(labels[e.source], labels[e.target], e.label) for e in canvas.edges}
    expected = {
        (
            labels.get(ids.get(e["source"], e["source"])),
            labels[ids[e["target"]]],
            e.get("label", ""),
        )
        for e in _edges()
    }
    assert drawn == expected
    # The open item's step stays unjoined; the rule and note have no lines.
    for key in ("4", "r1", "n1"):
        assert not any(e.source == ids[key] for e in canvas.edges)
    assert not any(ids["r1"] in (e.source, e.target) for e in canvas.edges)
    assert result["open_items"] == [
        {"at": "나중에 이어 간다", "question": "돌아오면 무엇이 남는지"}
    ]


def test_draw_refuses_without_a_proposal_and_refuses_to_draw_twice(tmp_path: Path) -> None:
    project_path = _project(tmp_path)

    with pytest.raises(ValueError, match="propose_flow"):
        mcp_tools.draw_proposed_flow(project_path, "alpha", "feature_x")

    _propose(project_path)
    mcp_tools.draw_proposed_flow(project_path, "alpha", "feature_x")
    with pytest.raises(ValueError, match="already drawn"):
        mcp_tools.draw_proposed_flow(project_path, "alpha", "feature_x")
    assert len(_canvas(project_path).nodes) == 1 + len(_nodes())


def test_a_later_proposal_extends_the_drawn_flow(tmp_path: Path) -> None:
    project_path = _project(tmp_path)
    _propose(project_path)
    first = mcp_tools.draw_proposed_flow(project_path, "alpha", "feature_x")["node_ids"]

    # Items drawn before need no cover; existing node ids are valid endpoints.
    mcp_tools.propose_flow(
        project_path,
        "alpha",
        "feature_x",
        nodes=[{"key": "6", "kind": "step", "label": "무엇이 남는지 본다"}],
        edges=[{"source": first["4"], "target": "6"}],
    )
    mcp_tools.draw_proposed_flow(project_path, "alpha", "feature_x")

    canvas = _canvas(project_path)
    six = next(node.id for node in canvas.nodes if node.label == "무엇이 남는지 본다")
    assert any(e.source == first["4"] and e.target == six for e in canvas.edges)


def test_a_new_proposal_replaces_one_not_yet_drawn(tmp_path: Path) -> None:
    project_path = _project(tmp_path)
    _propose(project_path)
    nodes = [
        {**node, "label": "흐름을 고른다"} if node["key"] == "1" else node for node in _nodes()
    ]
    _propose(project_path, nodes=nodes)

    mcp_tools.draw_proposed_flow(project_path, "alpha", "feature_x")

    labels = {node.label for node in _canvas(project_path).nodes}
    assert "흐름을 고른다" in labels and "흐름을 정한다" not in labels


def test_a_feature_without_a_description_needs_no_cover(tmp_path: Path) -> None:
    project_path = _project(tmp_path, proposed="")
    nodes = [{key: value for key, value in node.items() if key != "covers"} for node in _nodes()]

    assert "rendered" in _propose(project_path, nodes=nodes)


def test_both_tools_log_identifiers_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    log = tmp_path / "tools.jsonl"
    monkeypatch.setenv("MASHBILL_TOOL_LOG", str(log))
    project_path = _project(tmp_path)

    _propose(project_path)
    mcp_tools.draw_proposed_flow(project_path, "alpha", "feature_x")

    lines = [json.loads(line) for line in log.read_text().splitlines()]
    assert [line["tool"] for line in lines] == ["propose_flow", "draw_proposed_flow"]
    assert all(line["service_id"] == "feature_x" for line in lines)
    assert all("흐름을 정한다" not in json.dumps(line, ensure_ascii=False) for line in lines)
    assert len(lines[1]["node_ids"]) == len(_nodes())
