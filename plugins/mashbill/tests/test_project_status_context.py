"""Every coach turn names the project and what has been published (W-00000490).

Newcomer walk 4: the work tab's coach did not know the project id, so its tool
calls failed, and it answered "if you have not published the blueprint yet…"
after both the blueprint and a service had been published. The turn context now
carries one [Project] line in every scope.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mashbill import chat_project_status
from mashbill.chat_project_status import render_project_status
from mashbill.chat_selection import build_turn_preamble
from mashbill.folder_io import create_project, write_canvas
from mashbill.format_f_slugs import write_slug_store
from mashbill.models import CanvasDoc, ServiceNode
from mashbill.workspace import resolve_plot_root


def _project(tmp_path: Path) -> Path:
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "academy", "보습학원 출결")
    return plot_root


def _release(plot_root: Path, scope: str, name: str, extra: dict[str, str]) -> None:
    """A release folder with a manifest shaped like a real format F release."""
    folder = plot_root / "published" / scope / name
    folder.mkdir(parents=True)
    manifest: dict[str, object] = {
        "format_f_version": 1,
        "scope": "project" if scope == "_project" else "service",
        "release": name,
        "elements": [],
        **extra,
    }
    (folder / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def test_unpublished_project_says_nothing_is_published_yet(tmp_path: Path) -> None:
    line = render_project_status(_project(tmp_path))
    assert line.startswith("[Project] id academy")
    assert "blueprint: not published yet" in line
    assert "services: none yet" in line


def test_published_blueprint_and_services_are_named(tmp_path: Path) -> None:
    plot_root = _project(tmp_path)
    _release(plot_root, "_project", "vP1", {"blueprint_version": "v0.1.0"})
    _release(plot_root, "_project", "vP2", {"blueprint_version": "v0.2.0"})
    _release(
        plot_root,
        "tuition-management",
        "vS1",
        {"service": "service/tuition-management"},
    )
    line = render_project_status(plot_root)
    assert "blueprint: v0.2.0" in line
    assert "services: tuition-management vS1" in line


def test_every_service_on_the_canvas_says_whether_it_is_published(tmp_path: Path) -> None:
    """A service drawn but never published reads 'not published yet', so the
    coach does not take one published service for the whole project."""
    plot_root = _project(tmp_path)
    write_canvas(
        plot_root,
        "academy",
        CanvasDoc(
            canvas_id="services",
            canvas_kind="services",
            nodes=[
                ServiceNode(id="s_fee", label="수강료 관리", x=0.0, y=0.0),
                ServiceNode(id="s_att", label="출결 확인", x=0.0, y=200.0),
            ],
        ),
    )
    write_slug_store(plot_root, "academy", {"s_fee": "service/tuition-management"})
    _release(plot_root, "_project", "vP1", {"blueprint_version": "v0.1.0"})
    _release(plot_root, "tuition-management", "vS1", {"service": "service/tuition-management"})
    line = render_project_status(plot_root)
    assert "수강료 관리 vS1" in line
    assert "출결 확인 not published yet" in line


def test_every_scope_carries_the_project_line(tmp_path: Path) -> None:
    plot_root = _project(tmp_path)
    for scope in ("project", "foundation", "services", "entities", "feature:feature_x"):
        assert "[Project] id academy" in build_turn_preamble(plot_root, scope, []), scope


def test_unreadable_release_does_not_break_the_turn(tmp_path: Path) -> None:
    plot_root = _project(tmp_path)
    folder = plot_root / "published" / "_project" / "vP1"
    folder.mkdir(parents=True)
    (folder / "manifest.json").write_text("{not json", encoding="utf-8")
    line = render_project_status(plot_root)
    assert line.startswith("[Project] id academy")


def test_an_unreadable_publish_folder_still_lists_each_service(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reading the publish folder fails: the services on the canvas are still
    named, each as not published yet."""
    plot_root = _project(tmp_path)
    write_canvas(
        plot_root,
        "academy",
        CanvasDoc(
            canvas_id="services",
            canvas_kind="services",
            nodes=[ServiceNode(id="s_fee", label="수강료 관리", x=0.0, y=0.0)],
        ),
    )

    def _unreadable(_project_dir: Path) -> list[object]:
        raise OSError("permission denied")

    monkeypatch.setattr(chat_project_status, "latest_service_releases", _unreadable)
    line = render_project_status(plot_root)
    assert "수강료 관리 not published yet" in line


def test_an_unreadable_slug_record_keeps_the_published_releases(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The service-name record cannot be read: a published service still shows
    its release (by its folder name), and a drawn service is not wrongly
    called unpublished because of it."""
    plot_root = _project(tmp_path)
    _release(plot_root, "_project", "vP1", {"blueprint_version": "v0.1.0"})
    _release(plot_root, "tuition-management", "vS1", {"service": "service/tuition-management"})

    def _unreadable(_plot_root: Path, _project_id: str) -> dict[str, str]:
        raise ValueError("_slugs.json is broken")

    monkeypatch.setattr(chat_project_status, "read_slug_store", _unreadable)
    line = render_project_status(plot_root)
    assert "tuition-management vS1" in line
