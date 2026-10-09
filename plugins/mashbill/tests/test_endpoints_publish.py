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
import re
import subprocess
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import pytest
from starlette.testclient import TestClient

from mashbill.blueprint_publish import _bump_blueprint_version
from mashbill.broadcast import BroadcastHub
from mashbill.chat_provider import ChatProviderSelection, write_selection
from mashbill.chat_session import ChatProvider, ChatSessionRegistry, ChatStreamEvent
from mashbill.folder_io import _project_dir, read_canvas, write_canvas
from mashbill.format_f_slugs import write_slug_store
from mashbill.git_store import init_workspace_repo, list_tags, tag_snapshot
from mashbill.http_app import create_http_app
from mashbill.models import ActorNode, ServiceNode
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


@pytest.mark.parametrize(
    ("method", "suffix", "body"),
    [
        ("POST", "/publish", {"bump": "patch"}),
        ("GET", "/publish/status", None),
        ("GET", "/slugs", None),
        ("POST", "/publish/slug-proposals", {"scope": "project", "suggest": False}),
    ],
)
def test_publish_routes_reject_wrong_project_id_without_changes(
    client: TestClient, workspace: Path, method: str, suffix: str, body: dict[str, Any] | None
) -> None:
    plot_root = _make_project(workspace)
    init_workspace_repo(workspace)
    before = {p.relative_to(plot_root): p.read_bytes() for p in plot_root.rglob("*") if p.is_file()}
    tags_before = list_tags(workspace)
    response = client.request(
        method, f"/api/projects/wrong{suffix}?project_path={workspace}", json=body
    )
    assert response.status_code == 404
    assert response.json() == {"error": "project not found: wrong"}
    assert {
        p.relative_to(plot_root): p.read_bytes() for p in plot_root.rglob("*") if p.is_file()
    } == before
    assert list_tags(workspace) == tags_before


def _foundation_canvas(plot_root: Path) -> Path:
    return _project_dir(plot_root, "alpha") / "foundation" / "canvas.json"


