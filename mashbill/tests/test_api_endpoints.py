"""HTTP endpoint tests for the v0.4 project / canvas / tag surface.

Legacy ``/api/sketches/*`` endpoints were removed in v0.4 — this file
now covers only the new project-based shape.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from mashbill.broadcast import BroadcastHub
from mashbill.http_app import create_http_app


@pytest.fixture
def app_client(tmp_path: Path) -> tuple[TestClient, str]:
    # D-2026-06-11-D — Novel never auto-inits, but tests that exercise
    # tag/publish need a real repo, so the test seeds one. Endpoint tests
    # that exercise the needs_git_init path use a fresh tmp_path manually.
    from mashbill.git_store import init_workspace_repo

    init_workspace_repo(tmp_path)
    hub = BroadcastHub(enable_watchers=False)
    app = create_http_app(hub=hub)
    return TestClient(app), str(tmp_path)


# ---------------------------------------------------------------------------
# health + baseline
# ---------------------------------------------------------------------------


def test_health(app_client: tuple[TestClient, str]) -> None:
    client, _ = app_client
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["service"] == "mashbill"


def test_health_exposes_compat_versions(app_client: tuple[TestClient, str]) -> None:
    """The runtime compat banner (D-2026-06-20-N Phase D part c) reads the
    engine's wire ``schema_version`` + ``engine_version`` from /api/health and
    compares schema_version against the viewer's committed wire-contract."""
    from mashbill import __version__
    from mashbill.schema_export import SCHEMA_VERSION

    client, _ = app_client
    body = client.get("/api/health").json()
    assert body["schema_version"] == SCHEMA_VERSION
    assert body["engine_version"] == __version__


def test_list_empty(app_client: tuple[TestClient, str]) -> None:
    client, project_path = app_client
    resp = client.get("/api/projects", params={"project_path": project_path})
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"projects": [], "migrated": []}


def test_list_requires_project_path(app_client: tuple[TestClient, str]) -> None:
    client, _ = app_client
    resp = client.get("/api/projects")
    assert resp.status_code == 400


