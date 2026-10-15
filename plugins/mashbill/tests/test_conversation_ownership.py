"""A feature's flow and check belong to that feature's conversation (W-00000489).

In newcomer walk 4 the entities coach created a one-step "flow" named after the
feature on eight feature canvases (12:30:12) and then closed the '형제 할인'
feature's failure check from the entities conversation (12:30:48, 12:31:25).
An in-app coach turn's MCP server carries its conversation scope in
``MASHBILL_CHAT_SCOPE``; an external agent's server has none and stays
unrestricted.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from mashbill import mcp_tools
from mashbill.folder_io import create_project, read_canvas, write_canvas
from mashbill.models import CanvasDoc, EntityNode, FeatureNode, ServiceNode, SketchEdge
from mashbill.workspace import resolve_plot_root

_SCOPE = "MASHBILL_CHAT_SCOPE"
_SERVICE = "service_207e695a"
_FEATURE = "feature_1f5f654d"
_SIBLING = "feature_68cdcb85"
_ENTITY = "entity_student"


def _project(tmp_path: Path) -> str:
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    write_canvas(
        plot_root,
        "alpha",
        CanvasDoc(
            canvas_id="services",
            canvas_kind="services",
            nodes=[
                ServiceNode(id=_SERVICE, label="반 관리"),
                FeatureNode(
                    id=_FEATURE, label="학생 반 배정하기", proposed="원장만 학생을 반에 배정한다."
                ),
                FeatureNode(
                    id=_SIBLING,
                    label="형제 할인을 적용해 수강료 정하기",
                    proposed="원장이 학생별 수강료를 정한다.",
                ),
            ],
            edges=[
                SketchEdge(id="e1", source=_SERVICE, target=_FEATURE),
                SketchEdge(id="e2", source=_SERVICE, target=_SIBLING),
            ],
        ),
    )
    for feature_id, label in ((_FEATURE, "학생 반 배정하기"), (_SIBLING, "형제 할인")):
        write_canvas(
            plot_root,
            "alpha",
            CanvasDoc(
                canvas_id=feature_id,
                canvas_kind="feature",
                feature_ref=feature_id,
                nodes=[FeatureNode(id=feature_id, label=label)],
            ),
        )
    write_canvas(
        plot_root,
        "alpha",
        CanvasDoc(
            canvas_id="entities",
            canvas_kind="entities",
            nodes=[EntityNode(id=_ENTITY, label="학생")],
        ),
    )
    return str(tmp_path)


def _feature(project_path: str, feature_id: str = _FEATURE) -> CanvasDoc:
    return read_canvas(resolve_plot_root(project_path), "alpha", "feature", feature_id)


def _placeholder_step(project_path: str, feature_id: str = _FEATURE) -> dict[str, Any]:
    """The 12:30:12 call: a step named after the feature, its description as body."""
    result: dict[str, Any] = mcp_tools.create_node(
        project_path,
        "alpha",
        "feature",
        "step",
        {"label": "학생 반 배정하기", "body": "원장만 학생을 반에 배정한다."},
        service_id=feature_id,
        near=feature_id,
    )
    return result


def _draw_flow(project_path: str, feature_id: str = _FEATURE) -> dict[str, str]:
    mcp_tools.propose_flow(
        project_path,
        "alpha",
        feature_id,
        nodes=[{"key": "assign", "kind": "step", "label": "원장이 학생을 반에 배정한다"}],
        edges=[{"source": feature_id, "target": "assign"}],
        omitted=[{"item": 1, "reason": "시험용"}],
    )
    ids: dict[str, str] = mcp_tools.draw_proposed_flow(project_path, "alpha", feature_id)[
        "node_ids"
    ]
    return ids


# --- feature flows ---------------------------------------------------------


def test_another_conversation_cannot_create_a_step_on_a_feature_canvas(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_path = _project(tmp_path)
    before = _feature(project_path)
    monkeypatch.setenv(_SCOPE, "entities")

    with pytest.raises(ValueError, match="open that feature's canvas") as refused:
        _placeholder_step(project_path)

    assert _FEATURE in str(refused.value)
    assert _feature(project_path) == before


def test_another_conversation_cannot_create_a_decision_or_a_line_there(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_path = _project(tmp_path)
    monkeypatch.setenv(_SCOPE, f"feature:{_FEATURE}")
    step = _draw_flow(project_path)["assign"]
    before = _feature(project_path)
    monkeypatch.setenv(_SCOPE, "entities")

    with pytest.raises(ValueError, match="open that feature's canvas"):
        mcp_tools.create_node(
            project_path,
            "alpha",
            "feature",
            "decision",
            {"label": "배정할 반이 있나요?"},
            service_id=_FEATURE,
        )
    with pytest.raises(ValueError, match="open that feature's canvas"):
        mcp_tools.create_edge(
            project_path, "alpha", "feature", _FEATURE, step, service_id=_FEATURE, label="行う"
        )
    assert _feature(project_path) == before


def test_another_conversation_cannot_propose_or_draw_a_feature_flow(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_path = _project(tmp_path)
    monkeypatch.setenv(_SCOPE, f"feature:{_FEATURE}")
    step = _draw_flow(project_path)["assign"]
    monkeypatch.setenv(_SCOPE, "entities")

    # The 12:30:43 edge swap: no nodes, a line relabelled through the draft.
    with pytest.raises(ValueError, match="open that feature's canvas"):
        mcp_tools.propose_flow(
            project_path,
            "alpha",
            _FEATURE,
            nodes=[],
            placed=[{"item": 1, "at": step}],
            remove_edges=[{"source": _FEATURE, "target": step}],
            edges=[{"source": _FEATURE, "target": step, "label": "진행한다"}],
        )

    # A draft kept in the feature's conversation is drawn only there.
    monkeypatch.setenv(_SCOPE, f"feature:{_FEATURE}")
    mcp_tools.propose_flow(
        project_path,
        "alpha",
        _FEATURE,
        nodes=[{"key": "done", "kind": "step", "label": "반 명단에 학생이 보인다"}],
        edges=[{"source": step, "target": "done"}],
    )
    before = _feature(project_path)
    monkeypatch.setenv(_SCOPE, "entities")
    with pytest.raises(ValueError, match="open that feature's canvas"):
        mcp_tools.draw_proposed_flow(project_path, "alpha", _FEATURE)
    assert _feature(project_path) == before


def test_another_conversation_cannot_rewrite_a_feature_flow_whole(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_path = _project(tmp_path)
    canvas = _feature(project_path).model_dump(by_alias=True)
    canvas["nodes"].append({"id": "step_new", "kind": "step", "label": "학생 반 배정하기"})
    monkeypatch.setenv(_SCOPE, "entities")

    with pytest.raises(ValueError, match="open that feature's canvas"):
        mcp_tools.update_canvas(project_path, "alpha", canvas)
    assert [node.id for node in _feature(project_path).nodes] == [_FEATURE]


def test_a_feature_conversation_cannot_draw_another_features_flow(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_path = _project(tmp_path)
    monkeypatch.setenv(_SCOPE, f"feature:{_SIBLING}")

    with pytest.raises(ValueError, match="open that feature's canvas"):
        _placeholder_step(project_path)


def test_the_features_own_conversation_and_an_outside_agent_draw_its_flow(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_path = _project(tmp_path)
    monkeypatch.setenv(_SCOPE, f"feature:{_FEATURE}")
    _draw_flow(project_path)
    step = _placeholder_step(project_path)["node"]["id"]
    mcp_tools.create_edge(project_path, "alpha", "feature", _FEATURE, step, service_id=_FEATURE)

    monkeypatch.delenv(_SCOPE)
    _draw_flow(project_path, _SIBLING)
    _placeholder_step(project_path, _SIBLING)

    assert len(_feature(project_path).nodes) == 3
    assert len(_feature(project_path, _SIBLING).nodes) == 3


def test_another_conversation_still_links_entities_and_edits_a_drawn_steps_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The person asked the entities coach to link entities to steps (12:29:42),
    and to keep earlier sends (12:31:03): both reach existing steps, not the flow."""
    project_path = _project(tmp_path)
    monkeypatch.setenv(_SCOPE, f"feature:{_FEATURE}")
    step = _draw_flow(project_path)["assign"]
    monkeypatch.setenv(_SCOPE, "entities")

    mcp_tools.set_node_references(
        project_path,
        "alpha",
        "feature",
        step,
        {"ref_entity_ids": [_ENTITY]},
        service_id=_FEATURE,
    )
    mcp_tools.update_node(
        project_path,
        "alpha",
        "feature",
        step,
        {"body": "이전 배정 내역도 남긴다."},
        service_id=_FEATURE,
    )

    node = next(n for n in _feature(project_path).nodes if n.id == step)
    assert node.model_dump()["ref_entity_ids"] == [_ENTITY]
    assert node.model_dump()["body"] == "이전 배정 내역도 남긴다."


