"""D-2026-06-11-C/D — git lives at the workspace root (the user's opened
folder), not inside `.noory/novel/`. And Novel never auto-creates `.git/` —
the first tag/publish on a workspace without a repo replies
`needs_git_init=true` and the user must explicitly confirm via
`POST /api/workspace/git-init`.

Supersedes D-2026-06-09-C (repo at `.noory/novel/`) — the workspace-singleton
half stays correct; the location flips up one level so non-Novel files in the
workspace become part of the same repo (user's choice via `.gitignore`).

This file pins:
  - `create_project` never silently runs `git init`.
  - First tag attempt on a workspace without `.git/` returns 409
    `needs_git_init`, and per-project `.git` is never created.
  - `POST /api/workspace/git-init` (idempotent) creates the workspace repo.
  - After consent, tag/at-tag/publish all target `<workspace>/.git`, and
    file paths inside the repo are `.noory/novel/{project_id}/…`.
  - When the workspace already has a user `.git/`, Novel reuses it and never
    touches `user.name` / `user.email` / `.gitignore`.
  - Legacy `.noory/novel/.git/` is migrated up to the workspace root when
    safe (no existing `.git/`).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from mashbill.folder_io import create_project
from mashbill.workspace import resolve_plot_root


def _workspace_root(plot_root: Path) -> Path:
    """`<workspace>/.noory/novel` → `<workspace>`."""
    return plot_root.parent.parent


def test_create_project_does_not_auto_init_git(tmp_path: Path) -> None:
    """D-2026-06-11-D: Novel never silently runs `git init`. Creating a
    project just resolves the data root; no `.git/` appears anywhere."""
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "proj-a", "A")
    assert not (tmp_path / ".git").exists()
    assert not (plot_root / ".git").exists()
    assert not (plot_root / "proj-a" / ".git").exists()


def test_tag_endpoint_returns_needs_git_init_when_no_repo(tmp_path: Path) -> None:
    """First tag attempt without a workspace repo must NOT silently init.
    It returns a structured 409 the viewer can turn into a modal."""
    from starlette.testclient import TestClient

    from mashbill.broadcast import BroadcastHub
    from mashbill.http_app import create_http_app

    client = TestClient(create_http_app(hub=BroadcastHub(enable_watchers=False)))
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "proj-a", "A")

    r = client.post(
        "/api/projects/proj-a/tags",
        params={"project_path": str(tmp_path)},
        json={"name": "session-1"},
    )
    assert r.status_code == 409, r.text
    body = r.json()
    assert body.get("needs_git_init") is True
    assert "workspace_root" in body
    # Still no .git anywhere.
    assert not (tmp_path / ".git").exists()
    assert not (plot_root / ".git").exists()


def test_git_init_endpoint_creates_workspace_repo(tmp_path: Path) -> None:
    """The explicit `POST /api/workspace/git-init` is the ONLY path that
    runs `git init`. It targets the workspace root (`tmp_path`), not the
    plot data root. Idempotent — second call is a 200 no-op."""
    from starlette.testclient import TestClient

    from mashbill.broadcast import BroadcastHub
    from mashbill.http_app import create_http_app

    client = TestClient(create_http_app(hub=BroadcastHub(enable_watchers=False)))

    r = client.post(
        "/api/workspace/git-init",
        params={"project_path": str(tmp_path)},
    )
    assert r.status_code == 201, r.text
    assert (tmp_path / ".git").is_dir()
    plot_root = resolve_plot_root(str(tmp_path))
    assert not (plot_root / ".git").exists(), "no nested .git under .noory/novel"

    # Idempotent — second call is a 200, no error.
    r2 = client.post(
        "/api/workspace/git-init",
        params={"project_path": str(tmp_path)},
    )
    assert r2.status_code == 200, r2.text


def test_tag_after_consent_lands_in_workspace_repo(tmp_path: Path) -> None:
    """After the user consents to init, tag/at-tag/publish all hit
    `<workspace>/.git`. Files inside the repo sit at `.noory/novel/{id}/…`."""
    from starlette.testclient import TestClient

    from mashbill.broadcast import BroadcastHub
    from mashbill.http_app import create_http_app

    client = TestClient(create_http_app(hub=BroadcastHub(enable_watchers=False)))
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "proj-a", "A")
    client.post("/api/workspace/git-init", params={"project_path": str(tmp_path)})

    r = client.post(
        "/api/projects/proj-a/tags",
        params={"project_path": str(tmp_path)},
        json={"name": "session-1"},
    )
    assert r.status_code == 201, r.text
    assert (tmp_path / ".git").is_dir()
    assert not (plot_root / ".git").exists()

    listed = client.get(
        "/api/projects/proj-a/tags", params={"project_path": str(tmp_path)}
    )
    assert "session-1" in [t["name"] for t in listed.json()["tags"]]

    # At-tag: file paths inside the repo are prefixed with .noory/novel/{id}/.
    at = client.get(
        "/api/projects/proj-a/at-tag/session-1",
        params={"project_path": str(tmp_path)},
    )
    assert at.status_code == 200, at.text
    assert at.json()["project"]["id"] == "proj-a"


def test_plot_does_not_touch_existing_user_git(tmp_path: Path) -> None:
    """When the workspace already is a git repo with the user's identity,
    Novel must reuse it and not overwrite `user.name` / `user.email` /
    `.gitignore` / `.gitattributes`."""
    from starlette.testclient import TestClient

    from mashbill.broadcast import BroadcastHub
    from mashbill.http_app import create_http_app

    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "--local", "user.name", "Alice"], cwd=tmp_path, check=True
    )
    subprocess.run(
        ["git", "config", "--local", "user.email", "alice@example.com"],
        cwd=tmp_path,
        check=True,
    )
    user_gitignore = "*.pyc\n.env\n"
    (tmp_path / ".gitignore").write_text(user_gitignore, encoding="utf-8")

    client = TestClient(create_http_app(hub=BroadcastHub(enable_watchers=False)))
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "proj-a", "A")
    # init endpoint on a repo that already exists is a 200 no-op.
    r = client.post(
        "/api/workspace/git-init",
        params={"project_path": str(tmp_path)},
    )
    assert r.status_code == 200, r.text
    # Tag commit creates a commit, but the user's config + gitignore stay put.
    client.post(
        "/api/projects/proj-a/tags",
        params={"project_path": str(tmp_path)},
        json={"name": "session-1"},
    )
    name = subprocess.run(
        ["git", "config", "--local", "user.name"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    email = subprocess.run(
        ["git", "config", "--local", "user.email"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert name == "Alice"
    assert email == "alice@example.com"
    assert (tmp_path / ".gitignore").read_text(encoding="utf-8") == user_gitignore


def test_plot_commit_author_is_plot_even_on_users_repo(tmp_path: Path) -> None:
    """Novel commits carry their own author identity inline, so the user can
    still grep `git log --author Novel` even when the repo's local config
    points at the user."""
    from starlette.testclient import TestClient

    from mashbill.broadcast import BroadcastHub
    from mashbill.http_app import create_http_app

    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "--local", "user.name", "Alice"], cwd=tmp_path, check=True
    )
    subprocess.run(
        ["git", "config", "--local", "user.email", "alice@example.com"],
        cwd=tmp_path,
        check=True,
    )

    client = TestClient(create_http_app(hub=BroadcastHub(enable_watchers=False)))
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "proj-a", "A")
    client.post(
        "/api/projects/proj-a/tags",
        params={"project_path": str(tmp_path)},
        json={"name": "session-1"},
    )
    log = subprocess.run(
        ["git", "log", "-1", "--format=%an %ae"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert log == "Novel plot@noory-ai.local"


def test_tag_only_stages_plot_data_paths(tmp_path: Path) -> None:
    """Novel's tag commits must stage only `.noory/novel/`. A user file
    edited outside that path stays uncommitted across a Novel tag."""
    from starlette.testclient import TestClient

    from mashbill.broadcast import BroadcastHub
    from mashbill.http_app import create_http_app

    client = TestClient(create_http_app(hub=BroadcastHub(enable_watchers=False)))
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "proj-a", "A")
    client.post("/api/workspace/git-init", params={"project_path": str(tmp_path)})

    user_file = tmp_path / "user_notes.md"
    user_file.write_text("dirty user edit", encoding="utf-8")

    client.post(
        "/api/projects/proj-a/tags",
        params={"project_path": str(tmp_path)},
        json={"name": "session-1"},
    )
    # `user_notes.md` is still untracked after the Novel tag.
    status = subprocess.run(
        ["git", "status", "--porcelain", "user_notes.md"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "user_notes.md" in status, f"expected user_notes.md untracked, got: {status!r}"


def test_legacy_dotnoory_plot_git_migrates_up_to_workspace(tmp_path: Path) -> None:
    """A workspace last opened under the v0.59.x design has `.noory/novel/.git/`.
    On first open under the new model, Novel moves it up to the workspace root
    — but ONLY if the workspace doesn't already have a `.git/` (the user could
    have their own repo there)."""
    # Seed the legacy layout: a real git repo at .noory/novel/.
    plot_root = resolve_plot_root(str(tmp_path))
    subprocess.run(["git", "init", "-q"], cwd=plot_root, check=True)
    (plot_root / "marker.txt").write_text("legacy repo", encoding="utf-8")
    subprocess.run(
        ["git", "-c", "user.name=x", "-c", "user.email=x@x", "add", "-A"],
        cwd=plot_root,
        check=True,
    )
    subprocess.run(
        ["git", "-c", "user.name=x", "-c", "user.email=x@x",
         "commit", "-m", "legacy"], cwd=plot_root, check=True,
    )

    # Open the workspace (triggers migration).
    from mashbill.workspace import migrate_legacy_git_to_workspace

    moved = migrate_legacy_git_to_workspace(tmp_path)
    assert moved is True
    assert (tmp_path / ".git").is_dir()
    assert not (plot_root / ".git").exists()
    # History carried over — the legacy "marker.txt" commit is reachable.
    log = subprocess.run(
        ["git", "log", "--format=%s"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "legacy" in log


def test_legacy_migration_skipped_when_workspace_already_has_git(tmp_path: Path) -> None:
    """If the user already has their own `.git/` at the workspace root, the
    legacy `.noory/novel/.git/` migration is a no-op — merging histories is the
    user's call, not Novel's."""
    plot_root = resolve_plot_root(str(tmp_path))
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "init", "-q"], cwd=plot_root, check=True)

    from mashbill.workspace import migrate_legacy_git_to_workspace

    moved = migrate_legacy_git_to_workspace(tmp_path)
    assert moved is False
    # Both repos still present, untouched.
    assert (tmp_path / ".git").is_dir()
    assert (plot_root / ".git").is_dir()
