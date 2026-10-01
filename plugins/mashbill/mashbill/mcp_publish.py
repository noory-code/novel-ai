"""Human-approved publication adapters for the Mashbill MCP surface."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from mashbill.blueprint_publish import BlueprintUnchangedError, publish_blueprint
from mashbill.git_store import GitNotInitializedError, TagAlreadyExistsError


def publish_blueprint_for_person(
    plot_root: Path,
    project_id: str,
    bump: Literal["major", "minor", "patch"],
    message: str | None,
    workspace_root: Path,
    slugs: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Translate blueprint publication failures into MCP-facing values."""
    try:
        return publish_blueprint(plot_root, project_id, bump, message=message, slugs=slugs)
    except GitNotInitializedError as exc:
        raise ValueError(
            f"git not initialized at workspace root {workspace_root}. "
            "Open the workspace in the viewer and accept the 'Initialize "
            "git repo' prompt, or run `git init` there manually."
        ) from exc
    except (BlueprintUnchangedError, TagAlreadyExistsError) as exc:
        raise ValueError(str(exc)) from exc
