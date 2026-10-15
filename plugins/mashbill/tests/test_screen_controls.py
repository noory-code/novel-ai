"""The coach's turn context names the controls the viewer has on screen.

A coach told a first-time user to look at a zoom-percentage display the canvas
does not have (novel-workspace O-00000136): nothing in its context said which
controls the screen shows, so it guessed. The viewer now reports its rendered
controls with its live context (``POST /api/viewer/context``), and every turn's
context lists them in a ``[Screen controls]`` line. The labels come from the
viewer; the engine holds no UI text of its own.
"""

from __future__ import annotations

import time
from pathlib import Path

from starlette.testclient import TestClient

from mashbill.broadcast import BroadcastHub
from mashbill.chat_screen_controls import render_screen_controls
from mashbill.chat_selection import build_turn_preamble
from mashbill.http_app import create_http_app
from mashbill.viewer_context import (
    CONTROL_LABEL_CAP,
    CONTROLS_CAP,
    TTL_SECONDS,
    read_viewer_context,
    write_viewer_context,
)
from mashbill.workspace import resolve_plot_root

_CONTROLS = ["확대", "축소", "화면에 맞추기", "되돌리기"]


def _post(tmp_path: Path, controls: object, scope: str = "feature:svc_1") -> None:
    client = TestClient(create_http_app(hub=BroadcastHub(enable_watchers=False)))
    resp = client.post(
        "/api/viewer/context",
        json={
            "project_path": str(tmp_path),
            "scope": scope,
            "selection": [],
            "controls": controls,
        },
    )
    assert resp.status_code == 202


def test_the_store_keeps_the_controls_the_viewer_reported(tmp_path: Path) -> None:
    base = tmp_path / "rt"
    base.mkdir()
    write_viewer_context(
        tmp_path, scope="foundation", selection=[], controls=_CONTROLS, now=1000.0, base_dir=base
    )

    ctx = read_viewer_context(tmp_path, now=1001.0, base_dir=base)

    assert ctx["controls"] == _CONTROLS


def test_a_report_without_controls_reads_as_none(tmp_path: Path) -> None:
    """An older viewer or a harness without a screen reports no controls."""
    base = tmp_path / "rt"
    base.mkdir()
    write_viewer_context(tmp_path, scope="foundation", selection=[], now=1000.0, base_dir=base)

    assert read_viewer_context(tmp_path, now=1001.0, base_dir=base)["controls"] == []
    assert read_viewer_context(tmp_path / "none", now=1.0, base_dir=base)["controls"] == []


def test_the_endpoint_keeps_only_short_distinct_labels(tmp_path: Path) -> None:
    long_label = "가" * (CONTROL_LABEL_CAP + 5)
    _post(tmp_path, [" 확대 ", "확대", "", 3, None, "축소", long_label])

    ctx = read_viewer_context(resolve_plot_root(str(tmp_path)), now=time.time())

    assert ctx["controls"] == ["확대", "축소", "가" * CONTROL_LABEL_CAP]


def test_the_endpoint_caps_the_number_of_controls(tmp_path: Path) -> None:
    _post(tmp_path, [f"버튼 {i}" for i in range(CONTROLS_CAP + 10)])

    ctx = read_viewer_context(resolve_plot_root(str(tmp_path)), now=time.time())

    assert len(ctx["controls"]) == CONTROLS_CAP


def test_the_endpoint_ignores_malformed_controls(tmp_path: Path) -> None:
    _post(tmp_path, "확대")

    ctx = read_viewer_context(resolve_plot_root(str(tmp_path)), now=time.time())

    assert ctx["controls"] == []


def test_the_turn_context_names_the_controls_on_screen(tmp_path: Path) -> None:
    _post(tmp_path, _CONTROLS)
    plot_root = resolve_plot_root(str(tmp_path))

    preamble = build_turn_preamble(plot_root, "feature:svc_1", [])

    line = render_screen_controls(plot_root)
    assert line.startswith("[Screen controls]")
    assert "확대, 축소, 화면에 맞추기, 되돌리기" in line
    assert line in preamble


def test_the_controls_show_without_a_selection_and_on_the_project_scope(tmp_path: Path) -> None:
    _post(tmp_path, _CONTROLS, scope="project")
    plot_root = resolve_plot_root(str(tmp_path))

    assert "[Screen controls]" in build_turn_preamble(plot_root, "project", None)


def test_no_line_without_a_live_viewer(tmp_path: Path) -> None:
    plot_root = resolve_plot_root(str(tmp_path))
    assert render_screen_controls(plot_root) == ""

    write_viewer_context(
        plot_root,
        scope="foundation",
        selection=[],
        controls=_CONTROLS,
        now=time.time() - TTL_SECONDS - 5,
    )
    assert render_screen_controls(plot_root) == ""
    assert "[Screen controls]" not in build_turn_preamble(plot_root, "foundation", [])


def test_no_line_when_the_viewer_reports_no_controls(tmp_path: Path) -> None:
    _post(tmp_path, [])

    assert render_screen_controls(resolve_plot_root(str(tmp_path))) == ""


def test_the_external_agent_reads_the_controls_too(tmp_path: Path) -> None:
    from mashbill.mcp_tools import get_viewer_context

    _post(tmp_path, _CONTROLS)

    ctx = get_viewer_context(str(tmp_path))

    assert ctx["controls"] == _CONTROLS
    assert "[Screen controls]" in ctx["context"]


