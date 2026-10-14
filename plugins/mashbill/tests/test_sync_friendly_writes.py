"""A canvas edit changes that canvas only (D-2026-10-14-C).

Two machines that share a project folder (a git remote or a synced folder) each
edit different nodes. If every canvas save also rewrote ``project.json`` to
bump its ``updated`` stamp, the two edits would always collide on that one file
even when they touched different nodes. The project list's "most recently
edited first" order reads the data files' modification times instead.
"""

from __future__ import annotations

import os
from pathlib import Path

from mashbill.folder_io import create_node, create_project, read_canvas, update_node
from mashbill.models import ProjectDoc
from mashbill.workspace import discover_projects, resolve_plot_root


def _setup(tmp_path: Path) -> Path:
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    return plot_root


def test_editing_a_canvas_leaves_project_json_untouched(tmp_path: Path) -> None:
    plot_root = _setup(tmp_path)
    project_file = plot_root / "project.json"
    before = project_file.read_bytes()

    created = create_node(plot_root, "alpha", "foundation", "mission", {"label": "First"})
    node_id = created["node"]["id"]
    update_node(plot_root, "alpha", "foundation", node_id, {"label": "Second"})

    assert read_canvas(plot_root, "alpha", "foundation").nodes[0].label == "Second"
    assert project_file.read_bytes() == before, "a canvas edit rewrote project.json"


def _project(
    workspace_root: Path, reldir: str, proj_id: str, updated: str, edited_at: float
) -> None:
    data = workspace_root / reldir / ".noory" / "novel"
    (data / "foundation").mkdir(parents=True, exist_ok=True)
    (data / "project.json").write_text(
        ProjectDoc(id=proj_id, name=proj_id, updated=updated).model_dump_json()
    )
    canvas = data / "foundation" / "canvas.json"
    canvas.write_text(
        '{"canvas_id": "foundation", "canvas_kind": "foundation", "nodes": [], "edges": []}'
    )
    os.utime(data / "project.json", (edited_at, edited_at))
    os.utime(canvas, (edited_at, edited_at))


def test_project_list_puts_the_most_recently_edited_project_first(tmp_path: Path) -> None:
    # Same stored ``updated``; only B's canvas was edited recently.
    _project(
        tmp_path, "a", "proj-a", "2026-01-01T00:00:00+00:00", edited_at=1_767_225_600
    )  # 2026-01-01
    _project(
        tmp_path, "b", "proj-b", "2026-01-01T00:00:00+00:00", edited_at=1_780_000_000
    )  # 2026-05-28
    assert [p.id for p, _ in discover_projects(tmp_path)] == ["proj-b", "proj-a"]