def test_nonexistent_project_path_is_404(app_client: tuple[TestClient, str]) -> None:
    client, _ = app_client
    resp = client.get(
        "/api/projects",
        params={"project_path": "/tmp/definitely-does-not-exist-plot-xyz-12345"},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# project CRUD
# ---------------------------------------------------------------------------


def _create(client: TestClient, project_path: str, pid: str, name: str) -> dict:
    resp = client.post(
        "/api/projects",
        params={"project_path": project_path},
        json={"id": pid, "name": name},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_create_then_list(app_client: tuple[TestClient, str]) -> None:
    client, project_path = app_client
    proj = _create(client, project_path, "alpha", "Alpha")
    assert proj["id"] == "alpha"
    assert proj["version"] == 3  # v0.13 Phase 0

    listed = client.get("/api/projects", params={"project_path": project_path}).json()
    assert [p["id"] for p in listed["projects"]] == ["alpha"]


def test_duplicate_create_is_409(app_client: tuple[TestClient, str]) -> None:
    client, project_path = app_client
    _create(client, project_path, "alpha", "Alpha")
    resp = client.post(
        "/api/projects",
        params={"project_path": project_path},
        json={"id": "alpha", "name": "Again"},
    )
    assert resp.status_code == 409


def test_create_missing_id_is_400(app_client: tuple[TestClient, str]) -> None:
    client, project_path = app_client
    resp = client.post(
        "/api/projects",
        params={"project_path": project_path},
        json={"name": "No ID"},
    )
    assert resp.status_code == 400


def test_project_get_returns_details_and_tags(
    app_client: tuple[TestClient, str],
) -> None:
    client, project_path = app_client
    _create(client, project_path, "alpha", "Alpha")
    resp = client.get(
        "/api/projects/alpha",
        params={"project_path": project_path},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == "alpha"
    assert body["feature_details"] == []
    assert body["tags"] == []


def test_project_rename(app_client: tuple[TestClient, str]) -> None:
    """v0.13 Phase 0: rename updates ProjectDoc.name only (no canvas node sync)."""
    client, project_path = app_client
    _create(client, project_path, "alpha", "Alpha")
    resp = client.patch(
        "/api/projects/alpha",
        params={"project_path": project_path},
        json={"name": "Renamed"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed"
    # foundation canvas no longer carries a project node — anchor label is
    # derived from ProjectDoc.name at render time.
    canvas_resp = client.get(
        "/api/projects/alpha/canvases/foundation",
        params={"project_path": project_path},
    )
    assert canvas_resp.status_code == 200
    assert all(n["kind"] != "project" for n in canvas_resp.json()["nodes"])


def test_project_rename_requires_name(app_client: tuple[TestClient, str]) -> None:
    client, project_path = app_client
    _create(client, project_path, "alpha", "Alpha")
    resp = client.patch(
        "/api/projects/alpha",
        params={"project_path": project_path},
        json={},
    )
    assert resp.status_code == 400


def test_project_delete(app_client: tuple[TestClient, str]) -> None:
    client, project_path = app_client
    _create(client, project_path, "alpha", "Alpha")
    resp = client.delete("/api/projects/alpha", params={"project_path": project_path})
    assert resp.status_code == 200
    resp = client.get("/api/projects/alpha", params={"project_path": project_path})
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# canvas GET/PUT
# ---------------------------------------------------------------------------


def test_canvas_get_returns_seeded_core(
    app_client: tuple[TestClient, str],
) -> None:
    """v0.13 Phase 0: foundation seeds Mission + Core value + Identity (no project)."""
    client, project_path = app_client
    _create(client, project_path, "alpha", "Alpha")
    resp = client.get(
        "/api/projects/alpha/canvases/foundation",
        params={"project_path": project_path},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["canvas_kind"] == "foundation"
    kinds = sorted({n["kind"] for n in body["nodes"] if n.get("kind")})
    assert kinds == ["core_value", "identity", "mission"]


def test_canvas_put_round_trips_actor(
    app_client: tuple[TestClient, str],
) -> None:
    client, project_path = app_client
    _create(client, project_path, "alpha", "Alpha")
    resp = client.get(
        "/api/projects/alpha/canvases/actors",
        params={"project_path": project_path},
    )
    canvas = resp.json()
    canvas["nodes"].append(
        {
            "id": "guest",
            "kind": "actor",
            "label": "Guest",
            "body": "",
            "x": 0,
            "y": 0,
            "width": 120,
            "height": 120,
            "color": "#fecaca",
            "shape": "circle",
            "icon": "user",
            "parent_id": None,
            "collapsed": False,
            "is_root": False,
            "mission": "",
            "core_values": "",
            "identity": "",
            "ref_actor_id": None,
        }
    )
    resp = client.put(
        "/api/projects/alpha/canvases/actors",
        params={"project_path": project_path},
        json=canvas,
    )
    assert resp.status_code == 200
    reloaded = client.get(
        "/api/projects/alpha/canvases/actors",
        params={"project_path": project_path},
    ).json()
    assert any(n["id"] == "guest" for n in reloaded["nodes"])


def test_project_publish_bumps_patch_creates_tag(
    app_client: tuple[TestClient, str],
) -> None:
    """v0.24.13 (D-2026-05-21-B) — POST /publish bumps blueprint
    version and creates a git tag at the resulting version name."""
    client, project_path = app_client
    _create(client, project_path, "alpha", "Alpha")
    # New project defaults to v0.1.0.
    proj = client.get(
        "/api/projects/alpha",
        params={"project_path": project_path},
    ).json()
    assert proj.get("blueprint_version") == "v0.1.0"
    resp = client.post(
        "/api/projects/alpha/publish",
        params={"project_path": project_path},
        json={"bump": "patch"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["from_version"] == "v0.1.0"
    assert body["to_version"] == "v0.1.1"
    # Project doc reflects the new version on next read.
    proj_after = client.get(
        "/api/projects/alpha",
        params={"project_path": project_path},
    ).json()
    assert proj_after["blueprint_version"] == "v0.1.1"
    # The tag list now contains v0.1.1.
    tags = client.get(
        "/api/projects/alpha/tags",
        params={"project_path": project_path},
    ).json()
    assert any(t["name"] == "v0.1.1" for t in tags["tags"])


def test_project_publish_minor_and_major_bumps(
    app_client: tuple[TestClient, str],
) -> None:
    client, project_path = app_client
    _create(client, project_path, "alpha", "Alpha")
    minor = client.post(
        "/api/projects/alpha/publish",
        params={"project_path": project_path},
        json={"bump": "minor"},
    ).json()
    assert minor["to_version"] == "v0.2.0"
    major = client.post(
        "/api/projects/alpha/publish",
        params={"project_path": project_path},
        json={"bump": "major"},
    ).json()
    assert major["from_version"] == "v0.2.0"
    assert major["to_version"] == "v1.0.0"


def test_project_at_tag_returns_snapshot(
    app_client: tuple[TestClient, str],
) -> None:
    """v0.24.14 (D-2026-05-21-C) — GET /at-tag/{tag} returns the
    project + all canvases at the given git tag without touching the
    working tree."""
    client, project_path = app_client
    _create(client, project_path, "alpha", "Alpha")
    # Snapshot v0.1.1.
    pub = client.post(
        "/api/projects/alpha/publish",
        params={"project_path": project_path},
        json={"bump": "patch"},
    )
    assert pub.status_code == 201
    # Mutate the working tree AFTER the tag to confirm the snapshot
    # endpoint returns the tag-time state, not the current state.
    actors = client.get(
        "/api/projects/alpha/canvases/actors",
        params={"project_path": project_path},
    ).json()
    actors["nodes"].append(
        {"id": "after-tag", "kind": "actor", "label": "After tag", "body": ""},
    )
    client.put(
        "/api/projects/alpha/canvases/actors",
        params={"project_path": project_path},
        json=actors,
    )
    # Read at the tag.
    snap = client.get(
        "/api/projects/alpha/at-tag/v0.1.1",
        params={"project_path": project_path},
    )
    assert snap.status_code == 200, snap.text
    body = snap.json()
    assert body["project"]["blueprint_version"] == "v0.1.1"
    snap_actors = body["canvases"]["actors"]
    # 'after-tag' node was added AFTER the tag — must NOT appear.
    assert not any(n["id"] == "after-tag" for n in snap_actors["nodes"])


def test_project_at_tag_404_for_unknown_tag(
    app_client: tuple[TestClient, str],
) -> None:
    client, project_path = app_client
    _create(client, project_path, "alpha", "Alpha")
    resp = client.get(
        "/api/projects/alpha/at-tag/v9.9.9",
        params={"project_path": project_path},
    )
    assert resp.status_code == 404


def test_project_publish_invalid_bump_is_400(
    app_client: tuple[TestClient, str],
) -> None:
    client, project_path = app_client
    _create(client, project_path, "alpha", "Alpha")
    resp = client.post(
        "/api/projects/alpha/publish",
        params={"project_path": project_path},
        json={"bump": "huge"},
    )
    assert resp.status_code == 400
def test_canvas_put_overview_auto_creates_detail(
    app_client: tuple[TestClient, str],
) -> None:
    client, project_path = app_client
    _create(client, project_path, "alpha", "Alpha")
    payload = {
        "canvas_id": "services",
        "canvas_kind": "services",
        "nodes": [
            {
                "id": "default-cat",
                "kind": "category",
                "label": "Default",
                "body": "",
                "x": 0,
                "y": -100,
                "width": 200,
                "height": 100,
                "color": "#e2e8f0",
                "shape": "rounded",
                "icon": None,
                "parent_id": None,
                "collapsed": False,
                "is_root": False,
                "mission": "",
                "core_values": "",
                "identity": "",
                "ref_actor_id": None,
            },
            {
                # D-2026-06-17-D — the detail canvas drills into a *feature*
                # (the sole drill target), so auto-create keys off features,
                # not services. The drill-target node on the overview is a
                # feature.
                "id": "order",
                "kind": "feature",
                "label": "주문",
                "body": "",
                "x": 0,
                "y": 0,
                "width": 160,
                "height": 80,
                "color": "#bae6fd",
                "shape": "rounded",
                "icon": "zap",
                "parent_id": "default-cat",
                "collapsed": False,
                "is_root": False,
                "mission": "",
                "core_values": "",
                "identity": "",
                "ref_actor_id": None,
            },
        ],
        "edges": [],
    }
    resp = client.put(
        "/api/projects/alpha/canvases/services",
        params={"project_path": project_path},
        json=payload,
    )
    assert resp.status_code == 200
    assert resp.json()["sync"]["created"] == ["order"]
    detail = client.get(
        "/api/projects/alpha/canvases/feature",
        params={"project_path": project_path, "service_id": "order"},
    )
    assert detail.status_code == 200
    assert detail.json()["feature_ref"] == "order"


def test_canvas_get_unknown_kind_is_400(
    app_client: tuple[TestClient, str],
) -> None:
    client, project_path = app_client
    _create(client, project_path, "alpha", "Alpha")
    resp = client.get(
        "/api/projects/alpha/canvases/bogus",
        params={"project_path": project_path},
    )
    assert resp.status_code == 400


def test_canvas_put_bad_body_is_422(
    app_client: tuple[TestClient, str],
) -> None:
    client, project_path = app_client
    _create(client, project_path, "alpha", "Alpha")
    # Edge referencing a non-existent node → model validator rejects.
    resp = client.put(
        "/api/projects/alpha/canvases/actors",
        params={"project_path": project_path},
        json={
            "canvas_id": "actors",
            "nodes": [],
            "edges": [{"id": "e1", "source": "ghost", "target": "nowhere"}],
        },
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# tags (session bookmarks)
# ---------------------------------------------------------------------------


def test_tags_empty_on_new_project(app_client: tuple[TestClient, str]) -> None:
    client, project_path = app_client
    _create(client, project_path, "alpha", "Alpha")
    resp = client.get(
        "/api/projects/alpha/tags",
        params={"project_path": project_path},
    )
    assert resp.status_code == 200
    assert resp.json() == {"tags": []}


def test_tag_create_then_list(app_client: tuple[TestClient, str]) -> None:
    client, project_path = app_client
    _create(client, project_path, "alpha", "Alpha")
    resp = client.post(
        "/api/projects/alpha/tags",
        params={"project_path": project_path},
        json={"name": "session-start", "message": "kickoff"},
    )
    assert resp.status_code == 201
    assert resp.json()["name"] == "session-start"

    listed = client.get(
        "/api/projects/alpha/tags",
        params={"project_path": project_path},
    ).json()
    assert [t["name"] for t in listed["tags"]] == ["session-start"]


def test_tag_duplicate_is_409(app_client: tuple[TestClient, str]) -> None:
    client, project_path = app_client
    _create(client, project_path, "alpha", "Alpha")
    client.post(
        "/api/projects/alpha/tags",
        params={"project_path": project_path},
        json={"name": "dup"},
    )
    resp = client.post(
        "/api/projects/alpha/tags",
        params={"project_path": project_path},
        json={"name": "dup"},
    )
    assert resp.status_code == 409


def test_tag_delete(app_client: tuple[TestClient, str]) -> None:
    client, project_path = app_client
    _create(client, project_path, "alpha", "Alpha")
    client.post(
        "/api/projects/alpha/tags",
        params={"project_path": project_path},
        json={"name": "doomed"},
    )
    resp = client.delete(
        "/api/projects/alpha/tags/doomed",
        params={"project_path": project_path},
    )
    assert resp.status_code == 200
    listed = client.get(
        "/api/projects/alpha/tags",
        params={"project_path": project_path},
    ).json()
    assert listed == {"tags": []}


def test_tag_delete_unknown_is_404(app_client: tuple[TestClient, str]) -> None:
    client, project_path = app_client
    _create(client, project_path, "alpha", "Alpha")
    resp = client.delete(
        "/api/projects/alpha/tags/ghost",
        params={"project_path": project_path},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# v0.1 auto-migration on list
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# v0.7 file + folder surface (Inspector MD editor)
# ---------------------------------------------------------------------------


def test_file_put_and_get_roundtrip(app_client: tuple[TestClient, str]) -> None:
    client, project_path = app_client
    _create(client, project_path, "alpha", "Alpha")
    put = client.put(
        "/api/files",
        params={
            "project_path": project_path,
            "project_id": "alpha",
            "path": "notes.md",
        },
        json={"content": "# Hello\n일상 속..."},
    )
    assert put.status_code == 200
    got = client.get(
        "/api/files",
        params={
            "project_path": project_path,
            "project_id": "alpha",
            "path": "notes.md",
        },
    )
    assert got.status_code == 200
    assert got.json()["content"] == "# Hello\n일상 속..."


def test_file_get_missing_returns_empty_content(
    app_client: tuple[TestClient, str],
) -> None:
    client, project_path = app_client
    _create(client, project_path, "alpha", "Alpha")
    resp = client.get(
        "/api/files",
        params={
            "project_path": project_path,
            "project_id": "alpha",
            "path": "nothing.md",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["content"] == ""


def test_file_requires_project_id(app_client: tuple[TestClient, str]) -> None:
    client, project_path = app_client
    _create(client, project_path, "alpha", "Alpha")
    resp = client.get(
        "/api/files",
        params={"project_path": project_path, "path": "notes.md"},
    )
    assert resp.status_code == 400


def test_file_rejects_path_traversal(app_client: tuple[TestClient, str]) -> None:
    client, project_path = app_client
    _create(client, project_path, "alpha", "Alpha")
    resp = client.get(
        "/api/files",
        params={
            "project_path": project_path,
            "project_id": "alpha",
            "path": "../../../etc/passwd",
        },
    )
    assert resp.status_code == 400


def test_file_rejects_absolute_path(app_client: tuple[TestClient, str]) -> None:
    client, project_path = app_client
    _create(client, project_path, "alpha", "Alpha")
    resp = client.get(
        "/api/files",
        params={
            "project_path": project_path,
            "project_id": "alpha",
            "path": "/etc/passwd",
        },
    )
    assert resp.status_code == 400


def test_file_cannot_climb_into_other_project(
    app_client: tuple[TestClient, str],
) -> None:
    """v0.8 scoping: a file API call for project ``alpha`` can't walk up
    out of its own directory via ``../beta/...``. The escaping path is
    rejected by ``resolve_safe_path`` regardless of whether the climbed-to
    target exists — under one-project-per-dir (D-2026-06-21-AA) a sibling
    ``beta`` can't even share ``alpha``'s root, so only ``alpha`` is created."""
    client, project_path = app_client
    _create(client, project_path, "alpha", "Alpha")
    resp = client.get(
        "/api/files",
        params={
            "project_path": project_path,
            "project_id": "alpha",
            "path": "../beta/project.json",
        },
    )
    assert resp.status_code == 400


def test_file_rejects_disallowed_extension(
    app_client: tuple[TestClient, str],
) -> None:
    client, project_path = app_client
    _create(client, project_path, "alpha", "Alpha")
    resp = client.put(
        "/api/files",
        params={
            "project_path": project_path,
            "project_id": "alpha",
            "path": "foo.py",
        },
        json={"content": "import os"},
    )
    assert resp.status_code == 400


def test_file_put_does_not_touch_canvas(
    app_client: tuple[TestClient, str],
) -> None:
    """v0.9: writing a node's ``details.md`` is a leaf operation — the
    node's typed fields in canvas.json are untouched. (No more body cache
    sync; typed fields are the canvas-side source.)"""
    client, project_path = app_client
    _create(client, project_path, "alpha", "Alpha")
    core_before = client.get(
        "/api/projects/alpha/canvases/foundation",
        params={"project_path": project_path},
    ).json()
    mission = next(n for n in core_before["nodes"] if n["kind"] == "mission")
    mission["details_path"] = "core/mission-mission/details.md"
    client.put(
        "/api/projects/alpha/canvases/foundation",
        params={"project_path": project_path},
        json=core_before,
    ).raise_for_status()

    put = client.put(
        "/api/files",
        params={
            "project_path": project_path,
            "project_id": "alpha",
            "path": "core/mission-mission/details.md",
            "node_id": mission["id"],
        },
        json={"content": "긴 이야기..."},
    )
    assert put.status_code == 200
    body = put.json()
    assert "preview" not in body  # no canvas-side caching anymore

    core_after = client.get(
        "/api/projects/alpha/canvases/foundation",
        params={"project_path": project_path},
    ).json()
    refreshed_mission = next(n for n in core_after["nodes"] if n["id"] == mission["id"])
    # v0.17 Phase 1 (D-2026-05-16-A): Foundation typed-text kinds carry no
    # details_path in JSON. The absorption migrator clears the user-set
    # custom path on Mission/CoreValue/Identity unconditionally — JSON
    # SSOT now covers all MD-syntax fields (typed + body); per-node MD
    # editing surface is gone. The test's premise — "writing a file via
    # /api/files does not touch the canvas as a side-effect" — still
    # holds: the canvas mutation that cleared details_path was the PUT
    # at line above, not the file write.
    assert refreshed_mission["details_path"] is None


def test_folder_post_creates_unique_path(
    app_client: tuple[TestClient, str],
) -> None:
    client, project_path = app_client
    _create(client, project_path, "alpha", "Alpha")
    first = client.post(
        "/api/folders",
        params={"project_path": project_path},
        json={"project_id": "alpha", "path": "core/mission-mission"},
    )
    assert first.status_code == 201
    assert first.json()["path"] == "core/mission-mission"
    # Second request with the same name → server appends ``-2``.
    second = client.post(
        "/api/folders",
        params={"project_path": project_path},
        json={"project_id": "alpha", "path": "core/mission-mission"},
    )
    assert second.status_code == 201
    assert second.json()["path"] == "core/mission-mission-2"
    # index.md is seeded inside the created folder (under the project scope).
    # R9 (D-2026-06-10-G): artifacts live under .noory/novel/. S2: flat layout —
    # no {project_id} segment.
    assert (
        Path(project_path) / ".noory/novel/core/mission-mission/index.md"
    ).is_file()


def test_list_migrates_v01_sketches_silently(
    app_client: tuple[TestClient, str],
) -> None:
    client, project_path = app_client
    sketches_dir = Path(project_path) / ".plot" / "sketches"
    sketches_dir.mkdir(parents=True, exist_ok=True)
    (sketches_dir / "legacy.json").write_text(
        json.dumps(
            {
                "id": "legacy",
                "name": "Legacy",
                "created": "2026-01-01",
                "updated": "2026-01-01T00:00:00+00:00",
                "version": 1,
                "nodes": [
                    {
                        "id": "core-root",
                        "label": "Legacy",
                        "kind": "core",
                    }
                ],
                "edges": [],
            }
        ),
        encoding="utf-8",
    )
    resp = client.get("/api/projects", params={"project_path": project_path})
    assert resp.status_code == 200
    body = resp.json()
    assert "legacy" in body["migrated"]
    assert any(p["id"] == "legacy" for p in body["projects"])


# ---------------------------------------------------------------------------
# format F publish over HTTP (INT-g, D-2026-06-22-G) — mirrors the MCP tools
# ---------------------------------------------------------------------------


def _add_service_via_store(project_path: str, service_id: str) -> None:
    """Drop a bare service node onto the services canvas through the store
    (the viewer would do this via PUT; the endpoint test only needs the node)."""
    from mashbill.folder_io import read_canvas, write_canvas
    from mashbill.models import ServiceNode
    from mashbill.workspace import resolve_plot_root

    plot_root = resolve_plot_root(project_path)
    services = read_canvas(plot_root, "alpha", "services")
    write_canvas(
        plot_root,
        "alpha",
        services.model_copy(update={"nodes": [ServiceNode(id=service_id, label="Svc")]}),
    )


def test_format_f_snapshot_endpoint(app_client: tuple[TestClient, str]) -> None:
    client, project_path = app_client
    _create(client, project_path, "alpha", "Alpha")
    resp = client.post(
        "/api/projects/alpha/publish/snapshot",
        params={"project_path": project_path},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["scope"] == "project"
    assert body["release"] == "vP1"
    assert body["format_f_version"] == 1


def test_format_f_snapshot_unknown_project_is_404(
    app_client: tuple[TestClient, str],
) -> None:
    client, project_path = app_client
    resp = client.post(
        "/api/projects/ghost/publish/snapshot",
        params={"project_path": project_path},
    )
    assert resp.status_code == 404


def test_format_f_service_publish_endpoint(app_client: tuple[TestClient, str]) -> None:
    client, project_path = app_client
    _create(client, project_path, "alpha", "Alpha")
    client.post(
        "/api/projects/alpha/publish/snapshot",
        params={"project_path": project_path},
    )  # vP1 (bootstrap)
    _add_service_via_store(project_path, "svc1")
    resp = client.post(
        "/api/projects/alpha/services/svc1/publish",
        params={"project_path": project_path},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["scope"] == "service"
    assert body["based_on"] == "vP1"
    assert body["service"].startswith("service/")


def test_format_f_service_without_snapshot_is_409(
    app_client: tuple[TestClient, str],
) -> None:
    """Bootstrap invariant surfaced over HTTP: a vS without a vP is a 409."""
    client, project_path = app_client
    _create(client, project_path, "alpha", "Alpha")
    _add_service_via_store(project_path, "svc1")
    resp = client.post(
        "/api/projects/alpha/services/svc1/publish",
        params={"project_path": project_path},
    )
    assert resp.status_code == 409, resp.text
    assert "snapshot" in resp.json()["error"]


def test_format_f_service_unknown_service_is_404(
    app_client: tuple[TestClient, str],
) -> None:
    client, project_path = app_client
    _create(client, project_path, "alpha", "Alpha")
    client.post(
        "/api/projects/alpha/publish/snapshot",
        params={"project_path": project_path},
    )
    resp = client.post(
        "/api/projects/alpha/services/ghost/publish",
        params={"project_path": project_path},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# workspace discovery + dir-tree picker (v0.32.0)
# ---------------------------------------------------------------------------


def test_workspace_discover_empty(app_client: tuple[TestClient, str]) -> None:
    client, project_path = app_client
    resp = client.get("/api/workspace/projects", params={"project_path": project_path})
    assert resp.status_code == 200
    body = resp.json()
    assert body["projects"] == []
    assert "migrated" in body


def test_workspace_discover_finds_nested(app_client: tuple[TestClient, str]) -> None:
    client, project_path = app_client
    sub = Path(project_path) / "pkg"
    sub.mkdir()
    _create(client, str(sub), "proj-x", "X")
    resp = client.get("/api/workspace/projects", params={"project_path": project_path})
    assert resp.status_code == 200
    projects = resp.json()["projects"]
    assert len(projects) == 1
    assert projects[0]["dir"] == "pkg"
    assert projects[0]["project"]["id"] == "proj-x"


def test_workspace_discover_missing_param(app_client: tuple[TestClient, str]) -> None:
    client, _ = app_client
    assert client.get("/api/workspace/projects").status_code == 400


def test_workspace_discover_bad_root(app_client: tuple[TestClient, str]) -> None:
    client, project_path = app_client
    resp = client.get(
        "/api/workspace/projects",
        params={"project_path": str(Path(project_path) / "does-not-exist")},
    )
    assert resp.status_code == 404


def test_dir_tree_marks_has_plot(app_client: tuple[TestClient, str]) -> None:
    client, project_path = app_client
    (Path(project_path) / "a").mkdir()
    _create(client, str(Path(project_path) / "a"), "proj-a", "A")
    (Path(project_path) / "b").mkdir()
    resp = client.get("/api/workspace/tree", params={"project_path": project_path})
    assert resp.status_code == 200
    root = resp.json()["root"]
    assert root["rel"] == "."
    by_name = {c["name"]: c for c in root["children"]}
    assert by_name["a"]["has_plot"] is True
    assert by_name["b"]["has_plot"] is False


def test_dir_tree_missing_param(app_client: tuple[TestClient, str]) -> None:
    client, _ = app_client
    assert client.get("/api/workspace/tree").status_code == 400


# ---------------------------------------------------------------------------
# workspace dir create — v0.37.0 (D-2026-05-31-AC): "new folder" in the
# Add-a-Project picker so a project can start in a directory that does not
# exist yet.
# ---------------------------------------------------------------------------


def test_create_workspace_dir(app_client: tuple[TestClient, str]) -> None:
    client, project_path = app_client
    resp = client.post(
        "/api/workspace/dir",
        params={"project_path": project_path},
        json={"rel": "banana"},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["rel"] == "banana"
    assert (Path(project_path) / "banana").is_dir()


def test_create_workspace_dir_nested(app_client: tuple[TestClient, str]) -> None:
    client, project_path = app_client
    resp = client.post(
        "/api/workspace/dir",
        params={"project_path": project_path},
        json={"rel": "apps/admin"},
    )
    assert resp.status_code == 201, resp.text
    assert (Path(project_path) / "apps" / "admin").is_dir()


def test_create_workspace_dir_rejects_traversal(app_client: tuple[TestClient, str]) -> None:
    client, project_path = app_client
    resp = client.post(
        "/api/workspace/dir",
        params={"project_path": project_path},
        json={"rel": "../escape"},
    )
    assert resp.status_code == 400


def test_create_workspace_dir_requires_rel(app_client: tuple[TestClient, str]) -> None:
    client, project_path = app_client
    resp = client.post(
        "/api/workspace/dir",
        params={"project_path": project_path},
        json={},
    )
    assert resp.status_code == 400