# --- design checks ---------------------------------------------------------


def _check_state(project_path: str, node_id: str) -> str | None:
    overview = read_canvas(resolve_plot_root(project_path), "alpha", "services")
    node = next(n for n in overview.nodes if n.id == node_id)
    assert isinstance(node, (ServiceNode, FeatureNode))
    return node.design_check.state if node.design_check is not None else None


def test_another_conversation_cannot_record_a_features_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_path = _project(tmp_path)
    monkeypatch.setenv(_SCOPE, "entities")

    # 12:30:48 and 12:31:25, from the entities conversation.
    with pytest.raises(ValueError, match="open that feature's canvas"):
        mcp_tools.set_design_check(project_path, "alpha", _SIBLING, "checking", 1, 1)
    with pytest.raises(ValueError, match="open that feature's canvas"):
        mcp_tools.set_design_check(project_path, "alpha", _SIBLING, "checked", 1, 0)
    assert _check_state(project_path, _SIBLING) is None


def test_a_features_check_is_recorded_in_its_own_conversation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_path = _project(tmp_path)
    monkeypatch.setenv(_SCOPE, "services")
    with pytest.raises(ValueError, match="open that feature's canvas"):
        mcp_tools.set_design_check(project_path, "alpha", _SIBLING, "checking")
    monkeypatch.setenv(_SCOPE, f"feature:{_FEATURE}")
    with pytest.raises(ValueError, match="open that feature's canvas"):
        mcp_tools.set_design_check(project_path, "alpha", _SIBLING, "checking")

    monkeypatch.setenv(_SCOPE, f"feature:{_SIBLING}")
    mcp_tools.set_design_check(project_path, "alpha", _SIBLING, "checking")

    assert _check_state(project_path, _SIBLING) == "checking"


