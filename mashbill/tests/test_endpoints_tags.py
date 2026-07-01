"""Tag (git session bookmark) + read-only "view at tag" endpoint tests.

Covers the four handlers in ``mashbill/endpoints_tags.py``:

  - ``GET    /api/projects/{project_id}/tags``            (tags_list_endpoint)
  - ``POST   /api/projects/{project_id}/tags``            (tag_post_endpoint)
  - ``DELETE /api/projects/{project_id}/tags/{tag_name}`` (tag_delete_endpoint)
  - ``GET    /api/projects/{project_id}/at-tag/{tag}``     (project_at_tag_endpoint)

These are thin Starlette shells over ``mashbill.git_store``. The tests drive
the real HTTP layer through Starlette's ``TestClient`` against a real on-disk
temp workspace + git repo, asserting status codes, error bodies, and disk
side effects (created / deleted git tags, the frozen snapshot body) so each
test fails if the handler's branch logic breaks.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from mashbill.broadcast import BroadcastHub
from mashbill.git_store import init_workspace_repo, list_tags
from mashbill.http_app import create_http_app
from mashbill.project_io import create_project
from mashbill.workspace import resolve_plot_root

# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "ws"
    ws.mkdir()
    return ws


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_http_app(hub=BroadcastHub(enable_watchers=False)))


def _make_project(workspace: Path, project_id: str = "alpha") -> Path:
    """Create a flat project on disk and return its resolved plot_root."""
    plot_root = resolve_plot_root(str(workspace))
    create_project(plot_root, project_id, project_id.title())
    return plot_root


# ---------------------------------------------------------------------------
# tags_list_endpoint — GET /api/projects/{id}/tags
# ---------------------------------------------------------------------------


def test_tags_list_requires_project_path(client: TestClient) -> None:
    # _require_plot_root raises _ApiError -> exc.response (lines 43-44).
    resp = client.get("/api/projects/alpha/tags")
    assert resp.status_code == 400
    assert "project_path" in resp.json()["error"]


def test_tags_list_404_when_project_missing(client: TestClient, workspace: Path) -> None:
    # plot_root resolves (the .noory/plot dir is created) but there is no
    # project.json -> 404 (line 48).
    resp = client.get(f"/api/projects/ghost/tags?project_path={workspace}")
    assert resp.status_code == 404
    assert "project not found: ghost" in resp.json()["error"]


def test_tags_list_empty_when_no_git(client: TestClient, workspace: Path) -> None:
    # Project exists but the workspace has no .git/ -> list_tags returns []
    # (the happy path with zero tags, line 49).
    _make_project(workspace)
    resp = client.get(f"/api/projects/alpha/tags?project_path={workspace}")
    assert resp.status_code == 200
    assert resp.json() == {"tags": []}


def test_tags_list_returns_created_tag(client: TestClient, workspace: Path) -> None:
    _make_project(workspace)
    init_workspace_repo(workspace)
    # Create a tag through the POST handler, then read it back via GET.
    created = client.post(
        f"/api/projects/alpha/tags?project_path={workspace}",
        json={"name": "v1", "message": "first snapshot"},
    )
    assert created.status_code == 201, created.text

    resp = client.get(f"/api/projects/alpha/tags?project_path={workspace}")
    assert resp.status_code == 200
    tags = resp.json()["tags"]
    assert [t["name"] for t in tags] == ["v1"]
    assert tags[0]["message"] == "first snapshot"


# ---------------------------------------------------------------------------
# tag_post_endpoint — POST /api/projects/{id}/tags
# ---------------------------------------------------------------------------


def test_tag_post_requires_project_path(client: TestClient) -> None:
    # _require_plot_root raises -> exc.response (lines 54-56).
    resp = client.post("/api/projects/alpha/tags", json={"name": "v1"})
    assert resp.status_code == 400
    assert "project_path" in resp.json()["error"]


def test_tag_post_404_when_project_missing(client: TestClient, workspace: Path) -> None:
    # line 60.
    resp = client.post(
        f"/api/projects/ghost/tags?project_path={workspace}",
        json={"name": "v1"},
    )
    assert resp.status_code == 404
    assert "project not found: ghost" in resp.json()["error"]


def test_tag_post_rejects_invalid_json(client: TestClient, workspace: Path) -> None:
    # json.JSONDecodeError branch (lines 63-64).
    _make_project(workspace)
    resp = client.post(
        f"/api/projects/alpha/tags?project_path={workspace}",
        content=b"{not valid json",
        headers={"content-type": "application/json"},
    )
    assert resp.status_code == 400
    assert resp.json()["error"] == "invalid JSON body"


def test_tag_post_requires_non_empty_name(client: TestClient, workspace: Path) -> None:
    # name missing / blank -> 400 (line 68).
    _make_project(workspace)
    for body in ({}, {"name": ""}, {"name": "   "}, {"name": 5}):
        resp = client.post(
            f"/api/projects/alpha/tags?project_path={workspace}",
            json=body,
        )
        assert resp.status_code == 400, body
        assert "'name' is required" in resp.json()["error"]


def test_tag_post_409_when_git_not_initialized(client: TestClient, workspace: Path) -> None:
    # tag_snapshot raises GitNotInitializedError -> 409 needs_git_init body
    # (_git_not_initialized_response, lines 72-73).
    _make_project(workspace)
    resp = client.post(
        f"/api/projects/alpha/tags?project_path={workspace}",
        json={"name": "v1"},
    )
    assert resp.status_code == 409
    body = resp.json()
    assert body["needs_git_init"] is True
    assert body["error"] == "git not initialized in workspace"
    assert body["workspace_root"] == str(workspace)


def test_tag_post_creates_annotated_tag_on_disk(client: TestClient, workspace: Path) -> None:
    # Happy path: 201 + the tag is physically present in the repo afterwards.
    _make_project(workspace)
    init_workspace_repo(workspace)
    resp = client.post(
        f"/api/projects/alpha/tags?project_path={workspace}",
        json={"name": "v1", "message": "snapshot one"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "v1"
    assert body["message"] == "snapshot one"
    assert len(body["sha"]) >= 7  # a real commit sha
    # disk side effect: the tag exists in the real repo.
    assert [t["name"] for t in list_tags(workspace)] == ["v1"]


def test_tag_post_409_on_duplicate_tag(client: TestClient, workspace: Path) -> None:
    # TagAlreadyExistsError -> 409 (lines 74-75).
    _make_project(workspace)
    init_workspace_repo(workspace)
    first = client.post(
        f"/api/projects/alpha/tags?project_path={workspace}",
        json={"name": "v1"},
    )
    assert first.status_code == 201
    dup = client.post(
        f"/api/projects/alpha/tags?project_path={workspace}",
        json={"name": "v1"},
    )
    assert dup.status_code == 409
    assert "already exists" in dup.json()["error"]


# ---------------------------------------------------------------------------
# tag_delete_endpoint — DELETE /api/projects/{id}/tags/{tag_name}
# ---------------------------------------------------------------------------


def test_tag_delete_requires_project_path(client: TestClient) -> None:
    # lines 82-83.
    resp = client.delete("/api/projects/alpha/tags/v1")
    assert resp.status_code == 400
    assert "project_path" in resp.json()["error"]


def test_tag_delete_404_when_project_missing(client: TestClient, workspace: Path) -> None:
    # line 88.
    resp = client.delete(f"/api/projects/ghost/tags/v1?project_path={workspace}")
    assert resp.status_code == 404
    assert "project not found: ghost" in resp.json()["error"]


def test_tag_delete_404_when_tag_missing(client: TestClient, workspace: Path) -> None:
    # delete_tag raises KeyError -> 404 (lines 91-92).
    _make_project(workspace)
    init_workspace_repo(workspace)
    resp = client.delete(f"/api/projects/alpha/tags/nope?project_path={workspace}")
    assert resp.status_code == 404
    assert "tag not found: nope" in resp.json()["error"]


def test_tag_delete_removes_existing_tag(client: TestClient, workspace: Path) -> None:
    # Happy path: 200 {"ok": True} + the tag is gone from disk afterwards.
    _make_project(workspace)
    init_workspace_repo(workspace)
    client.post(
        f"/api/projects/alpha/tags?project_path={workspace}",
        json={"name": "v1"},
    )
    assert [t["name"] for t in list_tags(workspace)] == ["v1"]

    resp = client.delete(f"/api/projects/alpha/tags/v1?project_path={workspace}")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
    assert list_tags(workspace) == []  # disk side effect: tag removed


# ---------------------------------------------------------------------------
# project_at_tag_endpoint — GET /api/projects/{id}/at-tag/{tag}
# ---------------------------------------------------------------------------


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _seed_snapshot_project(client: TestClient, workspace: Path) -> Path:
    """Lay a flat project on disk with a services canvas that has a root
    service node plus its feature detail.json, then git-tag it as ``v1``.

    Returns the resolved plot_root. The on-disk JSON is written directly
    (not via the model layer) so the test pins exactly the raw-dict shape the
    ``at-tag`` handler reads back out of git.
    """
    plot_root = _make_project(workspace, "alpha")
    # Flat layout (S2): _project_dir == plot_root, files live directly under it.
    _write_json(
        plot_root / "project.json",
        {"id": "alpha", "name": "Alpha"},
    )
    _write_json(
        plot_root / "foundation" / "canvas.json",
        {"canvas_id": "foundation", "canvas_kind": "foundation", "nodes": []},
    )
    _write_json(
        plot_root / "services" / "canvas.json",
        {
            "canvas_id": "services",
            "canvas_kind": "services",
            "nodes": [
                # A root service -> its detail.json should be discovered.
                {"id": "svc1", "kind": "service", "is_root": True, "label": "Refunds"},
                # A non-root service -> skipped (line 166 continue).
                {"id": "svc2", "kind": "service", "is_root": False, "label": "Other"},
                # A non-service node -> skipped (line 166 continue).
                {"id": "cat1", "kind": "category", "is_root": True, "label": "Group"},
                # A root service whose id is not a str -> skipped (line 169-170).
                {"id": 123, "kind": "service", "is_root": True, "label": "Bad"},
                # A bare string in the nodes list -> skipped (line 164-165).
                "not-a-dict",
            ],
        },
    )
    _write_json(
        plot_root / "services" / "svc1" / "detail.json",
        {"canvas_id": "feature:svc1", "canvas_kind": "feature", "nodes": []},
    )
    # Commit + tag the data root.
    init_workspace_repo(workspace)
    resp = client.post(
        f"/api/projects/alpha/tags?project_path={workspace}",
        json={"name": "v1", "message": "snap"},
    )
    assert resp.status_code == 201, resp.text
    return plot_root


def test_at_tag_requires_project_path(client: TestClient) -> None:
    # lines 124-125.
    resp = client.get("/api/projects/alpha/at-tag/v1")
    assert resp.status_code == 400
    assert "project_path" in resp.json()["error"]


def test_at_tag_404_when_project_missing(client: TestClient, workspace: Path) -> None:
    # line 130.
    resp = client.get(f"/api/projects/ghost/at-tag/v1?project_path={workspace}")
    assert resp.status_code == 404
    assert "project not found: ghost" in resp.json()["error"]


def test_at_tag_404_when_tag_missing(client: TestClient, workspace: Path) -> None:
    # No such tag -> read_file_at_tag raises FileNotFoundError on project.json
    # -> project_raw is None -> 404 (line 153).
    _make_project(workspace)
    init_workspace_repo(workspace)
    resp = client.get(f"/api/projects/alpha/at-tag/missing?project_path={workspace}")
    assert resp.status_code == 404
    assert "project.json not at tag 'missing'" in resp.json()["error"]


def test_at_tag_returns_frozen_snapshot_with_feature_canvas(
    client: TestClient, workspace: Path
) -> None:
    """The core of the endpoint: at a real tag it returns the project doc plus
    every canvas, and discovers feature canvases by walking the services
    canvas's root service nodes (lines 161-173). Only the well-formed root
    service (``svc1``) yields a ``feature:`` entry; the non-root, non-service,
    non-str-id, and non-dict entries are all skipped."""
    _seed_snapshot_project(client, workspace)

    resp = client.get(f"/api/projects/alpha/at-tag/v1?project_path={workspace}")
    assert resp.status_code == 200
    body = resp.json()

    assert body["project"] == {"id": "alpha", "name": "Alpha"}

    canvases = body["canvases"]
    # create_project seeds all four base canvases on disk; each is surfaced
    # (the loop over ("foundation", "actors", "services", "entities")).
    assert "foundation" in canvases
    assert "actors" in canvases
    assert "services" in canvases
    assert "entities" in canvases

    # Exactly one feature canvas discovered: the root service svc1. The
    # non-root svc2, the category node, the int-id node, and the bare string
    # are all skipped by the discovery loop.
    feature_keys = [k for k in canvases if k.startswith("feature:")]
    assert feature_keys == ["feature:svc1"]
    assert canvases["feature:svc1"]["canvas_id"] == "feature:svc1"


def test_at_tag_skips_canvas_with_corrupt_json(client: TestClient, workspace: Path) -> None:
    """A canvas file whose committed bytes are not valid JSON is tolerated:
    ``_read_canvas_json`` swallows the ``json.JSONDecodeError`` and returns
    None (lines 148-149), so that canvas is simply absent rather than 500ing
    the whole snapshot. project.json itself stays valid -> overall 200."""
    plot_root = _make_project(workspace, "alpha")
    _write_json(plot_root / "project.json", {"id": "alpha", "name": "Alpha"})
    # Overwrite the seeded foundation canvas with garbage bytes.
    foundation = plot_root / "foundation" / "canvas.json"
    foundation.parent.mkdir(parents=True, exist_ok=True)
    foundation.write_text("{not json at all", encoding="utf-8")
    # A valid services canvas so the body still carries at least one canvas.
    _write_json(
        plot_root / "services" / "canvas.json",
        {"canvas_id": "services", "canvas_kind": "services", "nodes": []},
    )
    init_workspace_repo(workspace)
    created = client.post(
        f"/api/projects/alpha/tags?project_path={workspace}",
        json={"name": "v1"},
    )
    assert created.status_code == 201, created.text

    resp = client.get(f"/api/projects/alpha/at-tag/v1?project_path={workspace}")
    assert resp.status_code == 200
    canvases = resp.json()["canvases"]
    # The corrupt foundation canvas is dropped, not surfaced and not fatal.
    assert "foundation" not in canvases
    assert "services" in canvases


def test_at_tag_skips_missing_detail_json(client: TestClient, workspace: Path) -> None:
    """A root service whose detail.json was never written must NOT crash the
    handler and must NOT produce a ``feature:`` entry (lines 171-173: the
    ``if d is not None`` guard). This pins the None-detail branch."""
    plot_root = _make_project(workspace, "alpha")
    _write_json(plot_root / "project.json", {"id": "alpha", "name": "Alpha"})
    _write_json(
        plot_root / "services" / "canvas.json",
        {
            "canvas_id": "services",
            "canvas_kind": "services",
            "nodes": [
                {"id": "svcX", "kind": "service", "is_root": True, "label": "Lonely"},
            ],
        },
    )
    # NOTE: no services/svcX/detail.json on disk.
    init_workspace_repo(workspace)
    created = client.post(
        f"/api/projects/alpha/tags?project_path={workspace}",
        json={"name": "v1"},
    )
    assert created.status_code == 201, created.text

    resp = client.get(f"/api/projects/alpha/at-tag/v1?project_path={workspace}")
    assert resp.status_code == 200
    canvases = resp.json()["canvases"]
    assert "services" in canvases
    assert [k for k in canvases if k.startswith("feature:")] == []
