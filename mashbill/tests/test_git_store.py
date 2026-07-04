"""Per-workspace git repo for session-bookmark tags.

D-2026-06-11-C/D — git lives at the workspace root (the user's opened
folder), and Novel never silently runs `git init`. Identity is passed inline
on each commit (`git -c user.name=Novel …`) so the user's repo-level config
stays untouched. Novel's tag/publish commits stage only `.noory/novel/`.

These tests exercise `git_store` directly with workspace-root semantics.
The fixture sets up a real `.noory/novel/` folder under the workspace so
the path-scoped staging produces non-empty commits where relevant.
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

import pytest

from mashbill.git_store import (
    GitNotInitializedError,
    TagAlreadyExistsError,
    delete_tag,
    init_workspace_repo,
    is_workspace_repo,
    list_tags,
    tag_snapshot,
)


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    """A workspace root with `.noory/novel/{project}/` already populated so
    `git add -- .noory/novel/` has something to stage."""
    ws = tmp_path / "alpha"
    ws.mkdir()
    proj = ws / ".noory" / "novel" / "proj-a"
    proj.mkdir(parents=True)
    (proj / "project.json").write_text('{"id":"proj-a"}', encoding="utf-8")
    return ws


# ---------------------------------------------------------------------------
# init_workspace_repo + is_workspace_repo
# ---------------------------------------------------------------------------


def test_init_workspace_repo_creates_dotgit(workspace: Path) -> None:
    created = init_workspace_repo(workspace)
    assert created is True
    assert (workspace / ".git").is_dir()


def test_init_workspace_repo_is_idempotent(workspace: Path) -> None:
    init_workspace_repo(workspace)
    # Second call is a no-op success — returns False (nothing created).
    created2 = init_workspace_repo(workspace)
    assert created2 is False
    assert (workspace / ".git").is_dir()


def test_init_does_not_write_gitignore_or_gitattributes(workspace: Path) -> None:
    """Novel's territory is .noory/novel/, not the workspace root. Init must
    not write user-territory files (D-2026-06-11-D)."""
    init_workspace_repo(workspace)
    assert not (workspace / ".gitignore").exists()
    assert not (workspace / ".gitattributes").exists()


def test_init_does_not_set_local_user_config(workspace: Path) -> None:
    """No repo-level `user.name` / `user.email` writes — Novel uses inline
    identity per commit instead."""
    init_workspace_repo(workspace)
    name = subprocess.run(
        ["git", "config", "--local", "--get", "user.name"],
        cwd=workspace,
        capture_output=True,
        text=True,
    )
    assert name.returncode != 0 or not name.stdout.strip()


def test_is_workspace_repo_distinguishes_init_state(workspace: Path) -> None:
    assert is_workspace_repo(workspace) is False
    init_workspace_repo(workspace)
    assert is_workspace_repo(workspace) is True


# ---------------------------------------------------------------------------
# tag_snapshot
# ---------------------------------------------------------------------------


def test_tag_snapshot_raises_when_not_initialized(workspace: Path) -> None:
    with pytest.raises(GitNotInitializedError):
        tag_snapshot(workspace, "session-start")


def test_tag_snapshot_creates_commit_and_tag(workspace: Path) -> None:
    init_workspace_repo(workspace)
    result = tag_snapshot(workspace, "session-start")
    assert result["name"] == "session-start"
    assert isinstance(result["sha"], str) and len(result["sha"]) == 40
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=workspace,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert head == result["sha"]


def test_tag_snapshot_uses_inline_plot_identity(workspace: Path) -> None:
    """Novel's commit is authored as `Novel <plot@noory-ai.local>` regardless
    of repo / global config, because identity is passed inline."""
    init_workspace_repo(workspace)
    tag_snapshot(workspace, "v1")
    author = subprocess.run(
        ["git", "log", "-1", "--format=%an %ae"],
        cwd=workspace,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert author == "Novel plot@noory-ai.local"


def test_tag_snapshot_uses_message_when_given(workspace: Path) -> None:
    init_workspace_repo(workspace)
    tag_snapshot(workspace, "milestone-1", message="before BANAS refactor")
    msg = subprocess.run(
        ["git", "log", "-1", "--pretty=%s"],
        cwd=workspace,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert msg == "before BANAS refactor"


def test_tag_snapshot_duplicate_name_rejected(workspace: Path) -> None:
    init_workspace_repo(workspace)
    tag_snapshot(workspace, "dup")
    with pytest.raises(TagAlreadyExistsError):
        tag_snapshot(workspace, "dup")


def test_tag_snapshot_captures_latest_plot_data(workspace: Path) -> None:
    """Each snapshot reflects the on-disk state of .noory/novel/ at tag time."""
    init_workspace_repo(workspace)
    target = workspace / ".noory" / "novel" / "proj-a" / "project.json"
    target.write_text('{"id":"proj-a","v":1}', encoding="utf-8")
    tag_snapshot(workspace, "v1")
    target.write_text('{"id":"proj-a","v":2}', encoding="utf-8")
    tag_snapshot(workspace, "v2")
    blob = subprocess.run(
        ["git", "show", "v1:.noory/novel/proj-a/project.json"],
        cwd=workspace,
        capture_output=True,
        text=True,
    ).stdout
    assert '"v":1' in blob


def test_tag_snapshot_only_stages_noory_plot(workspace: Path) -> None:
    """Files outside .noory/novel/ stay untracked across a Novel tag."""
    init_workspace_repo(workspace)
    user_file = workspace / "user_notes.md"
    user_file.write_text("user's own working-tree", encoding="utf-8")
    tag_snapshot(workspace, "v1")
    status = subprocess.run(
        ["git", "status", "--porcelain", "user_notes.md"],
        cwd=workspace,
        capture_output=True,
        text=True,
    ).stdout
    assert "user_notes.md" in status, f"expected user_notes.md untracked, got status={status!r}"


def test_tag_snapshot_with_no_changes_still_tags(workspace: Path) -> None:
    """Back-to-back tags on an unchanged tree still produce a second tag
    (pointing at a no-op commit). Needed for "end-of-session" markers."""
    init_workspace_repo(workspace)
    tag_snapshot(workspace, "a")
    tag_snapshot(workspace, "b")
    tags = {t["name"] for t in list_tags(workspace)}
    assert {"a", "b"} <= tags


# ---------------------------------------------------------------------------
# list_tags / delete_tag
# ---------------------------------------------------------------------------


def test_list_tags_empty_on_uninitialized_workspace(workspace: Path) -> None:
    """No `.git/` → no tags possible → empty list (not an error)."""
    assert list_tags(workspace) == []


def test_list_tags_empty_on_fresh_repo(workspace: Path) -> None:
    init_workspace_repo(workspace)
    assert list_tags(workspace) == []


def test_list_tags_newest_first(workspace: Path) -> None:
    """Sort precision is 1s (git's own resolution); the test spaces
    the two tags by just over a second so the ordering is well-defined."""
    init_workspace_repo(workspace)
    tag_snapshot(workspace, "first")
    time.sleep(1.1)
    tag_snapshot(workspace, "second")
    tags = list_tags(workspace)
    assert [t["name"] for t in tags] == ["second", "first"]


def test_list_tags_returns_sha_and_message(workspace: Path) -> None:
    init_workspace_repo(workspace)
    tag_snapshot(workspace, "m1", message="first milestone")
    (tag,) = list_tags(workspace)
    assert tag["name"] == "m1"
    assert isinstance(tag["sha"], str) and len(tag["sha"]) == 40
    assert tag["message"] == "first milestone"
    assert tag["ts"]  # ISO timestamp, non-empty


def test_delete_tag_removes_tag_only(workspace: Path) -> None:
    init_workspace_repo(workspace)
    tag_snapshot(workspace, "doomed")
    delete_tag(workspace, "doomed")
    assert list_tags(workspace) == []
    # But the commit it pointed at is still reachable via reflog.
    reflog = subprocess.run(
        ["git", "reflog", "--all"],
        cwd=workspace,
        capture_output=True,
        text=True,
    ).stdout
    assert reflog  # non-empty


def test_delete_unknown_tag_raises(workspace: Path) -> None:
    init_workspace_repo(workspace)
    with pytest.raises(KeyError):
        delete_tag(workspace, "never-existed")


def test_delete_tag_on_uninitialized_workspace_raises(workspace: Path) -> None:
    """No `.git/` → no tag named anything → KeyError."""
    with pytest.raises(KeyError):
        delete_tag(workspace, "anything")