def test_a_services_check_is_recorded_in_the_services_conversation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_path = _project(tmp_path)
    for scope in ("entities", "project", f"feature:{_FEATURE}", "service:service_other"):
        monkeypatch.setenv(_SCOPE, scope)
        with pytest.raises(ValueError, match="Services canvas"):
            mcp_tools.set_design_check(project_path, "alpha", _SERVICE, "checking")
    assert _check_state(project_path, _SERVICE) is None

    for scope in ("services", f"service:{_SERVICE}"):
        monkeypatch.setenv(_SCOPE, scope)
        mcp_tools.set_design_check(project_path, "alpha", _SERVICE, "checked", 0, 0)
    assert _check_state(project_path, _SERVICE) == "checked"


def test_an_outside_agent_records_any_check(tmp_path: Path) -> None:
    project_path = _project(tmp_path)

    mcp_tools.set_design_check(project_path, "alpha", _SIBLING, "checked", 1, 0)
    mcp_tools.set_design_check(project_path, "alpha", _SERVICE, "checking")

    assert _check_state(project_path, _SIBLING) == "checked"
    assert _check_state(project_path, _SERVICE) == "checking"


def test_an_outside_agent_passing_a_scope_argument_is_not_restricted(tmp_path: Path) -> None:
    """Only the in-app turn's environment restricts; a tool argument does not."""
    project_path = _project(tmp_path)

    step = mcp_tools.create_node(
        project_path,
        "alpha",
        "feature",
        "step",
        {"label": "원장이 학생을 반에 배정한다"},
        service_id=_FEATURE,
        chat_scope="entities",
    )["node"]["id"]
    mcp_tools.create_edge(
        project_path, "alpha", "feature", _FEATURE, step, service_id=_FEATURE, chat_scope="entities"
    )

    assert len(_feature(project_path).nodes) == 2