def _write_canvas(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _publish_seeded_foundation(
    client: TestClient,
    workspace: Path,
    *,
    edges: list[dict[str, Any]] | None = None,
) -> tuple[Path, dict[str, Any]]:
    plot_root = _make_project(workspace)
    init_workspace_repo(workspace)
    canvas = _foundation_canvas(plot_root)
    payload: dict[str, Any] = {
        "canvas_id": "foundation",
        "canvas_kind": "foundation",
        "feature_ref": None,
        "nodes": [
            {
                "id": "mission-1",
                "kind": "mission",
                "label": "Original mission",
                "x": 10,
                "y": 20,
                "width": 160,
                "height": 80,
                "color": "#ffffff",
                "shape": "rounded",
                "icon": None,
                "collapsed": False,
                "statement": "Build the right thing",
            },
            {
                "id": "mission-2",
                "kind": "mission",
                "label": "Second mission",
                "x": 30,
                "y": 40,
                "width": 160,
                "height": 80,
                "color": "#eeeeee",
                "shape": "rounded",
                "icon": None,
                "collapsed": False,
                "statement": "Keep it understandable",
            },
        ],
        "edges": edges or [],
    }
    _write_canvas(canvas, payload)
    response = client.post(
        f"/api/projects/alpha/publish?project_path={workspace}",
        json={"bump": "patch"},
    )
    assert response.status_code == 201, response.text
    assert response.json()["to_version"] == "v0.1.1"
    return canvas, payload


def _assert_publish_unchanged(client: TestClient, workspace: Path) -> None:
    response = client.post(
        f"/api/projects/alpha/publish?project_path={workspace}",
        json={"bump": "patch"},
    )
    assert response.status_code == 409, response.text
    assert response.json()["unchanged"] is True
    project = client.get(f"/api/projects/alpha?project_path={workspace}").json()
    assert project["blueprint_version"] == "v0.1.1"
    assert [tag["name"] for tag in list_tags(workspace)] == ["v0.1.1"]


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


def test_slug_map_returns_stored_registry_without_writing(
    client: TestClient, workspace: Path
) -> None:
    plot_root = _make_project(workspace)
    write_slug_store(
        plot_root,
        "alpha",
        {"node-2": "feature/checkout", "node-1": "mission"},
    )
    slug_file = _project_dir(plot_root, "alpha") / "_slugs.json"
    before = slug_file.read_bytes()

    resp = client.get(
        f"/api/projects/alpha/slugs?project_path={workspace}",
    )

    assert resp.status_code == 200
    assert resp.json() == {"slugs": {"node-2": "feature/checkout", "node-1": "mission"}}
    assert slug_file.read_bytes() == before


def test_slug_map_returns_empty_without_minting_registry(
    client: TestClient, workspace: Path
) -> None:
    plot_root = _make_project(workspace)
    slug_file = _project_dir(plot_root, "alpha") / "_slugs.json"
    assert not slug_file.exists()

    resp = client.get(
        f"/api/projects/alpha/slugs?project_path={workspace}",
    )

    assert resp.status_code == 200
    assert resp.json() == {"slugs": {}}
    assert not slug_file.exists()


def test_slug_map_404_when_project_missing(client: TestClient, workspace: Path) -> None:
    resolve_plot_root(str(workspace))

    resp = client.get(
        f"/api/projects/ghost/slugs?project_path={workspace}",
    )

    assert resp.status_code == 404
    assert resp.json() == {"error": "project not found: ghost"}


def test_slug_map_reuses_stored_registry_validation(client: TestClient, workspace: Path) -> None:
    plot_root = _make_project(workspace)
    slug_file = _project_dir(plot_root, "alpha") / "_slugs.json"
    slug_file.write_text(json.dumps({"node-1": "../escape"}), encoding="utf-8")

    resp = client.get(
        f"/api/projects/alpha/slugs?project_path={workspace}",
    )

    assert resp.status_code == 400
    assert "_slugs.json has an invalid id" in resp.json()["error"]
    assert json.loads(slug_file.read_text(encoding="utf-8")) == {"node-1": "../escape"}


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
    assert not (_project_dir(resolve_plot_root(str(workspace)), "alpha") / "published").exists()


def test_publish_status_without_git_reports_changed(client: TestClient, workspace: Path) -> None:
    _make_project(workspace)

    resp = client.get(
        f"/api/projects/alpha/publish/status?project_path={workspace}",
    )

    assert resp.status_code == 200
    assert resp.json() == {"current_version": "v0.1.0", "changed": True}


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
    assert not (_project_dir(resolve_plot_root(str(workspace)), "alpha") / "published").exists()


def test_publish_ignores_node_position_changes(client: TestClient, workspace: Path) -> None:
    canvas, payload = _publish_seeded_foundation(client, workspace)
    node = payload["nodes"][0]
    node["x"] = 700
    node["y"] = -300
    _write_canvas(canvas, payload)

    _assert_publish_unchanged(client, workspace)


def test_publish_ignores_node_color_and_width_changes(client: TestClient, workspace: Path) -> None:
    canvas, payload = _publish_seeded_foundation(client, workspace)
    node = payload["nodes"][0]
    node["color"] = "#123456"
    node["width"] = 420
    _write_canvas(canvas, payload)

    _assert_publish_unchanged(client, workspace)


def test_publish_detects_node_label_change(client: TestClient, workspace: Path) -> None:
    canvas, payload = _publish_seeded_foundation(client, workspace)
    payload["nodes"][0]["label"] = "Changed mission"
    _write_canvas(canvas, payload)

    response = client.get(f"/api/projects/alpha/publish/status?project_path={workspace}")
    assert response.json() == {"current_version": "v0.1.1", "changed": True}


def test_publish_ignores_edge_handle_but_detects_added_edge(
    client: TestClient, workspace: Path
) -> None:
    canvas, payload = _publish_seeded_foundation(
        client,
        workspace,
        edges=[
            {
                "id": "edge-1",
                "source": "mission-1",
                "target": "mission-2",
                "sourceHandle": "right",
                "targetHandle": "left",
                "label": "supports",
                "style": "solid",
                "directed": True,
                "relation": "flow",
                "action_verb": None,
                "value_form": [],
            }
        ],
    )
    payload["edges"][0]["sourceHandle"] = "bottom"
    _write_canvas(canvas, payload)
    _assert_publish_unchanged(client, workspace)

    payload["edges"].append(
        {
            "id": "edge-2",
            "source": "mission-2",
            "target": "mission-1",
            "label": "informs",
        }
    )
    _write_canvas(canvas, payload)
    response = client.get(f"/api/projects/alpha/publish/status?project_path={workspace}")
    assert response.json() == {"current_version": "v0.1.1", "changed": True}


def test_publish_detects_canvas_change_when_novel_data_is_gitignored(
    client: TestClient, workspace: Path
) -> None:
    plot_root = _make_project(workspace)
    init_workspace_repo(workspace)
    (workspace / ".gitignore").write_text(".noory/novel/\n", encoding="utf-8")
    canvas = _foundation_canvas(plot_root)
    payload = json.loads(canvas.read_text(encoding="utf-8"))
    payload["nodes"] = [{"id": "mission-1", "kind": "mission", "label": "Original"}]
    _write_canvas(canvas, payload)
    first = client.post(
        f"/api/projects/alpha/publish?project_path={workspace}",
        json={"bump": "patch"},
    )
    assert first.status_code == 201, first.text

    payload["nodes"][0]["label"] = "Changed"
    _write_canvas(canvas, payload)

    response = client.get(f"/api/projects/alpha/publish/status?project_path={workspace}")
    assert response.json() == {"current_version": "v0.1.1", "changed": True}


def test_publish_uses_content_fingerprint_when_novel_data_is_gitignored(
    client: TestClient, workspace: Path
) -> None:
    plot_root = _make_project(workspace)
    init_workspace_repo(workspace)
    (workspace / ".gitignore").write_text(".noory/novel/\n", encoding="utf-8")
    canvas = _foundation_canvas(plot_root)
    payload = json.loads(canvas.read_text(encoding="utf-8"))
    payload["nodes"] = [
        {"id": "mission-1", "kind": "mission", "label": "Original", "x": 10, "y": 20}
    ]
    _write_canvas(canvas, payload)

    first = client.post(
        f"/api/projects/alpha/publish?project_path={workspace}",
        json={"bump": "patch"},
    )
    assert first.status_code == 201, first.text

    _assert_publish_unchanged(client, workspace)

    payload["nodes"][0]["x"] = 999
    payload["nodes"][0]["y"] = -999
    _write_canvas(canvas, payload)
    _assert_publish_unchanged(client, workspace)

    payload["nodes"][0]["label"] = "Changed"
    _write_canvas(canvas, payload)
    response = client.get(f"/api/projects/alpha/publish/status?project_path={workspace}")
    assert response.json() == {"current_version": "v0.1.1", "changed": True}


def test_publish_tag_message_includes_content_fingerprint_after_user_message(
    client: TestClient, workspace: Path
) -> None:
    _make_project(workspace)
    init_workspace_repo(workspace)

    response = client.post(
        f"/api/projects/alpha/publish?project_path={workspace}",
        json={"bump": "patch", "message": "Ready for review"},
    )
    assert response.status_code == 201, response.text

    tag_message = subprocess.run(
        ["git", "tag", "-l", "v0.1.1", "--format=%(contents)"],
        cwd=workspace,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.rstrip("\n")
    assert re.fullmatch(
        r"Ready for review\n\nNovel-Blueprint-Content: sha256:[0-9a-f]{64}",
        tag_message,
    )


def test_publish_falls_back_to_file_comparison_for_legacy_tag(
    client: TestClient, workspace: Path
) -> None:
    plot_root = _make_project(workspace)
    init_workspace_repo(workspace)
    canvas = _foundation_canvas(plot_root)
    payload = json.loads(canvas.read_text(encoding="utf-8"))
    payload["nodes"] = [{"id": "mission-1", "kind": "mission", "label": "Original"}]
    _write_canvas(canvas, payload)
    subprocess.run(["git", "add", ".noory/novel"], cwd=workspace, check=True)
    identity = [
        "-c",
        "user.name=Legacy User",
        "-c",
        "user.email=legacy@example.com",
    ]
    subprocess.run(
        ["git", *identity, "commit", "-m", "legacy publish"],
        cwd=workspace,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", *identity, "tag", "-a", "v0.1.0", "-m", "legacy publish"],
        cwd=workspace,
        check=True,
    )

    response = client.get(f"/api/projects/alpha/publish/status?project_path={workspace}")
    assert response.json() == {"current_version": "v0.1.0", "changed": False}

    payload["nodes"][0]["label"] = "Changed"
    _write_canvas(canvas, payload)
    response = client.get(f"/api/projects/alpha/publish/status?project_path={workspace}")
    assert response.json() == {"current_version": "v0.1.0", "changed": True}


def test_publish_ignores_node_array_order(client: TestClient, workspace: Path) -> None:
    canvas, payload = _publish_seeded_foundation(client, workspace)
    payload["nodes"] = list(reversed(payload["nodes"]))
    _write_canvas(canvas, payload)

    _assert_publish_unchanged(client, workspace)


def test_publish_treats_unreadable_canvas_json_as_changed(
    client: TestClient, workspace: Path
) -> None:
    canvas, _ = _publish_seeded_foundation(client, workspace)
    canvas.write_text("{not json", encoding="utf-8")

    response = client.get(f"/api/projects/alpha/publish/status?project_path={workspace}")
    assert response.json() == {"current_version": "v0.1.1", "changed": True}


# ---------------------------------------------------------------------------
# format-F endpoints — project_path guards
# ---------------------------------------------------------------------------


def test_publish_response_includes_format_f_manifest(client: TestClient, workspace: Path) -> None:
    _make_project(workspace)
    init_workspace_repo(workspace)

    resp = client.post(
        f"/api/projects/alpha/publish?project_path={workspace}",
        json={"bump": "patch"},
    )

    assert resp.status_code == 201
    assert resp.json()["manifest"]["release"] == "vP1"
    assert resp.json()["manifest"]["blueprint_version"] == "v0.1.1"


def test_snapshot_route_is_removed(client: TestClient) -> None:
    resp = client.post("/api/projects/alpha/publish/snapshot")
    assert resp.status_code in (404, 405)


def test_service_publish_requires_project_path(client: TestClient) -> None:
    resp = client.post("/api/projects/alpha/services/svc1/publish")
    assert resp.status_code == 400
    assert "project_path" in resp.json()["error"]


class _ProposalProvider(ChatProvider):
    def __init__(self, reply: str) -> None:
        self.reply = reply
        self.calls: list[str] = []

    async def complete_once(self, prompt: str, *, model: str | None = None) -> str:
        self.calls.append(prompt)
        return self.reply

    def stream_turn(self, user_message: str) -> AsyncIterator[ChatStreamEvent]:
        raise NotImplementedError


def _proposal_client(provider: _ProposalProvider) -> TestClient:
    registry = ChatSessionRegistry(factory=lambda _root, _name: provider)
    return TestClient(
        create_http_app(
            hub=BroadcastHub(enable_watchers=False),
            chat_registry_instance=registry,
        )
    )


def test_slug_proposals_endpoint_returns_suggestions(workspace: Path) -> None:
    plot_root = _make_project(workspace)
    actors = read_canvas(plot_root, "alpha", "actors")
    write_canvas(
        plot_root,
        "alpha",
        actors.model_copy(
            update={
                "nodes": [
                    ActorNode(id="fixed", label="관리자"),
                    ActorNode(id="customer", label="Customer"),
                    ActorNode(id="operator", label="운영자"),
                ]
            }
        ),
    )
    write_slug_store(plot_root, "alpha", {"fixed": "actor/admin"})
    write_selection(plot_root, ChatProviderSelection(provider="claude-code", model="sonnet"))
    provider = _ProposalProvider('{"operator":"operator"}')
    client = _proposal_client(provider)

    response = client.post(
        f"/api/projects/alpha/publish/slug-proposals?project_path={workspace}",
        json={"scope": "project", "suggest": True},
    )

    assert response.status_code == 200
    assert response.json() == {
        "needed": [
            {
                "node_id": "operator",
                "kind": "actor",
                "label": "운영자",
                "proposed": "operator",
                "deduped": False,
            }
        ],
        "taken": ["actor/admin", "actor/customer"],
        "ai_status": "ok",
    }
    assert len(provider.calls) == 1


def test_slug_proposals_endpoint_rejects_bad_scope(client: TestClient, workspace: Path) -> None:
    _make_project(workspace)

    response = client.post(
        f"/api/projects/alpha/publish/slug-proposals?project_path={workspace}",
        json={"scope": "everything"},
    )

    assert response.status_code == 400


def test_slug_proposals_endpoint_returns_404_for_missing_project(
    client: TestClient, workspace: Path
) -> None:
    resolve_plot_root(str(workspace))

    response = client.post(
        f"/api/projects/ghost/publish/slug-proposals?project_path={workspace}",
        json={"scope": "project"},
    )

    assert response.status_code == 404


def test_service_slug_proposals_requires_project_snapshot(
    client: TestClient, workspace: Path
) -> None:
    plot_root = _make_project(workspace)
    services = read_canvas(plot_root, "alpha", "services")
    write_canvas(
        plot_root,
        "alpha",
        services.model_copy(update={"nodes": [ServiceNode(id="svc", label="결제")]}),
    )

    response = client.post(
        f"/api/projects/alpha/publish/slug-proposals?project_path={workspace}",
        json={"scope": "service", "service_id": "svc"},
    )

    assert response.status_code == 409


def test_project_publish_maps_slug_errors(client: TestClient, workspace: Path) -> None:
    plot_root = _make_project(workspace)
    init_workspace_repo(workspace)
    actors = read_canvas(plot_root, "alpha", "actors")
    write_canvas(
        plot_root,
        "alpha",
        actors.model_copy(update={"nodes": [ActorNode(id="operator", label="운영자")]}),
    )

    needed = client.post(
        f"/api/projects/alpha/publish?project_path={workspace}",
        json={"bump": "patch"},
    )
    invalid = client.post(
        f"/api/projects/alpha/publish?project_path={workspace}",
        json={"bump": "patch", "slugs": {"operator": "Operator"}},
    )

    assert needed.status_code == 409
    assert needed.json()["needs_slugs"][0]["node_id"] == "operator"
    assert invalid.status_code == 400
    assert invalid.json()["invalid_slugs"][0]["reason"] == "format"


def test_publish_rejects_non_string_slug_object(client: TestClient, workspace: Path) -> None:
    _make_project(workspace)

    response = client.post(
        f"/api/projects/alpha/publish?project_path={workspace}",
        json={"bump": "patch", "slugs": {"node": 3}},
    )

    assert response.status_code == 400
    assert response.json()["error"] == "'slugs' must be an object of node id to English id"


def test_service_publish_accepts_empty_body_and_slug_body(workspace: Path) -> None:
    from mashbill.format_f import publish_project_snapshot

    plot_root = _make_project(workspace)
    publish_project_snapshot(plot_root, "alpha", blueprint_version="v0.1.1")
    services = read_canvas(plot_root, "alpha", "services")
    write_canvas(
        plot_root,
        "alpha",
        services.model_copy(update={"nodes": [ServiceNode(id="svc", label="결제")]}),
    )
    client = TestClient(create_http_app(hub=BroadcastHub(enable_watchers=False)))

    needed = client.post(
        f"/api/projects/alpha/services/svc/publish?project_path={workspace}",
    )
    published = client.post(
        f"/api/projects/alpha/services/svc/publish?project_path={workspace}",
        json={"slugs": {"svc": "payments"}},
    )

    assert needed.status_code == 409
    assert needed.json()["needs_slugs"][0]["node_id"] == "svc"
    assert published.status_code == 201
    assert published.json()["service"] == "service/payments"
