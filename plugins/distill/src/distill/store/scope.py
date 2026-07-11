"""Path resolution for knowledge storage."""

from __future__ import annotations

import shutil
from pathlib import Path

from distill.store.types import KnowledgeScope

# The GLOBAL tier stays at ~/.distill — pinned in the noory-ai overhaul (R9):
# only per-project / per-workspace artifacts consolidate under `.noory/`.
GLOBAL_DIR = Path.home() / ".distill" / "knowledge"
# R9: local tiers live under `<root>/.noory/distill/` (was `<root>/.distill/`).
LEGACY_PROJECT_SUBDIR = ".distill"
PROJECT_SUBDIR = str(Path(".noory") / "distill")


def local_data_root(root: Path, *, create: bool = True) -> Path:
    """Resolve `<root>/.noory/distill/`, lazily migrating a legacy
    `<root>/.distill/` (one move, same volume — config.json and knowledge/
    travel together). If BOTH exist, the new root wins and the legacy dir is
    preserved for the user to reconcile — never merged blindly. The global
    `~/.distill` tier is NOT handled here (it does not move).

    ``create=False`` is the READ path (config loading): it still migrates a
    legacy dir when one exists, but never creates directories — loading
    config from a root that has no distill data must stay side-effect-free
    (and must not crash on a nonexistent root)."""
    new_root = root / ".noory" / "distill"
    legacy = root / LEGACY_PROJECT_SUBDIR
    if legacy.is_dir() and not new_root.exists():
        new_root.parent.mkdir(exist_ok=True)
        shutil.move(str(legacy), str(new_root))
    if create:
        new_root.mkdir(parents=True, exist_ok=True)
    return new_root

# Markers that indicate a package/app root (nearest wins for project scope)
PROJECT_MARKERS = ["pyproject.toml", "pubspec.yaml", "package.json", "CLAUDE.md"]


def _walk_up_to_marker(start: Path, marker: str | list[str]) -> Path | None:
    """Walk up the directory tree to find a directory containing the given marker.

    Args:
        start: Starting path for the search
        marker: Marker file/directory name or list of marker names to look for

    Returns:
        Directory containing the marker, or None
    """
    directory = start.resolve()
    markers = [marker] if isinstance(marker, str) else marker

    while True:
        if any((directory / m).exists() for m in markers):
            return directory
        parent = directory.parent
        if parent == directory:  # filesystem root
            return None
        directory = parent


def resolve_store_path(
    scope: KnowledgeScope,
    project_root: str | None = None,
    workspace_root: str | None = None,
) -> Path:
    """Resolve the storage directory for a given scope."""
    if scope == "global":
        GLOBAL_DIR.mkdir(parents=True, exist_ok=True)
        return GLOBAL_DIR

    if scope == "workspace":
        if not workspace_root:
            raise ValueError("workspace scope requires workspace_root")
        path = local_data_root(Path(workspace_root)) / "knowledge"
        path.mkdir(parents=True, exist_ok=True)
        return path

    # project
    if not project_root:
        raise ValueError("project scope requires project_root")

    path = local_data_root(Path(project_root)) / "knowledge"
    path.mkdir(parents=True, exist_ok=True)
    return path


def resolve_db_path(
    scope: KnowledgeScope,
    project_root: str | None = None,
    workspace_root: str | None = None,
) -> Path:
    """Get the SQLite database path for a scope."""
    return resolve_store_path(scope, project_root, workspace_root) / "metadata.db"


def detect_project_root(cwd: str | None = None) -> str | None:
    """Detect nearest package/app root by walking up from CWD.

    Looks for: pyproject.toml, pubspec.yaml, package.json, CLAUDE.md
    Returns the nearest directory containing any of these markers.
    """
    import os

    start = Path(cwd or os.getcwd())
    result = _walk_up_to_marker(start, PROJECT_MARKERS)
    return str(result) if result else None


def detect_workspace_root(cwd: str | None = None) -> str | None:
    """Detect monorepo root by walking up from CWD looking for .git.

    Returns the directory containing .git (the monorepo/workspace root).
    """
    import os

    start = Path(cwd or os.getcwd())
    result = _walk_up_to_marker(start, ".git")
    return str(result) if result else None