# --- tabs and the buttons beside them (novel-workspace W-00000471) ----------
#
# In the second first-time-user walk the coach did not know the canvas tabs or
# the publish buttons: it asked the person where the flow canvas was, and after
# a publish it never pointed to the work tab (O-00000146, O-00000148). The
# viewer now also reports the tab labels and the buttons outside the canvas
# (the project publish beside the tabs, a selected service's publish), and the
# line names them as tabs and buttons.

_TABS = ["파운데이션", "액터", "서비스", "엔티티", "일감"]
_PAGE = ["설계도 발행", "📤 서비스 발행"]


def _post_screen(tmp_path: Path, *, controls: object, tabs: object, page_controls: object) -> None:
    client = TestClient(create_http_app(hub=BroadcastHub(enable_watchers=False)))
    resp = client.post(
        "/api/viewer/context",
        json={
            "project_path": str(tmp_path),
            "scope": "services",
            "selection": [],
            "controls": controls,
            "tabs": tabs,
            "page_controls": page_controls,
        },
    )
    assert resp.status_code == 202


def test_the_store_keeps_the_tabs_and_page_controls(tmp_path: Path) -> None:
    base = tmp_path / "rt"
    base.mkdir()
    write_viewer_context(
        tmp_path,
        scope="services",
        selection=[],
        controls=_CONTROLS,
        tabs=_TABS,
        page_controls=_PAGE,
        now=1000.0,
        base_dir=base,
    )

    ctx = read_viewer_context(tmp_path, now=1001.0, base_dir=base)

    assert ctx["tabs"] == _TABS
    assert ctx["page_controls"] == _PAGE


def test_a_report_without_tabs_reads_as_none(tmp_path: Path) -> None:
    base = tmp_path / "rt"
    base.mkdir()
    write_viewer_context(tmp_path, scope="foundation", selection=[], now=1000.0, base_dir=base)

    ctx = read_viewer_context(tmp_path, now=1001.0, base_dir=base)
    assert ctx["tabs"] == [] and ctx["page_controls"] == []
    empty = read_viewer_context(tmp_path / "none", now=1.0, base_dir=base)
    assert empty["tabs"] == [] and empty["page_controls"] == []


def test_the_endpoint_trims_and_caps_tabs_and_page_controls(tmp_path: Path) -> None:
    long_label = "가" * (CONTROL_LABEL_CAP + 5)
    _post_screen(
        tmp_path,
        controls=[],
        tabs=[" 일감 ", "일감", 3, long_label],
        page_controls=[f"버튼 {i}" for i in range(CONTROLS_CAP + 10)],
    )

    ctx = read_viewer_context(resolve_plot_root(str(tmp_path)), now=time.time())

    assert ctx["tabs"] == ["일감", "가" * CONTROL_LABEL_CAP]
    assert len(ctx["page_controls"]) == CONTROLS_CAP


def test_the_line_names_tabs_canvas_buttons_and_page_buttons_apart(tmp_path: Path) -> None:
    _post_screen(tmp_path, controls=_CONTROLS, tabs=_TABS, page_controls=_PAGE)

    line = render_screen_controls(resolve_plot_root(str(tmp_path)))

    assert line.startswith("[Screen controls]")
    assert "Canvas tabs: 파운데이션, 액터, 서비스, 엔티티, 일감." in line
    assert "Buttons on the canvas: 확대, 축소, 화면에 맞추기, 되돌리기." in line
    assert "설계도 발행, 📤 서비스 발행" in line
    # The tabs and canvas buttons are always rendered, so the coach names only
    # these; the page buttons come and go with the selection, so the guard does
    # not forbid a publish button that is not on screen this moment.
    guard, page = line.split("name only these", 1)
    assert "설계도 발행" not in guard
    assert "설계도 발행" in page
    assert "the screen has no other" not in line


def test_the_line_shows_with_only_tabs(tmp_path: Path) -> None:
    """The work tab has no design-canvas toolbar but still has the tabs."""
    _post_screen(tmp_path, controls=[], tabs=_TABS, page_controls=["설계도 발행"])

    line = render_screen_controls(resolve_plot_root(str(tmp_path)))

    assert "Canvas tabs: 파운데이션, 액터, 서비스, 엔티티, 일감." in line
    assert "Buttons on the canvas" not in line
    assert "설계도 발행" in line


def test_an_older_viewer_keeps_the_canvas_only_line(tmp_path: Path) -> None:
    _post(tmp_path, _CONTROLS)

    line = render_screen_controls(resolve_plot_root(str(tmp_path)))

    assert line == (
        "[Screen controls] Buttons on the canvas: 확대, 축소, 화면에 맞추기, 되돌리기. "
        "When pointing to a canvas button or display, name only these; the canvas has no other."
    )


def test_the_external_agent_reads_the_tabs_too(tmp_path: Path) -> None:
    from mashbill.mcp_tools import get_viewer_context

    _post_screen(tmp_path, controls=_CONTROLS, tabs=_TABS, page_controls=_PAGE)

    ctx = get_viewer_context(str(tmp_path))

    assert ctx["tabs"] == _TABS
    assert ctx["page_controls"] == _PAGE
    assert "Canvas tabs:" in ctx["context"]
