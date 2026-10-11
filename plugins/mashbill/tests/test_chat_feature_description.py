"""Feature-scope chat context reads its description from the Services canvas."""

from __future__ import annotations

from pathlib import Path

import pytest

from mashbill.chat_selection import build_turn_preamble
from mashbill.folder_io import create_project, write_canvas
from mashbill.models import CanvasDoc, FeatureNode
from mashbill.workspace import resolve_plot_root


def _project(tmp_path: Path, proposed: str | None) -> Path:
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    if proposed is not None:
        write_canvas(
            plot_root,
            "alpha",
            CanvasDoc(
                canvas_id="services",
                canvas_kind="services",
                nodes=[FeatureNode(id="feature_x", label="기능 흐름 그리기", proposed=proposed)],
            ),
        )
    write_canvas(
        plot_root,
        "alpha",
        CanvasDoc(
            canvas_id="feature_x",
            canvas_kind="feature",
            feature_ref="feature_x",
            nodes=[FeatureNode(id="feature_x", label="Old label", proposed="stale detail copy")],
        ),
    )
    return plot_root


_HEADER = (
    '[Feature description] "기능 흐름 그리기" (feature_x). Each numbered item is a '
    "step a canvas holds: draft it in the flow where its wording places it, and "
    "keep an ending it does not state open on that step."
)


def test_feature_description_without_selection_uses_services_node(tmp_path: Path) -> None:
    plot_root = _project(tmp_path, "Draw each step and outcome")

    preamble = build_turn_preamble(plot_root, "feature:feature_x", [])

    assert f"{_HEADER}\n1. Draw each step and outcome" in preamble
    assert "stale detail copy" not in preamble
    assert preamble.index("[Canvas: feature:feature_x]") < preamble.index("[Feature description]")
    assert "\n\n[Feature description]" in preamble


@pytest.mark.parametrize("proposed", ["", " \n\t ", None])
def test_feature_description_omitted_without_services_text(
    tmp_path: Path, proposed: str | None
) -> None:
    plot_root = _project(tmp_path, proposed)

    assert "[Feature description]" not in build_turn_preamble(plot_root, "feature:feature_x", [])


def test_feature_description_omitted_when_services_node_is_missing(tmp_path: Path) -> None:
    plot_root = _project(tmp_path, None)
    write_canvas(
        plot_root,
        "alpha",
        CanvasDoc(
            canvas_id="services",
            canvas_kind="services",
            nodes=[FeatureNode(id="other_feature", label="Other", proposed="Other description")],
        ),
    )

    assert "[Feature description]" not in build_turn_preamble(plot_root, "feature:feature_x", [])


@pytest.mark.parametrize(
    "scope", ["services", "service:feature_x", "entities", "foundation", "actors", "project"]
)
def test_feature_description_only_on_feature_scope(tmp_path: Path, scope: str) -> None:
    plot_root = _project(tmp_path, "Services-owned description")

    assert "[Feature description]" not in build_turn_preamble(plot_root, scope, [])


def test_feature_description_lists_each_sentence_as_a_numbered_item(tmp_path: Path) -> None:
    """The real self-design description: three sentences, the second holding two
    branches joined by "-거나" — one sentence stays one item."""
    plot_root = _project(
        tmp_path,
        "사용자는 기능에서 사람이 하는 일과 갈림길, 끝 결과를 정한다. "
        "초안에 필요한 정보가 부족하면 한 가지씩 더 답하거나 나중에 이어 간다. "
        "그린 흐름의 선을 고치거나 지울 수 있다.",
    )

    preamble = build_turn_preamble(plot_root, "feature:feature_x", [])

    assert (
        f"{_HEADER}\n"
        "1. 사용자는 기능에서 사람이 하는 일과 갈림길, 끝 결과를 정한다.\n"
        "2. 초안에 필요한 정보가 부족하면 한 가지씩 더 답하거나 나중에 이어 간다.\n"
        "3. 그린 흐름의 선을 고치거나 지울 수 있다."
    ) in preamble


def test_feature_description_splits_lines_and_collapses_spaces(tmp_path: Path) -> None:
    plot_root = _project(tmp_path, "First  branch\n  Second branch\r\n\r\nThird branch")

    preamble = build_turn_preamble(plot_root, "feature:feature_x", [])

    assert f"{_HEADER}\n1. First branch\n2. Second branch\n3. Third branch" in preamble


def test_feature_description_keeps_decimal_points_inside_an_item(tmp_path: Path) -> None:
    plot_root = _project(tmp_path, "Pay 1.5 times the fee. Then leave!  Done?")

    preamble = build_turn_preamble(plot_root, "feature:feature_x", [])

    assert f"{_HEADER}\n1. Pay 1.5 times the fee.\n2. Then leave!\n3. Done?" in preamble
