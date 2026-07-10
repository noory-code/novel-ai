"""R9 — distill's local tiers live under `.noory/distill/` (noory-ai overhaul).

The workspace and project tiers move from `<root>/.distill/` to
`<root>/.noory/distill/` so every plugin's per-project artifacts share ONE
`.noory/` dotfolder. A legacy `.distill/` dir is migrated lazily on first
access (one move; if both exist the new root wins and legacy is preserved).
The GLOBAL tier (`~/.distill/`) does NOT move — pinned in the overhaul.
"""

from __future__ import annotations

from pathlib import Path

from distill.store.scope import GLOBAL_DIR, local_data_root, resolve_store_path


def test_project_store_lives_under_noory(tmp_path: Path) -> None:
    path = resolve_store_path("project", project_root=str(tmp_path))
    assert path == tmp_path / ".noory" / "distill" / "knowledge"
    assert path.is_dir()


def test_workspace_store_lives_under_noory(tmp_path: Path) -> None:
    path = resolve_store_path("workspace", workspace_root=str(tmp_path))
    assert path == tmp_path / ".noory" / "distill" / "knowledge"


def test_global_tier_does_not_move() -> None:
    assert GLOBAL_DIR == Path.home() / ".distill" / "knowledge"


def test_legacy_dot_distill_migrates_on_first_access(tmp_path: Path) -> None:
    legacy = tmp_path / ".distill"
    (legacy / "knowledge").mkdir(parents=True)
    (legacy / "config.json").write_text("{}", encoding="utf-8")
    (legacy / "knowledge" / "meta.db").write_text("x", encoding="utf-8")

    root = local_data_root(tmp_path)

    assert root == tmp_path / ".noory" / "distill"
    assert (root / "knowledge" / "meta.db").is_file()
    assert (root / "config.json").is_file(), "config travels with the move"
    assert not legacy.exists(), "legacy .distill must be moved, not copied"


def test_legacy_migration_never_clobbers_existing_noory(tmp_path: Path) -> None:
    (tmp_path / ".distill" / "knowledge").mkdir(parents=True)
    (tmp_path / ".noory" / "distill" / "knowledge").mkdir(parents=True)

    root = local_data_root(tmp_path)

    assert root == tmp_path / ".noory" / "distill"
    assert (tmp_path / ".distill").is_dir(), "must not destroy legacy data"
