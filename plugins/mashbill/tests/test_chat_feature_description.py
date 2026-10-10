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


def test_feature_description_without_selection_uses_services_node(tmp_path: Path) -> None:
    plot_root = _project(tmp_path, "Draw each step and outcome")

    preamble = build_turn_preamble(plot_root, "feature:feature_x", [])

    assert (
        '[Feature description] "기능 흐름 그리기" (feature_x): Draw each step and outcome'
        in preamble
    )
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


def test_feature_description_collapses_internal_newlines(tmp_path: Path) -> None:
    plot_root = _project(tmp_path, "First branch\n  Second branch\r\nThird branch")

    preamble = build_turn_preamble(plot_root, "feature:feature_x", [])

    assert (
        '[Feature description] "기능 흐름 그리기" (feature_x): '
        "First branch Second branch Third branch"
    ) in preamble
