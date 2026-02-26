"""Path resolution for knowledge storage."""

from __future__ import annotations

from pathlib import Path

from distill.store.types import KnowledgeScope

GLOBAL_DIR = Path.home() / ".distill" / "knowledge"
PROJECT_SUBDIR = ".distill"

# Markers that indicate a package/app root (nearest wins for project scope)
PROJECT_MARKERS = ["pyproject.toml", "pubspec.yaml", "package.json", "CLAUDE.md"]


def _walk_up_to_marker(start: Path, marker: str | list[str]) -> Path | None:
    """주어진 마커를 포함하는 디렉토리를 찾아 상위로 이동.

    Args:
        start: 탐색 시작 경로
        marker: 찾을 마커 파일/디렉토리 이름 또는 마커 목록

    Returns:
        마커를 포함하는 디렉토리 또는 None
    """
    directory = start.resolve()
    markers = [marker] if isinstance(marker, str) else marker

    while True:
        if any((directory / m).exists() for m in markers):
            return directory
        parent = directory.parent
        if parent == directory:  # 파일시스템 루트
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
