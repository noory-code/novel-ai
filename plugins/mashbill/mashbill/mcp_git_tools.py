"""MCP-callable git session tag operations."""

from __future__ import annotations

from typing import Any

from mashbill.git_store import (
    GitNotInitializedError,
    TagAlreadyExistsError,
    delete_tag,
    list_tags,
    tag_session,
)
from mashbill.workspace import resolve_plot_root, workspace_root_from_plot_root


def tag_project(
    project_path: str,
    project_id: str,
    name: str,
    message: str | None = None,
) -> dict[str, Any]:
    """Plant a named git tag at the current state of the project. Use this
    at the start or end of a work session ("session-banas-start",
    "before-refactor") — day-to-day edits don't commit, only tags do."""
    plot_root = resolve_plot_root(project_path)
    workspace_root = workspace_root_from_plot_root(plot_root)
    try:
        # D-2026-06-11-C/D — git lives at the workspace root. The tag
        # snapshots `.noory/novel/` inside that repo, not a single project.
        # project_id is kept on the tool signature for call-site clarity
        # and future per-project naming.
        return tag_session(workspace_root, name, message=message)
    except GitNotInitializedError as exc:
        raise ValueError(
            f"git not initialized at workspace root {workspace_root}. "
            "Open the workspace in the viewer and accept the 'Initialize "
            "git repo' prompt, or run `git init` there manually."
        ) from exc
    except TagAlreadyExistsError as exc:
        raise ValueError(str(exc)) from exc


def list_project_tags(project_path: str, project_id: str) -> list[dict[str, Any]]:
    """Return tags for a project, newest first."""
    plot_root = resolve_plot_root(project_path)
    return list_tags(workspace_root_from_plot_root(plot_root))


def delete_project_tag(project_path: str, project_id: str, name: str) -> str:
    """Drop a tag from a project. The commit it pointed at stays reachable.

    Published blueprint version tags cannot be deleted.
    """
    plot_root = resolve_plot_root(project_path)
    try:
        delete_tag(workspace_root_from_plot_root(plot_root), name)
    except KeyError as exc:
        raise ValueError(f"tag not found: {exc.args[0]}") from exc
    return f"deleted tag {name}"
