"""Atomic blueprint publication across format F, project metadata, and git."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from mashbill.blueprint_content import blueprint_content_fingerprint
from mashbill.folder_io import _project_dir, read_project, write_project
from mashbill.format_f import publish_project_snapshot, remove_project_snapshot
from mashbill.format_f_slugs import read_slug_store_bytes, restore_slug_store
from mashbill.git_store import (
    TagAlreadyExistsError,
    blueprint_canvas_changed,
    tag_exists,
    tag_snapshot,
)
from mashbill.tag_names import is_blueprint_version_tag
from mashbill.workspace import workspace_root_from_plot_root


class BlueprintUnchangedError(ValueError):
    """Raised when the canvas matches the current blueprint-version tag."""

    def __init__(self, from_version: str) -> None:
        self.from_version = from_version
        super().__init__(f"blueprint is unchanged since {from_version}")


def _bump_blueprint_version(current: str, bump: str) -> str:
    """Bump ``v<MAJOR>.<MINOR>.<PATCH>`` per the selected level."""
    if not current.startswith("v"):
        raise ValueError(f"invalid blueprint version (must start with 'v'): {current!r}")
    parts = current[1:].split(".")
    if not is_blueprint_version_tag(current):
        raise ValueError(f"invalid semver (need v<MAJOR>.<MINOR>.<PATCH>): {current!r}")
    major, minor, patch = (int(part) for part in parts)
    if bump == "major":
        return f"v{major + 1}.0.0"
    if bump == "minor":
        return f"v{major}.{minor + 1}.0"
    if bump == "patch":
        return f"v{major}.{minor}.{patch + 1}"
    raise ValueError(f"bump must be one of major/minor/patch, got {bump!r}")


def publish_blueprint(
    plot_root: Path,
    project_id: str,
    bump: str,
    message: str | None = None,
    slugs: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Publish one blueprint version as a format-F snapshot and git tag."""
    project = read_project(plot_root, project_id)
    from_version = project.blueprint_version
    to_version = _bump_blueprint_version(from_version, bump)
    project_dir = _project_dir(plot_root, project_id)
    workspace_root = workspace_root_from_plot_root(plot_root)

    if not blueprint_canvas_changed(workspace_root, project_dir, from_version):
        raise BlueprintUnchangedError(from_version)
    if tag_exists(workspace_root, to_version):
        raise TagAlreadyExistsError(f"tag already exists: {to_version!r}")

    previous_slug_store = read_slug_store_bytes(plot_root, project_id)
    manifest = publish_project_snapshot(
        plot_root,
        project_id,
        blueprint_version=to_version,
        slugs=slugs,
    )
    release = str(manifest["release"])
    bumped = project.model_copy(update={"blueprint_version": to_version})
    try:
        write_project(plot_root, bumped)
        tag_message = message or to_version
        fingerprint = blueprint_content_fingerprint(workspace_root, project_dir)
        if fingerprint is not None:
            tag_message = f"{tag_message}\n\nNovel-Blueprint-Content: sha256:{fingerprint}"
        tag = tag_snapshot(workspace_root, to_version, message=tag_message)
    except Exception as exc:
        try:
            write_project(plot_root, project)
        except Exception as rollback_exc:
            exc.add_note(f"project rollback failed: {rollback_exc}")
        finally:
            remove_project_snapshot(plot_root, project_id, release)
            try:
                restore_slug_store(plot_root, project_id, previous_slug_store)
            except Exception as rollback_exc:
                exc.add_note(f"slug store rollback failed: {rollback_exc}")
        raise

    return {
        "from_version": from_version,
        "to_version": to_version,
        "tag": tag,
        "manifest": manifest,
    }
