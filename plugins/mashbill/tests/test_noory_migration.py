"""R9 — plugin artifacts live under `<project>/.noory/novel/` (D-2026-06-10-G).

OVERHAUL R9: every plugin's per-project output consolidates under ONE
`.noory/` dotfolder (`.noory/novel/`, `.noory/distill/`, …) so plugin mode and
app mode share artifacts continuously. The legacy `.plot/` root is migrated
lazily on first access (one `shutil.move`, same volume).
"""

from __future__ import annotations

from pathlib import Path

from mashbill.project_io import create_project
from mashbill.workspace import discover_projects, resolve_plot_root


def test_plot_root_lives_under_noory(tmp_path: Path) -> None:
    root = resolve_plot_root(str(tmp_path))
    assert root == tmp_path / ".noory" / "novel"
    assert root.is_dir()


def test_legacy_dot_plot_migrates_on_first_access(tmp_path: Path) -> None:
    """A pre-R9 workspace (`.plot/proj-x`) is moved wholesale to `.noory/novel`
    the first time the engine touches it, then flattened (S2) since it holds a
    single project — so `project.json` lands directly under the root."""
    legacy = tmp_path / ".plot"
    legacy.mkdir()
    (legacy / "proj-x").mkdir()
    (legacy / "proj-x" / "project.json").write_text(
        '{"id": "proj-x", "name": "X", "version": 3}', encoding="utf-8"
    )

    root = resolve_plot_root(str(tmp_path))

    assert root == tmp_path / ".noory" / "novel"
    assert (root / "project.json").is_file()
    assert not (root / "proj-x").exists()
    assert not legacy.exists(), "legacy .plot must be moved, not copied"


def test_legacy_migration_never_clobbers_existing_noory(tmp_path: Path) -> None:
    """If BOTH exist (half-migrated / user-restored), .noory/novel wins and
    .plot is left untouched for the user to reconcile — never merged blindly."""
    (tmp_path / ".plot" / "proj-old").mkdir(parents=True)
    (tmp_path / ".noory" / "novel" / "proj-new").mkdir(parents=True)

    root = resolve_plot_root(str(tmp_path))

    assert (root / "proj-new").is_dir()
    assert (tmp_path / ".plot" / "proj-old").is_dir(), "must not destroy legacy data"


def test_discovery_sees_noory_projects(tmp_path: Path) -> None:
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "proj-a", "A")
    found = discover_projects(Path(str(tmp_path)))
    assert [p.id for p, _rel in found] == ["proj-a"]


def test_discovery_sees_sibling_dir_projects(tmp_path: Path) -> None:
    """One-project-per-dir (D-2026-06-21-AA): two services live in sibling
    directories, each with its own `.noory/novel`. Recursive discovery still
    surfaces both — the guard is on the create *write* path, not on the
    discovery *read* path (S4 coherence)."""
    web = tmp_path / "apps" / "web"
    api = tmp_path / "services" / "api"
    web.mkdir(parents=True)
    api.mkdir(parents=True)
    create_project(resolve_plot_root(str(web)), "web", "Web")
    create_project(resolve_plot_root(str(api)), "api", "Api")
    found = discover_projects(Path(str(tmp_path)))
    assert {p.id for p, _rel in found} == {"web", "api"}
    assert {rel for _p, rel in found} == {"apps/web", "services/api"}


def test_discovery_sees_legacy_only_workspaces(tmp_path: Path) -> None:
    """A workspace that was never opened post-R9 still shows its projects in
    discovery (read-only peek at `.plot/`) — migration happens on open."""
    legacy = tmp_path / "sub" / ".plot" / "proj-l"
    legacy.mkdir(parents=True)
    (legacy / "project.json").write_text(
        '{"id": "proj-l", "name": "L", "version": 3}', encoding="utf-8"
    )
    found = discover_projects(Path(str(tmp_path)))
    assert [p.id for p, _rel in found] == ["proj-l"]


def test_resolve_flattens_single_nested_project(tmp_path: Path) -> None:
    """S2 (D-2026-06-21-AB): a legacy nested `.noory/novel/{id}/` project is
    migrated up to the root on open, so its files sit directly under
    `.noory/novel/`. The {id}/ folder is removed."""
    nested = tmp_path / ".noory" / "novel" / "alpha"
    (nested / "foundation").mkdir(parents=True)
    (nested / "project.json").write_text(
        '{"id": "alpha", "name": "Alpha", "version": 3}', encoding="utf-8"
    )
    (nested / "foundation" / "canvas.json").write_text(
        '{"canvas_id": "foundation", "canvas_kind": "foundation", "nodes": [], "edges": []}',
        encoding="utf-8",
    )
    root = resolve_plot_root(str(tmp_path))
    assert (root / "project.json").is_file()
    assert (root / "foundation" / "canvas.json").is_file()
    assert not (root / "alpha").exists()


def test_resolve_leaves_multiple_nested_projects_untouched(tmp_path: Path) -> None:
    """The forbidden stacking case (two projects under one root) is NOT
    auto-flattened — that would have to pick a winner. They are left in place
    for the user to reconcile (handoff S5); discovery still reads both."""
    plot_root = tmp_path / ".noory" / "novel"
    for pid in ("alpha", "beta"):
        d = plot_root / pid
        d.mkdir(parents=True)
        (d / "project.json").write_text(
            f'{{"id": "{pid}", "name": "{pid}", "version": 3}}', encoding="utf-8"
        )
    root = resolve_plot_root(str(tmp_path))
    assert (root / "alpha" / "project.json").is_file()
    assert (root / "beta" / "project.json").is_file()
    assert not (root / "project.json").exists()


def test_resolve_plot_root_guards_against_double_nesting(tmp_path: Path) -> None:
    """D-2026-06-21-W — passing a path that ALREADY points at a `.noory/novel`
    data root must NOT append another `.noory/novel`. Regression for the
    orphaned-project bug where an MCP caller produced
    `.noory/novel/.noory/novel/{id}` (invisible to discovery)."""
    data_root = tmp_path / ".noory" / "novel"
    data_root.mkdir(parents=True)
    resolved = resolve_plot_root(str(data_root))
    assert resolved == data_root
    # no second nesting created
    assert not (data_root / ".noory").exists()


def test_resolve_plot_root_double_nest_then_create_lands_correctly(
    tmp_path: Path,
) -> None:
    """A project created after resolving a `.noory/novel` path lands flat at
    `.noory/novel/project.json` (S2), not `.noory/novel/.noory/novel/{id}`."""
    data_root = tmp_path / ".noory" / "novel"
    data_root.mkdir(parents=True)
    root = resolve_plot_root(str(data_root))
    create_project(root, "banas", "Banas")
    assert (data_root / "project.json").is_file()
    assert not (data_root / ".noory").exists()
