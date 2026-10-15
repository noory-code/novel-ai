"""propose_flow refuses branching defects a machine can see (novel-workspace W-00000448).

A decision needs at least two branches (or an open question about the missing
case), each branch names its case, no two branches of one decision name the same
case, and every loop has a line leaving it (or an open question about the way
out). A last step with no outgoing line is a valid end. Only defects the draft
creates are refused: what is already drawn on the canvas does not block a draft.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from mashbill import mcp_tools
from mashbill.folder_io import create_project, write_canvas
from mashbill.models import ActorRefNode, CanvasDoc, FeatureNode, SketchEdge
from mashbill.workspace import resolve_plot_root


def _project(tmp_path: Path) -> str:
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    write_canvas(
        plot_root,
        "alpha",
        CanvasDoc(
            canvas_id="services",
            canvas_kind="services",
            nodes=[FeatureNode(id="feature_x", label="카드 등록")],
        ),
    )
    write_canvas(
        plot_root,
        "alpha",
        CanvasDoc(
            canvas_id="feature_x",
            canvas_kind="feature",
            feature_ref="feature_x",
            nodes=[FeatureNode(id="feature_x", label="카드 등록")],
        ),
    )
    return str(tmp_path)


def _nodes() -> list[dict[str, Any]]:
    return [
        {"key": "enter", "kind": "step", "label": "손님이 카드를 등록한다"},
        {"key": "ok", "kind": "decision", "label": "카드 등록에 성공했는가?"},
        {"key": "retry", "kind": "step", "label": "손님이 다른 카드를 입력한다"},
        {"key": "next", "kind": "step", "label": "손님이 수거 시간을 고른다"},
        {"key": "quit", "kind": "step", "label": "손님이 등록을 그만둔다"},
    ]


def _edges() -> list[dict[str, Any]]:
    return [
        {"source": "feature_x", "target": "enter"},
        {"source": "enter", "target": "ok"},
        {"source": "ok", "target": "next", "label": "성공"},
        {"source": "ok", "target": "retry", "label": "실패"},
        {"source": "retry", "target": "enter", "label": "다시 입력"},
        {"source": "retry", "target": "quit", "label": "그만둔다"},
    ]


def _propose(project_path: str, **overrides: Any) -> dict[str, Any]:
    args: dict[str, Any] = {"nodes": _nodes(), "edges": _edges()}
    args.update(overrides)
    return mcp_tools.propose_flow(project_path, "alpha", "feature_x", **args)


def _without(source: str, target: str) -> list[dict[str, Any]]:
    return [e for e in _edges() if (e["source"], e["target"]) != (source, target)]


def test_a_well_branched_draft_with_outcome_less_ends_is_recorded(tmp_path: Path) -> None:
    """Two ends (next, quit) have no outgoing line and no outcome: valid ends."""
    assert "rendered" in _propose(_project(tmp_path))


def test_a_decision_with_one_branch_is_refused(tmp_path: Path) -> None:
    project_path = _project(tmp_path)

    with pytest.raises(ValueError, match="카드 등록에 성공했는가") as raised:
        _propose(project_path, edges=_without("ok", "retry"))
    assert "1 branch" in str(raised.value)
    assert "open_items" in str(raised.value)


def test_a_decision_with_no_branch_is_refused(tmp_path: Path) -> None:
    project_path = _project(tmp_path)
    edges = [e for e in _edges() if e["source"] != "ok"]

    with pytest.raises(ValueError, match="0 branches"):
        _propose(project_path, edges=edges)


def test_an_open_question_at_a_decision_stands_for_its_missing_branch(tmp_path: Path) -> None:
    project_path = _project(tmp_path)

    rendered = _propose(
        project_path,
        edges=_without("ok", "retry"),
        open_items=[{"at": "ok", "question": "카드 등록에 실패하면 어떻게 되나요?"}],
    )["rendered"]

    assert "… 카드 등록에 실패하면 어떻게 되나요?" in rendered


def test_a_decision_branch_without_a_label_is_refused(tmp_path: Path) -> None:
    project_path = _project(tmp_path)
    edges = [
        {**e, "label": " "} if (e["source"], e["target"]) == ("ok", "retry") else e
        for e in _edges()
    ]

    with pytest.raises(ValueError, match="no label") as raised:
        _propose(project_path, edges=edges)
    assert "손님이 다른 카드를 입력한다" in str(raised.value)


def test_a_line_from_a_step_needs_no_label(tmp_path: Path) -> None:
    project_path = _project(tmp_path)
    edges = [{**e, "label": ""} if e["source"] != "ok" else e for e in _edges()]

    assert "rendered" in _propose(project_path, edges=edges)


def test_two_branches_of_one_decision_with_the_same_label_are_refused(tmp_path: Path) -> None:
    project_path = _project(tmp_path)
    edges = [
        {**e, "label": " 성공  "} if (e["source"], e["target"]) == ("ok", "retry") else e
        for e in _edges()
    ]

    with pytest.raises(ValueError, match="'성공'") as raised:
        _propose(project_path, edges=edges)
    assert "카드 등록에 성공했는가" in str(raised.value)


def test_a_loop_with_no_line_leaving_it_is_refused(tmp_path: Path) -> None:
    """The decision's success branch leaves the loop; without it and the give-up
    line, enter → ok → retry → enter never ends."""
    project_path = _project(tmp_path)
    edges = [
        e for e in _edges() if (e["source"], e["target"]) not in {("ok", "next"), ("retry", "quit")}
    ]
    edges.append({"source": "ok", "target": "enter", "label": "다시"})

    with pytest.raises(ValueError, match="loop") as raised:
        _propose(project_path, edges=edges)
    message = str(raised.value)
    for label in (
        "손님이 카드를 등록한다",
        "카드 등록에 성공했는가?",
        "손님이 다른 카드를 입력한다",
    ):
        assert label in message
    assert "open_items" in message


def test_an_open_question_in_a_loop_stands_for_its_way_out(tmp_path: Path) -> None:
    project_path = _project(tmp_path)
    edges = [
        e for e in _edges() if (e["source"], e["target"]) not in {("ok", "next"), ("retry", "quit")}
    ]
    edges.append({"source": "ok", "target": "enter", "label": "다시"})

    rendered = _propose(
        project_path,
        edges=edges,
        open_items=[{"at": "retry", "question": "몇 번 실패하면 그만두나요?"}],
    )["rendered"]

    assert "… 몇 번 실패하면 그만두나요?" in rendered


def test_a_step_looping_onto_itself_with_no_way_out_is_refused(tmp_path: Path) -> None:
    project_path = _project(tmp_path)
    nodes = [*_nodes(), {"key": "wait", "kind": "step", "label": "손님이 기다린다"}]
    edges = [
        *_edges(),
        {"source": "next", "target": "wait"},
        {"source": "wait", "target": "wait"},
    ]

    with pytest.raises(ValueError, match="손님이 기다린다"):
        _propose(project_path, nodes=nodes, edges=edges)


def test_every_defect_is_named_in_one_refusal(tmp_path: Path) -> None:
    project_path = _project(tmp_path)
    nodes = [*_nodes(), {"key": "pay", "kind": "decision", "label": "결제가 되었는가?"}]
    edges = [*_edges(), {"source": "next", "target": "pay"}, {"source": "pay", "target": "quit"}]

    with pytest.raises(ValueError) as raised:
        _propose(project_path, nodes=nodes, edges=edges)
    message = str(raised.value)
    assert "결제가 되었는가?" in message and "1 branch" in message
    assert "no label" in message


def _draw_hand_made_decision(project_path: str) -> dict[str, str]:
    """A person drew a decision with one branch so far."""
    decision = mcp_tools.create_node(
        project_path,
        "alpha",
        "feature",
        "decision",
        {"label": "손님이 집에 있는가?"},
        service_id="feature_x",
    )["node"]["id"]
    home = mcp_tools.create_node(
        project_path,
        "alpha",
        "feature",
        "step",
        {"label": "기사님이 세탁물을 받는다"},
        service_id="feature_x",
    )["node"]["id"]
    mcp_tools.create_edge(
        project_path, "alpha", "feature", decision, home, label="있다", service_id="feature_x"
    )
    return {"decision": decision, "home": home}


def test_what_is_already_drawn_does_not_block_a_draft(tmp_path: Path) -> None:
    project_path = _project(tmp_path)
    _draw_hand_made_decision(project_path)

    assert "rendered" in _propose(project_path)


def test_a_draft_that_leaves_a_drawn_decision_one_branch_is_refused(tmp_path: Path) -> None:
    project_path = _project(tmp_path)
    drawn = _draw_hand_made_decision(project_path)
    away = mcp_tools.create_node(
        project_path,
        "alpha",
        "feature",
        "step",
        {"label": "기사님이 다시 방문한다"},
        service_id="feature_x",
    )["node"]["id"]
    mcp_tools.create_edge(
        project_path,
        "alpha",
        "feature",
        drawn["decision"],
        away,
        label="없다",
        service_id="feature_x",
    )

    with pytest.raises(ValueError, match="손님이 집에 있는가"):
        _propose(project_path, remove_edges=[{"source": drawn["decision"], "target": away}])


def test_a_draft_branch_repeating_a_drawn_branch_label_is_refused(tmp_path: Path) -> None:
    project_path = _project(tmp_path)
    drawn = _draw_hand_made_decision(project_path)

    with pytest.raises(ValueError, match="'있다'"):
        _propose(
            project_path,
            edges=[*_edges(), {"source": drawn["decision"], "target": "quit", "label": "있다"}],
        )


# W-00000489 (newcomer walk 5, NEW-1) — '구독 신청': the coach drew a decision
# nothing led into (12:34:27) and removed the only line into '확정 문자'
# (12:35:46), each time with open items on the loose node, and drew both in
# the same turn.
def _subscription(project_path: str) -> dict[str, str]:
    """The 12:33:17 first draft on a canvas with no lines (description items left out)."""
    mcp_tools.propose_flow(
        project_path,
        "alpha",
        "feature_x",
        nodes=[
            {"key": "entry", "kind": "step", "label": "손님이 인스타 링크를 보고 들어온다"},
            {"key": "date", "kind": "step", "label": "손님이 첫 배송 날짜를 고른다"},
            {"key": "flowers", "kind": "note", "label": "꽃을 고르는 방식 안내"},
            {"key": "pay", "kind": "step", "label": "손님이 입금한다"},
            {"key": "check", "kind": "step", "label": "꽃집 사장이 입금을 확인한다"},
            {"key": "sms", "kind": "step", "label": "꽃집 사장이 확정 문자를 보낸다"},
        ],
        edges=[
            {"source": "entry", "target": "date"},
            {"source": "date", "target": "pay"},
            {"source": "pay", "target": "check"},
            {"source": "check", "target": "sms"},
        ],
        open_items=[{"at": "flowers", "question": "꽃을 고르는 방식은 어느 단계에서 안내하나요?"}],
    )
    ids: dict[str, str] = mcp_tools.draw_proposed_flow(project_path, "alpha", "feature_x")[
        "node_ids"
    ]
    return ids


def test_a_new_decision_nothing_leads_into_is_refused_even_with_open_items(
    tmp_path: Path,
) -> None:
    project_path = _project(tmp_path)
    ids = _subscription(project_path)

    with pytest.raises(ValueError, match="nothing leads into") as refused:
        mcp_tools.propose_flow(
            project_path,
            "alpha",
            "feature_x",
            nodes=[
                {"key": "paid", "kind": "decision", "label": "신청 후 3일까지 입금했나요?"},
                {"key": "cancel", "kind": "step", "label": "꽃집 사장이 신청을 취소한다"},
                {
                    "key": "delivery",
                    "kind": "decision",
                    "label": "첫 배송일까지 이틀도 안 남았나요?",
                },
                {"key": "postpone", "kind": "step", "label": "꽃집 사장이 첫 배송을 미룬다"},
                {"key": "payment_rule", "kind": "rule", "label": "입금은 신청 후 3일까지 기다린다"},
            ],
            remove_edges=[{"source": ids["pay"], "target": ids["check"]}],
            edges=[
                {"source": ids["pay"], "target": "paid"},
                {"source": "paid", "target": ids["check"], "label": "예"},
                {"source": "paid", "target": "cancel", "label": "아니요"},
                {"source": "delivery", "target": "postpone", "label": "예"},
            ],
            open_items=[
                {
                    "at": "delivery",
                    "question": "남은 시간은 신청할 때와 입금 확인할 때 중 언제 확인하나요?",
                },
                {"at": "delivery", "question": "이틀 이상 남았으면 어느 단계로 이어지나요?"},
                {"at": "postpone", "question": "다음 배송일로 미룬 뒤 어느 단계로 이어지나요?"},
            ],
        )

    message = str(refused.value)
    assert "첫 배송일까지 이틀도 안 남았나요?" in message
    # Reached nodes, a rule, and the drawn entry step are not named.
    for label in ("신청 후 3일까지", "꽃집 사장이 신청을 취소한다", "입금은", "인스타 링크"):
        assert label not in message, label


def test_removing_the_only_line_into_a_drawn_step_is_refused_even_with_open_items(
    tmp_path: Path,
) -> None:
    project_path = _project(tmp_path)
    ids = _subscription(project_path)
    # The canvas as walk 5 left it at 12:34:31: a decision drawn loose beside the flow.
    delivery = mcp_tools.create_node(
        project_path,
        "alpha",
        "feature",
        "decision",
        {"label": "첫 배송일까지 이틀도 안 남았나요?"},
        service_id="feature_x",
    )["node"]["id"]
    postpone = mcp_tools.create_node(
        project_path,
        "alpha",
        "feature",
        "step",
        {"label": "꽃집 사장이 첫 배송을 다음 배송일로 미룬다"},
        service_id="feature_x",
    )["node"]["id"]
    mcp_tools.create_edge(
        project_path, "alpha", "feature", delivery, postpone, label="예", service_id="feature_x"
    )

    # 12:35:46: the line 입금 확인 → 확정 문자 is cut while its replacement is still a question.
    with pytest.raises(ValueError, match="꽃집 사장이 확정 문자를 보낸다"):
        mcp_tools.propose_flow(
            project_path,
            "alpha",
            "feature_x",
            nodes=[],
            remove_edges=[{"source": ids["check"], "target": ids["sms"]}],
            edges=[{"source": ids["check"], "target": delivery}],
            open_items=[
                {"at": delivery, "question": "이틀 이상 남았으면 바로 확정 문자를 보내나요?"},
                {"at": postpone, "question": "미룬 뒤 그 날짜로 확정 문자를 보내나요?"},
            ],
        )

    # 12:36:29: the same change with the lines that reach 확정 문자 is recorded.
    assert "rendered" in mcp_tools.propose_flow(
        project_path,
        "alpha",
        "feature_x",
        nodes=[],
        remove_edges=[{"source": ids["check"], "target": ids["sms"]}],
        edges=[
            {"source": ids["check"], "target": delivery},
            {"source": delivery, "target": ids["sms"], "label": "아니요 · 이틀 이상 남음"},
            {"source": postpone, "target": ids["sms"]},
        ],
    )


def test_a_first_draft_beside_an_actor_line_keeps_its_entry(tmp_path: Path) -> None:
    """A line between the feature root and its actor is not a flow yet, so the
    first draft's entry step needs no line into it."""
    project_path = _project(tmp_path)
    write_canvas(
        resolve_plot_root(project_path),
        "alpha",
        CanvasDoc(
            canvas_id="feature_x",
            canvas_kind="feature",
            feature_ref="feature_x",
            nodes=[
                FeatureNode(id="feature_x", label="카드 등록"),
                ActorRefNode(id="actor_ref_x", label="손님", ref_actor_id="actor_x"),
            ],
            edges=[SketchEdge(id="edge_x", source="feature_x", target="actor_ref_x")],
        ),
    )

    assert "rendered" in mcp_tools.propose_flow(
        project_path,
        "alpha",
        "feature_x",
        nodes=[
            {"key": "entry", "kind": "step", "label": "손님이 인스타 링크를 보고 들어온다"},
            {"key": "pay", "kind": "step", "label": "손님이 입금한다"},
        ],
        edges=[{"source": "entry", "target": "pay"}],
    )
