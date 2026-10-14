"""The services coach hands the agreed service set to the engine, which adds every missing
service at once.

A coach that walks through services one at a time asked to keep only the newest one and left the
rest of the agreed set off the canvas (novel-workspace O-00000123, W-00000425). propose_services
holds the whole set; add_proposed_services writes every service of it that the canvas lacks in
one canvas write.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mashbill import mcp_tools
from mashbill.folder_io import create_project, read_canvas, write_canvas
from mashbill.mcp_registration import IN_APP_COACH_ENV
from mashbill.models import CanvasDoc
from mashbill.models_actors import ServiceNode
from mashbill.workspace import resolve_plot_root


def _project(tmp_path: Path, existing: list[str] | None = None) -> str:
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    write_canvas(
        plot_root,
        "alpha",
        CanvasDoc(
            canvas_id="services",
            canvas_kind="services",
            nodes=[
                ServiceNode(id=f"service_{i}", label=label)
                for i, label in enumerate(existing or [])
            ],
        ),
    )
    return str(tmp_path)


def _services_canvas(project_path: str) -> CanvasDoc:
    return read_canvas(resolve_plot_root(project_path), "alpha", "services")


def _set() -> list[dict[str, Any]]:
    return [
        {"key": "pay", "label": "돈 보내기", "value_created": "문자 보내듯 쉽게 돈을 보낸다"},
        {"key": "asset", "label": "자산·소비 관리", "value_created": "지출과 자산을 한눈에 본다"},
        {"key": "invest", "label": "주식 투자"},
        {"key": "reward", "label": "혜택·리워드", "problem": "금융이 멀게 느껴진다"},
    ]


def _labels(project_path: str) -> list[str]:
    return [n.label for n in _services_canvas(project_path).nodes if n.kind == "service"]


def test_propose_renders_the_whole_set_and_adds_nothing(tmp_path: Path) -> None:
    project_path = _project(tmp_path)

    rendered = mcp_tools.propose_services(project_path, "alpha", services=_set())["rendered"]

    for line in (
        "[1] 돈 보내기: 문자 보내듯 쉽게 돈을 보낸다",
        "[3] 주식 투자",
        "[4] 혜택·리워드",
    ):
        assert line in rendered
    assert _labels(project_path) == []


def test_the_person_reads_numbers_and_the_coach_gets_the_keys(tmp_path: Path) -> None:
    """The coach's keys are often English names it made up; the person reads numbers."""
    project_path = _project(tmp_path)

    result = mcp_tools.propose_services(project_path, "alpha", services=_set())

    for key in ("pay", "asset", "invest", "reward"):
        assert f"[{key}]" not in result["rendered"]
    assert result["numbers"] == {"1": "pay", "2": "asset", "3": "invest", "4": "reward"}


def test_propose_marks_services_already_on_the_canvas(tmp_path: Path) -> None:
    project_path = _project(tmp_path, existing=["돈 보내기"])

    rendered = mcp_tools.propose_services(project_path, "alpha", services=_set())["rendered"]

    # Numbers follow the coach's order, so they stay the same whatever the canvas holds.
    assert "[1] ✓ 돈 보내기" in rendered
    assert "[2] 자산·소비 관리: 지출과 자산을 한눈에 본다" in rendered
    assert "[pay]" not in rendered


@pytest.mark.parametrize(
    "services",
    [
        [{"key": "a", "label": "하나"}, {"key": "a", "label": "둘"}],
        [{"key": "a", "label": "하나"}, {"key": "b", "label": " 하나 "}],
        [],
    ],
)
def test_propose_rejects_repeated_keys_or_names_and_an_empty_set(
    tmp_path: Path, services: list[dict[str, Any]]
) -> None:
    project_path = _project(tmp_path)

    with pytest.raises(ValueError):
        mcp_tools.propose_services(project_path, "alpha", services=services)


def test_add_writes_every_missing_service_once(tmp_path: Path) -> None:
    project_path = _project(tmp_path, existing=["돈 보내기"])
    mcp_tools.propose_services(project_path, "alpha", services=_set())

    result = mcp_tools.add_proposed_services(project_path, "alpha")

    assert sorted(_labels(project_path)) == sorted(s["label"] for s in _set())
    assert sorted(result["service_ids"]) == ["asset", "invest", "reward"]
    nodes = {n.label: n for n in _services_canvas(project_path).nodes}
    asset = nodes["자산·소비 관리"]
    assert isinstance(asset, ServiceNode) and asset.value_created == "지출과 자산을 한눈에 본다"
    reward = nodes["혜택·리워드"]
    assert isinstance(reward, ServiceNode) and reward.problem == "금융이 멀게 느껴진다"


def test_add_refuses_without_a_proposal_and_refuses_to_add_twice(tmp_path: Path) -> None:
    project_path = _project(tmp_path)

    with pytest.raises(ValueError, match="propose_services"):
        mcp_tools.add_proposed_services(project_path, "alpha")

    mcp_tools.propose_services(project_path, "alpha", services=_set())
    mcp_tools.add_proposed_services(project_path, "alpha")
    with pytest.raises(ValueError, match="already added"):
        mcp_tools.add_proposed_services(project_path, "alpha")
    assert len(_labels(project_path)) == len(_set())


def test_a_new_proposal_replaces_one_not_yet_added(tmp_path: Path) -> None:
    project_path = _project(tmp_path)
    mcp_tools.propose_services(project_path, "alpha", services=_set())
    mcp_tools.propose_services(project_path, "alpha", services=_set()[:2])

    mcp_tools.add_proposed_services(project_path, "alpha")

    assert sorted(_labels(project_path)) == ["돈 보내기", "자산·소비 관리"]


def test_the_in_app_coach_is_told_the_app_shows_the_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_path = _project(tmp_path)

    monkeypatch.setenv(IN_APP_COACH_ENV, "1")
    in_app = mcp_tools.propose_services(project_path, "alpha", services=_set())["show"]
    monkeypatch.delenv(IN_APP_COACH_ENV)
    headless = mcp_tools.propose_services(project_path, "alpha", services=_set())["show"]

    assert "app shows" in in_app and "do not restate" in in_app
    assert "Show the person this service set" in headless


def test_both_tools_log_identifiers_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    log = tmp_path / "tools.jsonl"
    monkeypatch.setenv("MASHBILL_TOOL_LOG", str(log))
    project_path = _project(tmp_path)

    mcp_tools.propose_services(project_path, "alpha", services=_set())
    mcp_tools.add_proposed_services(project_path, "alpha")

    lines = [json.loads(line) for line in log.read_text().splitlines()]
    assert [line["tool"] for line in lines] == ["propose_services", "add_proposed_services"]
    assert all(line["canvas"] == "services" for line in lines)
    assert all("돈 보내기" not in json.dumps(line, ensure_ascii=False) for line in lines)
    assert len(lines[1]["node_ids"]) == len(_set())


def test_propose_refuses_a_set_with_nothing_to_add(tmp_path: Path) -> None:
    """A set whose services are all on the canvas showed a ✓-only block under feature talk
    (W-00000426: five of six feature-candidate turns)."""
    project_path = _project(tmp_path, existing=[s["label"] for s in _set()])

    with pytest.raises(ValueError, match="already on the Services canvas"):
        mcp_tools.propose_services(project_path, "alpha", services=_set())
