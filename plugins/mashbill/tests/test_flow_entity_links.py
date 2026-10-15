"""A flow draft's steps name the entities they touch, and drawing links them.

In novel-workspace newcomer walk 6 the coach drew 24 steps and none named an
entity, so every entity card read "인터랙션 0개": the draft had no place for
entities and linking each step needed a separate ``set_node_references`` call
(O-00000176). A draft step now carries ``ref_entity_ids``; an id that is no
entity is refused when the draft is recorded and again when it is drawn
(novel-workspace W-00000500, D-2026-10-15-O).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mashbill import mcp_tools
from mashbill.folder_io import create_project, read_canvas, write_canvas
from mashbill.models import CanvasDoc, EntityNode, FeatureNode, SketchEdge, StepNode
from mashbill.workspace import resolve_plot_root


def _project(tmp_path: Path, steps: list[StepNode] | None = None) -> str:
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    write_canvas(
        plot_root,
        "alpha",
        CanvasDoc(
            canvas_id="services",
            canvas_kind="services",
            nodes=[FeatureNode(id="feature_x", label="미용 예약", proposed="예약을 잡는다.")],
        ),
    )
    write_canvas(
        plot_root,
        "alpha",
        CanvasDoc(
            canvas_id="entities",
            canvas_kind="entities",
            nodes=[
                EntityNode(id="entity_booking", label="예약"),
                EntityNode(id="entity_dog", label="강아지"),
            ],
        ),
    )
    write_canvas(
        plot_root,
        "alpha",
        CanvasDoc(
            canvas_id="feature_x",
            canvas_kind="feature",
            feature_ref="feature_x",
            nodes=[FeatureNode(id="feature_x", label="미용 예약"), *(steps or [])],
        ),
    )
    return str(tmp_path)


def _step(**extra: Any) -> dict[str, Any]:
    return {"key": "book", "kind": "step", "label": "예약을 잡는다", "covers": [1], **extra}


def _propose(project_path: str, nodes: list[dict[str, Any]], **more: Any) -> dict[str, Any]:
    edges = [{"source": "feature_x", "target": nodes[0]["key"]}]
    return mcp_tools.propose_flow(
        project_path, "alpha", "feature_x", nodes=nodes, edges=edges, **more
    )


def _feature(project_path: str) -> CanvasDoc:
    return read_canvas(resolve_plot_root(project_path), "alpha", "feature", "feature_x")


def _drawn_step(project_path: str, label: str) -> StepNode:
    node = next(n for n in _feature(project_path).nodes if n.label == label)
    assert isinstance(node, StepNode)
    return node


def test_a_drawn_step_carries_the_entities_its_draft_step_named(tmp_path: Path) -> None:
    project_path = _project(tmp_path)

    _propose(project_path, [_step(ref_entity_ids=["entity_booking", "entity_dog"])])
    mcp_tools.draw_proposed_flow(project_path, "alpha", "feature_x")

    step = _drawn_step(project_path, "예약을 잡는다")
    assert step.ref_entity_ids == ["entity_booking", "entity_dog"]


def test_the_rendering_names_a_steps_entities_by_label(tmp_path: Path) -> None:
    project_path = _project(tmp_path)

    rendered = _propose(project_path, [_step(ref_entity_ids=["entity_booking", "entity_dog"])])[
        "rendered"
    ]

    assert "[1] 예약을 잡는다\n  ⇢ 예약, 강아지" in rendered
    assert "entity_booking" not in rendered


def test_a_step_without_entities_renders_no_link_line(tmp_path: Path) -> None:
    project_path = _project(tmp_path)

    rendered = _propose(project_path, [_step()])["rendered"]

    assert "⇢" not in rendered


def test_an_id_that_is_no_entity_is_refused_naming_the_known_entities(tmp_path: Path) -> None:
    project_path = _project(tmp_path)

    with pytest.raises(ValueError) as refused:
        _propose(project_path, [_step(ref_entity_ids=["entity_cat"])])

    message = str(refused.value)
    assert "entity_cat" in message
    assert "entity_booking (예약)" in message and "entity_dog (강아지)" in message
    assert [n.id for n in _feature(project_path).nodes] == ["feature_x"]


def test_only_a_step_links_entities(tmp_path: Path) -> None:
    project_path = _project(tmp_path)
    nodes = [
        _step(),
        {
            "key": "ok",
            "kind": "decision",
            "label": "자리가 있나?",
            "ref_entity_ids": ["entity_dog"],
        },
    ]

    with pytest.raises(ValueError, match="only a step"):
        mcp_tools.propose_flow(
            project_path,
            "alpha",
            "feature_x",
            nodes=nodes,
            edges=[{"source": "feature_x", "target": "book"}, {"source": "book", "target": "ok"}],
            open_items=[{"at": "ok", "question": "자리가 없으면?"}],
        )


def test_an_entity_removed_after_the_draft_is_refused_at_draw(tmp_path: Path) -> None:
    project_path = _project(tmp_path)
    _propose(project_path, [_step(ref_entity_ids=["entity_dog"])])
    plot_root = resolve_plot_root(project_path)
    write_canvas(
        plot_root,
        "alpha",
        CanvasDoc(
            canvas_id="entities",
            canvas_kind="entities",
            nodes=[EntityNode(id="entity_booking", label="예약")],
        ),
    )

    with pytest.raises(ValueError, match="entity_dog"):
        mcp_tools.draw_proposed_flow(project_path, "alpha", "feature_x")

    assert [n.id for n in _feature(project_path).nodes] == ["feature_x"]


def test_a_proposal_file_kept_before_links_still_draws(tmp_path: Path) -> None:
    project_path = _project(tmp_path)
    _propose(project_path, [_step()])
    (kept,) = resolve_plot_root(project_path).rglob("flow_proposals/feature_x.json")
    raw = json.loads(kept.read_text(encoding="utf-8"))
    for node in raw["current"]["nodes"]:
        node.pop("ref_entity_ids", None)
    kept.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")

    mcp_tools.draw_proposed_flow(project_path, "alpha", "feature_x")

    assert _drawn_step(project_path, "예약을 잡는다").ref_entity_ids == []


def test_a_relabel_links_a_drawn_step_and_replaces_its_entities(tmp_path: Path) -> None:
    drawn = StepNode(id="step_a", label="예약을 잡는다", ref_entity_ids=["entity_dog"])
    project_path = _project(tmp_path, steps=[drawn])
    plot_root = resolve_plot_root(project_path)
    feature = _feature(project_path)
    write_canvas(plot_root, "alpha", feature.model_copy(update={"edges": _feature_line()}))

    rendered = mcp_tools.propose_flow(
        project_path,
        "alpha",
        "feature_x",
        nodes=[],
        relabels=[
            {"node": "step_a", "label": "예약을 잡는다", "ref_entity_ids": ["entity_booking"]}
        ],
        placed=[{"item": 1, "at": "step_a"}],
    )["rendered"]
    mcp_tools.draw_proposed_flow(project_path, "alpha", "feature_x")

    assert "~ 예약을 잡는다 → 예약을 잡는다\n  ⇢ 예약" in rendered
    assert _drawn_step(project_path, "예약을 잡는다").ref_entity_ids == ["entity_booking"]


def test_a_relabel_without_entities_leaves_a_drawn_steps_links(tmp_path: Path) -> None:
    drawn = StepNode(id="step_a", label="예약을 잡는다", ref_entity_ids=["entity_dog"])
    project_path = _project(tmp_path, steps=[drawn])
    plot_root = resolve_plot_root(project_path)
    feature = _feature(project_path)
    write_canvas(plot_root, "alpha", feature.model_copy(update={"edges": _feature_line()}))

    mcp_tools.propose_flow(
        project_path,
        "alpha",
        "feature_x",
        nodes=[],
        relabels=[{"node": "step_a", "label": "예약을 확정한다"}],
        placed=[{"item": 1, "at": "step_a"}],
    )
    mcp_tools.draw_proposed_flow(project_path, "alpha", "feature_x")

    assert _drawn_step(project_path, "예약을 확정한다").ref_entity_ids == ["entity_dog"]


def test_a_relabel_links_only_a_drawn_step(tmp_path: Path) -> None:
    project_path = _project(tmp_path)

    with pytest.raises(ValueError, match="only a step"):
        mcp_tools.propose_flow(
            project_path,
            "alpha",
            "feature_x",
            nodes=[_step()],
            edges=[{"source": "feature_x", "target": "book"}],
            relabels=[
                {"node": "feature_x", "label": "미용 예약", "ref_entity_ids": ["entity_dog"]}
            ],
        )


def _feature_line() -> list[SketchEdge]:
    return [SketchEdge(id="e_root", source="feature_x", target="step_a", directed=True)]


async def test_the_coach_reads_where_a_step_names_its_entities() -> None:
    from mashbill.tool_shapes import tool_shapes

    tools = {tool.name: tool for tool in await mcp_tools.mcp.list_tools()}
    description = tools["propose_flow"].description or ""
    assert '"ref_entity_ids"?: [entity ids]' in description
    assert "only a step" in description
    (shape,) = [line for line in tool_shapes().splitlines() if "propose_flow(" in line]
    assert "covers?:[int], ref_entity_ids?:[str]}" in shape
    assert "relabels?:[{node, label, outcome?, ref_entity_ids?:[str]}]" in shape


def test_the_coach_is_told_to_link_entities_inside_the_flow_draft() -> None:
    """Newcomer walk 6: 0 of 24 drawn steps named an entity. The write rule
    now points a step's data to the draft itself, not only to a later
    set_node_references call."""
    from mashbill.chat_context import WRITE_PLAYBOOK

    assert "a step/feature's data → ref_entity_ids, in a flow draft via propose_flow)" in (
        WRITE_PLAYBOOK
    )
