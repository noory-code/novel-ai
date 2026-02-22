"""Path resolution for knowledge storage."""

from __future__ import annotations

from pathlib import Path

from distill.store.types import KnowledgeScope

GLOBAL_DIR = Path.home() / ".distill" / "knowledge"
PROJECT_SUBDIR = ".distill"

# Markers that indicate a package/app root (nearest wins for project scope)
PROJECT_MARKERS = ["pyproject.toml", "pubspec.yaml", "package.json", "CLAUDE.md"]


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
        path = Path(workspace_root) / PROJECT_SUBDIR / "knowledge"
        path.mkdir(parents=True, exist_ok=True)
        return path

    # project
    if not project_root:
        raise ValueError("project scope requires project_root")

    path = Path(project_root) / PROJECT_SUBDIR / "knowledge"
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

    directory = Path(cwd or os.getcwd())
    while True:
        if any((directory / m).exists() for m in PROJECT_MARKERS):
            return str(directory)
        parent = directory.parent
        if parent == directory:  # filesystem root
            return None
        directory = parent


def detect_workspace_root(cwd: str | None = None) -> str | None:
    """Detect monorepo root by walking up from CWD looking for .git.

    Returns the directory containing .git (the monorepo/workspace root).
    """
    import os

    directory = Path(cwd or os.getcwd())
    while True:
        if (directory / ".git").exists():
            return str(directory)
        parent = directory.parent
        if parent == directory:  # filesystem root
            return None
        directory = parent
