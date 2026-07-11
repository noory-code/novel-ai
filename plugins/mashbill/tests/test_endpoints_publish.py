"""Error / edge-path coverage for the publish endpoints (D-2026-06-11-B).

The happy paths (patch/minor/major bump, at-tag read, invalid-bump 400) live
in ``test_api_endpoints.py``. This file pins the branches that only fire on
failure, because those are the ones that rot silently:

  - the semver bumper's own validation (bad prefix / bad parts / bad level);
  - the project-publish guards: missing ``project_path`` (400), unknown
    project (404), non-JSON body (400), a corrupted on-disk version (400);
  - the git write-boundary rollbacks: no repo → structured ``needs_git_init``
    409 with the version rolled back, and a tag collision → 409 with rollback;
  - ``project_path`` guards on the two format-F endpoints (snapshot / service).

These drive the real Starlette layer through ``TestClient`` against an on-disk
temp workspace so a broken branch fails the assert, not a mock.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from mashbill.broadcast import BroadcastHub
from mashbill.endpoints_publish import _bump_blueprint_version
from mashbill.folder_io import _project_dir
from mashbill.git_store import init_workspace_repo, list_tags, tag_snapshot
from mashbill.http_app import create_http_app
from mashbill.project_io import create_project
from mashbill.workspace import resolve_plot_root


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "ws"
    ws.mkdir()
    return ws


@pytest.fixture
def client() -> TestClient:
    """A NO-git client — Novel never auto-inits, so the publish git boundary
    fires unless a test seeds a repo itself."""
    return TestClient(create_http_app(hub=BroadcastHub(enable_watchers=False)))


def _make_project(workspace: Path, project_id: str = "alpha") -> Path:
    plot_root = resolve_plot_root(str(workspace))
    create_project(plot_root, project_id, project_id.title())
    return plot_root


# ---------------------------------------------------------------------------
# _bump_blueprint_version — pure semver bumper
# ---------------------------------------------------------------------------


def test_bump_happy_paths() -> None:
    assert _bump_blueprint_version("v1.2.3", "major") == "v2.0.0"
    assert _bump_blueprint_version("v1.2.3", "minor") == "v1.3.0"
    assert _bump_blueprint_version("v1.2.3", "patch") == "v1.2.4"


def test_bump_rejects_missing_v_prefix() -> None:
    with pytest.raises(ValueError, match="must start with 'v'"):
        _bump_blueprint_version("1.2.3", "patch")


@pytest.mark.parametrize("bad", ["v1.2", "v1.2.3.4", "vx.y.z", "v1.2.x"])
def test_bump_rejects_non_semver(bad: str) -> None:
    with pytest.raises(ValueError, match="need v<MAJOR>"):
        _bump_blueprint_version(bad, "patch")


def test_bump_rejects_unknown_level() -> None:
    with pytest.raises(ValueError, match="bump must be one of"):
        _bump_blueprint_version("v1.2.3", "huge")


# ---------------------------------------------------------------------------
# project_publish_endpoint — guards & rollbacks
# ---------------------------------------------------------------------------


def test_publish_requires_project_path(client: TestClient) -> None:
    resp = client.post("/api/projects/alpha/publish", json={"bump": "patch"})
    assert resp.status_code == 400
    assert "project_path" in resp.json()["error"]


def test_publish_404_when_project_missing(client: TestClient, workspace: Path) -> None:
    resolve_plot_root(str(workspace))  # create .noory/plot but no project
    resp = client.post(
        f"/api/projects/ghost/publish?project_path={workspace}",
        json={"bump": "patch"},
    )
    assert resp.status_code == 404
    assert "project not found: ghost" in resp.json()["error"]


def test_publish_rejects_invalid_json(client: TestClient, workspace: Path) -> None:
    _make_project(workspace)
    resp = client.post(
        f"/api/projects/alpha/publish?project_path={workspace}",
        content=b"{not json",
        headers={"content-type": "application/json"},
    )
    assert resp.status_code == 400
    assert "invalid JSON" in resp.json()["error"]


def test_publish_400_on_corrupted_on_disk_version(client: TestClient, workspace: Path) -> None:
    # A project whose stored version is not valid semver makes the bumper
    # raise — the endpoint surfaces it as a 400 rather than 500ing.
    plot_root = _make_project(workspace)
    project_json = _project_dir(plot_root, "alpha") / "project.json"
    data = json.loads(project_json.read_text())
    data["blueprint_version"] = "1.0.0"  # missing the 'v' prefix
    project_json.write_text(json.dumps(data))
    resp = client.post(
        f"/api/projects/alpha/publish?project_path={workspace}",
        json={"bump": "patch"},
    )
    assert resp.status_code == 400
    assert "must start with 'v'" in resp.json()["error"]


def test_publish_without_git_returns_needs_init_and_rolls_back(
    client: TestClient, workspace: Path
) -> None:
    _make_project(workspace)  # NO init_workspace_repo
    resp = client.post(
        f"/api/projects/alpha/publish?project_path={workspace}",
        json={"bump": "patch"},
    )
    assert resp.status_code == 409
    body = resp.json()
    assert body["needs_git_init"] is True
    assert body["workspace_root"] == str(workspace)
    # The version bump must be rolled back so a later retry starts clean.
    proj = client.get(f"/api/projects/alpha?project_path={workspace}").json()
    assert proj["blueprint_version"] == "v0.1.0"


def test_publish_tag_collision_returns_409_and_rolls_back(
    client: TestClient, workspace: Path
) -> None:
    _make_project(workspace)
    init_workspace_repo(workspace)
    # Pre-create the tag the patch bump would target (v0.1.0 -> v0.1.1).
    tag_snapshot(workspace, "v0.1.1", message="manual")
    resp = client.post(
        f"/api/projects/alpha/publish?project_path={workspace}",
        json={"bump": "patch"},
    )
    assert resp.status_code == 409
    # Version rolled back, and no duplicate tag was created.
    proj = client.get(f"/api/projects/alpha?project_path={workspace}").json()
    assert proj["blueprint_version"] == "v0.1.0"
    names = [t["name"] for t in list_tags(workspace)]
    assert names.count("v0.1.1") == 1


# ---------------------------------------------------------------------------
# format-F endpoints — project_path guards
# ---------------------------------------------------------------------------


def test_snapshot_requires_project_path(client: TestClient) -> None:
    resp = client.post("/api/projects/alpha/publish/snapshot")
    assert resp.status_code == 400
    assert "project_path" in resp.json()["error"]


def test_service_publish_requires_project_path(client: TestClient) -> None:
    resp = client.post("/api/projects/alpha/services/svc1/publish")
    assert resp.status_code == 400
    assert "project_path" in resp.json()["error"]
