"""R9 — `.solera/` consolidates under `.noory/solera/` (overhaul Track 2.3).

Same shape as the plot/evonest migrations: resolver prefers the new
`.noory/solera/` location, lazily migrates a legacy `.solera/` on first
access, and preserves both when both exist (no blind merge). The migration
also carries the user's `.gitignore` intent — a project that ignored
`.solera/` keeps ignoring the data after the move.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from solera_mcp.workspace import resolve_solera_root


def _seed(workspace: Path) -> None:
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "concepts").mkdir(exist_ok=True)


def test_prefers_noory_solera_when_present(tmp_path: Path) -> None:
    new_root = tmp_path / ".noory" / "solera"
    _seed(new_root)
    resolved = resolve_solera_root(str(tmp_path))
    assert resolved == new_root.resolve()


def test_migrates_legacy_dotsolera_to_noory_solera(tmp_path: Path) -> None:
    legacy = tmp_path / ".solera"
    _seed(legacy)
    (legacy / "concepts" / "marker.md").write_text("legacy data")

    resolved = resolve_solera_root(str(tmp_path))
    new_root = tmp_path / ".noory" / "solera"
    assert resolved == new_root.resolve()
    assert (new_root / "concepts" / "marker.md").read_text() == "legacy data"
    assert not legacy.exists(), "legacy directory should be moved, not copied"


def test_both_roots_present_new_wins_legacy_preserved(tmp_path: Path) -> None:
    """Half-migrated / user-restored: never merge blindly. New wins, legacy stays."""
    new_root = tmp_path / ".noory" / "solera"
    legacy = tmp_path / ".solera"
    _seed(new_root)
    _seed(legacy)
    (legacy / "concepts" / "legacy.md").write_text("legacy")
    (new_root / "concepts" / "new.md").write_text("new")

    resolved = resolve_solera_root(str(tmp_path))
    assert resolved == new_root.resolve()
    assert legacy.is_dir(), "legacy preserved when new already exists (no clobber)"
    assert (legacy / "concepts" / "legacy.md").exists()


def test_migration_carries_gitignore_intent(tmp_path: Path) -> None:
    """A project that ignored `.solera/` must keep ignoring the data after
    the move — otherwise the next blanket `git add` silently tracks runtime
    data (the evonest v1.1.1 dogfood incident)."""
    legacy = tmp_path / ".solera"
    _seed(legacy)
    (tmp_path / ".gitignore").write_text(
        "node_modules/\n.solera/\n*.log\n", encoding="utf-8"
    )

    resolve_solera_root(str(tmp_path))

    contents = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert ".noory/solera/" in contents, (
        "migration must append .noory/solera/ to .gitignore when the legacy "
        ".solera/ entry was present"
    )


def test_migration_does_not_invent_gitignore_for_tracked_projects(tmp_path: Path) -> None:
    """If the project tracked `.solera/` on purpose (no ignore entry), the
    migration must not invent ignore policy."""
    legacy = tmp_path / ".solera"
    _seed(legacy)
    (tmp_path / ".gitignore").write_text("node_modules/\n*.log\n", encoding="utf-8")

    resolve_solera_root(str(tmp_path))

    contents = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert ".noory/solera/" not in contents


def test_no_gitignore_file_no_op(tmp_path: Path) -> None:
    """Projects without a `.gitignore` get no file created."""
    legacy = tmp_path / ".solera"
    _seed(legacy)
    resolve_solera_root(str(tmp_path))
    assert not (tmp_path / ".gitignore").exists()


def test_v3_workspace_still_resolves_unchanged(tmp_path: Path) -> None:
    """The v3 `workspace/` fallback is independent of R9; it must keep
    resolving (deprecated warning), with no migration triggered."""
    v3 = tmp_path / "workspace"
    _seed(v3)
    resolved = resolve_solera_root(str(tmp_path))
    assert resolved == v3.resolve()
    assert not (tmp_path / ".noory").exists()


def test_no_workspace_anywhere_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        resolve_solera_root(str(tmp_path))
