"""Atomic blueprint publication: format-F snapshot, version, commit, and tag."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from mashbill.folder_io import _project_dir, create_project, read_project
from mashbill.git_store import (
    GitNotInitializedError,
    TagAlreadyExistsError,
    init_workspace_repo,
    tag_snapshot,
)
from mashbill.workspace import resolve_plot_root


@pytest.fixture
def project(tmp_path: Path) -> tuple[Path, Path]:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    plot_root = resolve_plot_root(str(workspace))
    create_project(plot_root, "alpha", "Alpha")
    return workspace, plot_root


def _snapshot_dir(plot_root: Path, release: str = "vP1") -> Path:
    return _project_dir(plot_root, "alpha") / "published" / "_project" / release


def test_publish_blueprint_commits_snapshot_bumps_version_and_tags(
    project: tuple[Path, Path],
) -> None:
    from mashbill.blueprint_publish import publish_blueprint

    workspace, plot_root = project
    init_workspace_repo(workspace)

    result = publish_blueprint(plot_root, "alpha", "patch")

    assert result["from_version"] == "v0.1.0"
    assert result["to_version"] == "v0.1.1"
    assert result["tag"]["name"] == "v0.1.1"
    assert result["manifest"]["release"] == "vP1"
    assert result["manifest"]["blueprint_version"] == "v0.1.1"
    assert read_project(plot_root, "alpha").blueprint_version == "v0.1.1"

    manifest_path = _snapshot_dir(plot_root) / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["blueprint_version"] == "v0.1.1"
    tagged_paths = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", "v0.1.1"],
        cwd=workspace,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    assert str(manifest_path.relative_to(workspace)) in tagged_paths


def test_publish_blueprint_rolls_back_snapshot_when_format_f_write_fails(
    project: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    import mashbill.format_f as format_f
    from mashbill.blueprint_publish import publish_blueprint

    workspace, plot_root = project
    init_workspace_repo(workspace)

    def fail_read(*_args: object, **_kwargs: object) -> object:
        raise RuntimeError("read failed")

    monkeypatch.setattr(format_f, "read_canvas", fail_read)

    with pytest.raises(RuntimeError, match="read failed"):
        publish_blueprint(plot_root, "alpha", "patch")

    assert not _snapshot_dir(plot_root).exists()
    assert read_project(plot_root, "alpha").blueprint_version == "v0.1.0"
    assert (
        subprocess.run(
            ["git", "tag", "--list", "v0.1.1"],
            cwd=workspace,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        == ""
    )


def test_publish_blueprint_rolls_back_version_and_snapshot_when_tagging_fails(
    project: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    import mashbill.blueprint_publish as blueprint_publish

    workspace, plot_root = project
    init_workspace_repo(workspace)
    monkeypatch.setattr(
        blueprint_publish,
        "tag_snapshot",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("tag failed")),
    )

    with pytest.raises(RuntimeError, match="tag failed"):
        blueprint_publish.publish_blueprint(plot_root, "alpha", "patch")

    assert not _snapshot_dir(plot_root).exists()
    assert read_project(plot_root, "alpha").blueprint_version == "v0.1.0"


def test_publish_blueprint_rejects_existing_target_tag_before_writing(
    project: tuple[Path, Path],
) -> None:
    from mashbill.blueprint_publish import publish_blueprint

    workspace, plot_root = project
    init_workspace_repo(workspace)
    tag_snapshot(workspace, "v0.1.1", message="already there")

    with pytest.raises(TagAlreadyExistsError, match="tag already exists"):
        publish_blueprint(plot_root, "alpha", "patch")

    assert not _snapshot_dir(plot_root).exists()
    assert read_project(plot_root, "alpha").blueprint_version == "v0.1.0"


def test_publish_blueprint_rejects_unchanged_canvas_before_writing(
    project: tuple[Path, Path],
) -> None:
    from mashbill.blueprint_content import blueprint_content_fingerprint
    from mashbill.blueprint_publish import BlueprintUnchangedError, publish_blueprint

    workspace, plot_root = project
    init_workspace_repo(workspace)
    project_dir = _project_dir(plot_root, "alpha")
    fingerprint = blueprint_content_fingerprint(workspace, project_dir)
    assert fingerprint is not None
    tag_snapshot(
        workspace,
        "v0.1.0",
        message=f"baseline\n\nNovel-Blueprint-Content: sha256:{fingerprint}",
    )

    with pytest.raises(BlueprintUnchangedError, match="v0.1.0") as caught:
        publish_blueprint(plot_root, "alpha", "patch")

    assert caught.value.from_version == "v0.1.0"
    assert not _snapshot_dir(plot_root).exists()
    assert read_project(plot_root, "alpha").blueprint_version == "v0.1.0"


def test_publish_blueprint_requires_git_before_writing(
    project: tuple[Path, Path],
) -> None:
    from mashbill.blueprint_publish import publish_blueprint

    _workspace, plot_root = project

    with pytest.raises(GitNotInitializedError):
        publish_blueprint(plot_root, "alpha", "patch")

    assert not _snapshot_dir(plot_root).exists()
    assert read_project(plot_root, "alpha").blueprint_version == "v0.1.0"
