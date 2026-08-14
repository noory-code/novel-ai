"""Workspace recursive discovery — v0.32.0 (D-2026-05-31-L).

`discover_projects(workspace_root)` walks the root for directories that
contain a `.plot/` and returns (ProjectDoc, relative_dir) for every valid
project — "." for a root-level project. Heavy / dot directories are pruned;
depth + count are capped.
"""

from __future__ import annotations

from pathlib import Path

from mashbill.models import ProjectDoc
from mashbill.workspace import MAX_DISCOVERY_DEPTH, discover_projects


def _make_project(
    workspace_root: Path, reldir: str, proj_id: str, name: str = "P", updated: str = ""
) -> None:
    base = workspace_root if reldir == "." else workspace_root / reldir
    pdir = base / ".plot" / proj_id
    pdir.mkdir(parents=True, exist_ok=True)
    doc = ProjectDoc(id=proj_id, name=name, updated=updated)
    (pdir / "project.json").write_text(doc.model_dump_json())


def _dirs(results: list[tuple[ProjectDoc, str]]) -> set[str]:
    return {d for _p, d in results}


def _ids(results: list[tuple[ProjectDoc, str]]) -> set[str]:
    return {p.id for p, _d in results}


def test_discovers_nested_projects(tmp_path: Path) -> None:
    _make_project(tmp_path, "a", "proj-a")
    _make_project(tmp_path, "b/c", "proj-bc")
    results = discover_projects(tmp_path)
    assert _ids(results) == {"proj-a", "proj-bc"}
    assert _dirs(results) == {"a", "b/c"}


def test_root_level_project_dir_is_dot(tmp_path: Path) -> None:
    _make_project(tmp_path, ".", "proj-root")
    results = discover_projects(tmp_path)
    assert results
    assert _dirs(results) == {"."}


def test_prunes_node_modules_and_dotdirs(tmp_path: Path) -> None:
    _make_project(tmp_path, "node_modules/pkg", "proj-nm")
    _make_project(tmp_path, ".hidden", "proj-dot")
    _make_project(tmp_path, "real", "proj-real")
    results = discover_projects(tmp_path)
    assert _ids(results) == {"proj-real"}


def test_depth_cap(tmp_path: Path) -> None:
    deep = "/".join(["d"] * (MAX_DISCOVERY_DEPTH + 2))
    _make_project(tmp_path, deep, "proj-deep")
    _make_project(tmp_path, "shallow", "proj-shallow")
    results = discover_projects(tmp_path)
    assert "proj-shallow" in _ids(results)
    assert "proj-deep" not in _ids(results)


def test_empty_workspace_returns_empty(tmp_path: Path) -> None:
    (tmp_path / "just" / "dirs").mkdir(parents=True)
    assert discover_projects(tmp_path) == []


def test_invalid_project_json_skipped(tmp_path: Path) -> None:
    _make_project(tmp_path, "a", "proj-good")
    bad = tmp_path / "a" / ".plot" / "proj-bad"
    bad.mkdir(parents=True)
    (bad / "project.json").write_text("{ not valid json")
    results = discover_projects(tmp_path)
    assert _ids(results) == {"proj-good"}


def test_dir_with_empty_plot_not_a_project(tmp_path: Path) -> None:
    (tmp_path / "x" / ".plot").mkdir(parents=True)
    assert discover_projects(tmp_path) == []


def test_results_sorted_newest_first(tmp_path: Path) -> None:
    _make_project(tmp_path, "old", "proj-old", updated="2020-01-01T00:00:00")
    _make_project(tmp_path, "new", "proj-new", updated="2026-01-01T00:00:00")
    results = discover_projects(tmp_path)
    assert [p.id for p, _ in results] == ["proj-new", "proj-old"]


# --- O-00000064: a folder git is told to ignore is not part of the work ------


def test_gitignored_folder_is_not_walked(tmp_path: Path) -> None:
    """A throwaway folder buries the real projects.

    This workspace keeps `playground/` for simulation runs — 379 of them turned
    up in the picker, so the root could not be opened in the app at all. The
    user already declared that folder disposable by gitignoring it; discovery
    now reads the same declaration.
    """
    (tmp_path / ".gitignore").write_text("playground/\n")
    _make_project(tmp_path, ".", "keep")
    _make_project(tmp_path, "playground/run-1", "throwaway")

    assert _dirs(discover_projects(tmp_path)) == {"."}


def test_gitignore_only_counts_at_the_workspace_root(tmp_path: Path) -> None:
    """A nested repo's ignores are its own business, not the workspace's."""
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / ".gitignore").write_text("kept/\n")
    _make_project(tmp_path, "sub/kept", "still-found")

    assert _dirs(discover_projects(tmp_path)) == {"sub/kept"}


def test_no_gitignore_changes_nothing(tmp_path: Path) -> None:
    _make_project(tmp_path, "a", "one")
    _make_project(tmp_path, "b", "two")

    assert _dirs(discover_projects(tmp_path)) == {"a", "b"}


def test_gitignore_patterns_that_are_not_folders_are_left_alone(tmp_path: Path) -> None:
    """Only whole-folder ignores prune a walk; `*.log` says nothing about dirs."""
    (tmp_path / ".gitignore").write_text("*.log\n!keep.log\n# a comment\n\n")
    _make_project(tmp_path, "a", "one")

    assert _dirs(discover_projects(tmp_path)) == {"a"}


def test_an_unreadable_gitignore_does_not_stop_discovery(tmp_path: Path) -> None:
    """A broken ignore file must not take the whole picker down."""
    (tmp_path / ".gitignore").write_bytes(b"\xff\xfe not text at all")
    _make_project(tmp_path, "a", "one")

    assert _dirs(discover_projects(tmp_path)) == {"a"}
