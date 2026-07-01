"""Project + workspace-discovery HTTP endpoint tests (D-2026-06-11-B).

Pins the request→response contract of ``mashbill.endpoints_projects`` — the
Starlette handlers behind ``/api/projects*`` and ``/api/workspace/*``. The
data-layer behaviour (``project_io`` / ``workspace`` / ``git_store``) is tested
elsewhere; here we cover the HTTP shell: status codes, error envelopes, and the
on-disk side effects each endpoint is responsible for.

Harness mirrors ``tests/test_endpoints_chat.py``: a ``TestClient`` over
``create_http_app`` with a watcher-free ``BroadcastHub`` and a per-test
``workspace`` temp dir. ``project_path`` is the workspace dir; the engine
resolves ``{project_path}/.noory/plot`` itself.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from starlette.testclient import TestClient

from mashbill.broadcast import BroadcastHub
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
    return TestClient(create_http_app(hub=BroadcastHub(enable_watchers=False)))


# ---------------------------------------------------------------------------
# GET /api/projects — list + lazy migration
# ---------------------------------------------------------------------------


def test_projects_list_requires_project_path(client: TestClient) -> None:
    resp = client.get("/api/projects")
    assert resp.status_code == 400
    assert "project_path" in resp.json()["error"]


def test_projects_list_empty_workspace(client: TestClient, workspace: Path) -> None:
    resp = client.get(f"/api/projects?project_path={workspace}")
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"projects": [], "migrated": []}


def test_projects_list_returns_created_project(client: TestClient, workspace: Path) -> None:
    create_project(resolve_plot_root(str(workspace)), "alpha", "Alpha")
    resp = client.get(f"/api/projects?project_path={workspace}")
    assert resp.status_code == 200
    projects = resp.json()["projects"]
    assert [p["id"] for p in projects] == ["alpha"]
    assert projects[0]["name"] == "Alpha"


# ---------------------------------------------------------------------------
# POST /api/projects — create
# ---------------------------------------------------------------------------


def test_project_post_creates_project_and_seeds_canvases(
    client: TestClient, workspace: Path
) -> None:
    resp = client.post(
        f"/api/projects?project_path={workspace}",
        json={"id": "alpha", "name": "Alpha"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"] == "alpha"
    assert body["name"] == "Alpha"
    # Side effect: the four seed canvases are on disk. S2 flat layout
    # (D-2026-06-21-AB) — a lone project's files live directly under plot_root.
    plot_root = resolve_plot_root(str(workspace))
    assert (plot_root / "project.json").exists()
    for kind in ("foundation", "actors", "services", "entities"):
        assert (plot_root / kind / "canvas.json").exists(), kind


def test_project_post_requires_project_path(client: TestClient) -> None:
    resp = client.post("/api/projects", json={"id": "alpha"})
    assert resp.status_code == 400
    assert "project_path" in resp.json()["error"]


def test_project_post_rejects_invalid_json(client: TestClient, workspace: Path) -> None:
    resp = client.post(
        f"/api/projects?project_path={workspace}",
        content=b"{not json",
        headers={"content-type": "application/json"},
    )
    assert resp.status_code == 400
    assert resp.json()["error"] == "invalid JSON body"


def test_project_post_requires_id(client: TestClient, workspace: Path) -> None:
    resp = client.post(f"/api/projects?project_path={workspace}", json={"name": "Alpha"})
    assert resp.status_code == 400
    assert "id" in resp.json()["error"]


def test_project_post_rejects_non_string_id(client: TestClient, workspace: Path) -> None:
    resp = client.post(
        f"/api/projects?project_path={workspace}",
        json={"id": 123, "name": "Alpha"},
    )
    assert resp.status_code == 400
    assert "id" in resp.json()["error"]


def test_project_post_conflict_when_dir_already_holds_a_project(
    client: TestClient, workspace: Path
) -> None:
    """One-project-per-dir (D-2026-06-21-AA): a second create in the same
    workspace is a 409, not a silent overwrite."""
    create_project(resolve_plot_root(str(workspace)), "alpha", "Alpha")
    resp = client.post(
        f"/api/projects?project_path={workspace}",
        json={"id": "beta", "name": "Beta"},
    )
    assert resp.status_code == 409
    assert "alpha" in resp.json()["error"]


def test_project_post_invalid_id_is_422(client: TestClient, workspace: Path) -> None:
    """A syntactically-present but model-invalid id (space → kebab validator)
    surfaces the pydantic ValidationError as a 422, not a 500."""
    resp = client.post(
        f"/api/projects?project_path={workspace}",
        json={"id": "bad id!", "name": "Bad"},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/projects/{project_id}
# ---------------------------------------------------------------------------


def test_project_get_returns_doc_with_details_and_tags(
    client: TestClient, workspace: Path
) -> None:
    create_project(resolve_plot_root(str(workspace)), "alpha", "Alpha")
    resp = client.get(f"/api/projects/alpha?project_path={workspace}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == "alpha"
    # The GET endpoint enriches the bare ProjectDoc with these two keys.
    assert body["feature_details"] == []
    assert body["tags"] == []  # no git repo → no tags


def test_project_get_missing_is_404(client: TestClient, workspace: Path) -> None:
    resp = client.get(f"/api/projects/ghost?project_path={workspace}")
    assert resp.status_code == 404


def test_project_get_requires_project_path(client: TestClient) -> None:
    resp = client.get("/api/projects/alpha")
    assert resp.status_code == 400
    assert "project_path" in resp.json()["error"]


# ---------------------------------------------------------------------------
# PATCH /api/projects/{project_id} — rename
# ---------------------------------------------------------------------------


def test_project_patch_renames(client: TestClient, workspace: Path) -> None:
    create_project(resolve_plot_root(str(workspace)), "alpha", "Alpha")
    resp = client.patch(
        f"/api/projects/alpha?project_path={workspace}",
        json={"name": "Renamed"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed"
    # Persisted: a fresh GET reflects the new name.
    again = client.get(f"/api/projects/alpha?project_path={workspace}")
    assert again.json()["name"] == "Renamed"


def test_project_patch_rejects_invalid_json(client: TestClient, workspace: Path) -> None:
    create_project(resolve_plot_root(str(workspace)), "alpha", "Alpha")
    resp = client.patch(
        f"/api/projects/alpha?project_path={workspace}",
        content=b"{nope",
        headers={"content-type": "application/json"},
    )
    assert resp.status_code == 400
    assert resp.json()["error"] == "invalid JSON body"


def test_project_patch_rejects_blank_name(client: TestClient, workspace: Path) -> None:
    create_project(resolve_plot_root(str(workspace)), "alpha", "Alpha")
    resp = client.patch(
        f"/api/projects/alpha?project_path={workspace}",
        json={"name": "   "},
    )
    assert resp.status_code == 400
    assert "name" in resp.json()["error"]


def test_project_patch_missing_project_is_404(client: TestClient, workspace: Path) -> None:
    resp = client.patch(
        f"/api/projects/ghost?project_path={workspace}",
        json={"name": "X"},
    )
    assert resp.status_code == 404


def test_project_patch_requires_project_path(client: TestClient) -> None:
    resp = client.patch("/api/projects/alpha", json={"name": "X"})
    assert resp.status_code == 400
    assert "project_path" in resp.json()["error"]


# ---------------------------------------------------------------------------
# PATCH /api/projects/{project_id}/anchors/{canvas} — anchor placement
# ---------------------------------------------------------------------------


def test_anchor_patch_updates_only_supplied_fields(
    client: TestClient, workspace: Path
) -> None:
    """The longer 176-199 block: read project, merge only non-None body fields
    onto the existing AnchorPlacement, write back. Defaults stay put."""
    create_project(resolve_plot_root(str(workspace)), "alpha", "Alpha")
    resp = client.patch(
        f"/api/projects/alpha/anchors/foundation?project_path={workspace}",
        json={"x": 42.0, "color": "#ff0000"},
    )
    assert resp.status_code == 200
    anchor = resp.json()["anchors"]["foundation"]
    assert anchor["x"] == 42.0
    assert anchor["color"] == "#ff0000"
    # Untouched fields keep the AnchorPlacement defaults.
    assert anchor["y"] == -75.0
    assert anchor["width"] == 150.0
    assert anchor["shape"] == "circle"
    # Other canvases are unaffected.
    assert resp.json()["anchors"]["actors"]["x"] == -75.0


def test_anchor_patch_ignores_none_values(client: TestClient, workspace: Path) -> None:
    """An explicit null in the body must not clobber the existing value
    (the ``if v is not None`` filter)."""
    create_project(resolve_plot_root(str(workspace)), "alpha", "Alpha")
    client.patch(
        f"/api/projects/alpha/anchors/foundation?project_path={workspace}",
        json={"x": 99.0},
    )
    resp = client.patch(
        f"/api/projects/alpha/anchors/foundation?project_path={workspace}",
        json={"x": None, "y": 5.0},
    )
    assert resp.status_code == 200
    anchor = resp.json()["anchors"]["foundation"]
    assert anchor["x"] == 99.0  # null did not overwrite the prior 99
    assert anchor["y"] == 5.0


def test_anchor_patch_persists_to_disk(client: TestClient, workspace: Path) -> None:
    create_project(resolve_plot_root(str(workspace)), "alpha", "Alpha")
    client.patch(
        f"/api/projects/alpha/anchors/services?project_path={workspace}",
        json={"width": 200.0},
    )
    fresh = client.get(f"/api/projects/alpha?project_path={workspace}")
    assert fresh.json()["anchors"]["services"]["width"] == 200.0


def test_anchor_patch_unknown_canvas_is_400(client: TestClient, workspace: Path) -> None:
    create_project(resolve_plot_root(str(workspace)), "alpha", "Alpha")
    resp = client.patch(
        f"/api/projects/alpha/anchors/bogus?project_path={workspace}",
        json={"x": 1.0},
    )
    assert resp.status_code == 400
    assert "bogus" in resp.json()["error"]


def test_anchor_patch_rejects_invalid_json(client: TestClient, workspace: Path) -> None:
    create_project(resolve_plot_root(str(workspace)), "alpha", "Alpha")
    resp = client.patch(
        f"/api/projects/alpha/anchors/foundation?project_path={workspace}",
        content=b"{bad",
        headers={"content-type": "application/json"},
    )
    assert resp.status_code == 400
    assert resp.json()["error"] == "invalid JSON body"


def test_anchor_patch_missing_project_is_404(client: TestClient, workspace: Path) -> None:
    resp = client.patch(
        f"/api/projects/ghost/anchors/foundation?project_path={workspace}",
        json={"x": 1.0},
    )
    assert resp.status_code == 404


def test_anchor_patch_requires_project_path(client: TestClient) -> None:
    resp = client.patch("/api/projects/alpha/anchors/foundation", json={"x": 1.0})
    assert resp.status_code == 400
    assert "project_path" in resp.json()["error"]


# ---------------------------------------------------------------------------
# DELETE /api/projects/{project_id}
# ---------------------------------------------------------------------------


def test_project_delete_removes_project(client: TestClient, workspace: Path) -> None:
    create_project(resolve_plot_root(str(workspace)), "alpha", "Alpha")
    resp = client.delete(f"/api/projects/alpha?project_path={workspace}")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
    # Gone from the list afterwards.
    listing = client.get(f"/api/projects?project_path={workspace}")
    assert listing.json()["projects"] == []


def test_project_delete_missing_is_404(client: TestClient, workspace: Path) -> None:
    resp = client.delete(f"/api/projects/ghost?project_path={workspace}")
    assert resp.status_code == 404


def test_project_delete_requires_project_path(client: TestClient) -> None:
    resp = client.delete("/api/projects/alpha")
    assert resp.status_code == 400
    assert "project_path" in resp.json()["error"]


# ---------------------------------------------------------------------------
# GET /api/workspace/projects — recursive discovery
# ---------------------------------------------------------------------------


def test_workspace_discover_requires_project_path(client: TestClient) -> None:
    resp = client.get("/api/workspace/projects")
    assert resp.status_code == 400


def test_workspace_discover_nonexistent_path_is_404(
    client: TestClient, tmp_path: Path
) -> None:
    resp = client.get(f"/api/workspace/projects?project_path={tmp_path / 'nope'}")
    assert resp.status_code == 404


def test_workspace_discover_finds_nested_project(client: TestClient, workspace: Path) -> None:
    sub = workspace / "service-a"
    sub.mkdir()
    create_project(resolve_plot_root(str(sub)), "alpha", "Alpha")
    resp = client.get(f"/api/workspace/projects?project_path={workspace}")
    assert resp.status_code == 200
    found = resp.json()["projects"]
    assert len(found) == 1
    assert found[0]["project"]["id"] == "alpha"
    assert found[0]["dir"] == "service-a"


# ---------------------------------------------------------------------------
# GET /api/workspace/tree — dir-tree picker
# ---------------------------------------------------------------------------


def test_dir_tree_returns_nested_dirs(client: TestClient, workspace: Path) -> None:
    (workspace / "child").mkdir()
    resp = client.get(f"/api/workspace/tree?project_path={workspace}")
    assert resp.status_code == 200
    root = resp.json()["root"]
    assert root["rel"] == "."
    assert root["has_plot"] is False
    child_rels = [c["rel"] for c in root["children"]]
    assert "child" in child_rels


def test_dir_tree_requires_project_path(client: TestClient) -> None:
    resp = client.get("/api/workspace/tree")
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# POST /api/workspace/dir — create a directory under the workspace
# ---------------------------------------------------------------------------


def test_dir_create_makes_directory(client: TestClient, workspace: Path) -> None:
    resp = client.post(
        f"/api/workspace/dir?project_path={workspace}",
        json={"rel": "banana"},
    )
    assert resp.status_code == 201
    assert resp.json() == {"rel": "banana"}
    assert (workspace / "banana").is_dir()


def test_dir_create_requires_project_path(client: TestClient) -> None:
    resp = client.post("/api/workspace/dir", json={"rel": "banana"})
    assert resp.status_code == 400
    assert "project_path" in resp.json()["error"]


def test_dir_create_rejects_invalid_json(client: TestClient, workspace: Path) -> None:
    resp = client.post(
        f"/api/workspace/dir?project_path={workspace}",
        content=b"{bad",
        headers={"content-type": "application/json"},
    )
    assert resp.status_code == 400
    assert resp.json()["error"] == "invalid JSON body"


def test_dir_create_requires_rel(client: TestClient, workspace: Path) -> None:
    resp = client.post(f"/api/workspace/dir?project_path={workspace}", json={})
    assert resp.status_code == 400
    assert "rel" in resp.json()["error"]


def test_dir_create_rejects_escaping_path(client: TestClient, workspace: Path) -> None:
    """A ``..`` traversal is rejected by resolve_safe_path → 400, not a write
    outside the workspace."""
    resp = client.post(
        f"/api/workspace/dir?project_path={workspace}",
        json={"rel": "../escape"},
    )
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# POST /api/workspace/git-init — explicit consent (D-2026-06-11-D)
# ---------------------------------------------------------------------------


def test_git_init_creates_repo_then_is_idempotent(client: TestClient, workspace: Path) -> None:
    resp = client.post(f"/api/workspace/git-init?project_path={workspace}")
    assert resp.status_code == 201
    body = resp.json()
    assert body["created"] is True
    assert body["ok"] is True
    assert (workspace / ".git").is_dir()

    # Second call is a 200 no-op (idempotent).
    again = client.post(f"/api/workspace/git-init?project_path={workspace}")
    assert again.status_code == 200
    assert again.json()["created"] is False


def test_git_init_requires_project_path(client: TestClient) -> None:
    resp = client.post("/api/workspace/git-init")
    assert resp.status_code == 400
