"""Published release imports through Solera's HTTP contract."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import cast
from unittest.mock import AsyncMock

import pytest
from httpx import Response
from starlette.testclient import TestClient

from solera.broadcast import BroadcastHub
from solera.http_app import create_http_app
from solera.intake import import_release
from solera.workspace import Workspace


def _published(project: Path) -> tuple[Path, Path]:
    published = project / "published"
    project_dir = published / "_project" / "vP1"
    service_dir = published / "svc" / "vS1"
    project_dir.mkdir(parents=True)
    service_dir.mkdir(parents=True)
    (project_dir / "manifest.json").write_text(
        json.dumps(
            {
                "format_f_version": 1,
                "scope": "project",
                "release": "vP1",
                "git_sha": "",
                "elements": [{"id": "actor/user", "kind": "actor", "hash": "aaaa"}],
            }
        ),
        encoding="utf-8",
    )
    (service_dir / "manifest.json").write_text(
        json.dumps(
            {
                "format_f_version": 1,
                "scope": "service",
                "service": "service/svc",
                "release": "vS1",
                "based_on": "vP1",
                "git_sha": "",
                "elements": [{"id": "service/svc", "kind": "service", "hash": "bbbb"}],
                "refs": {
                    "anchors": {"core_values": [], "identity": []},
                    "actors": ["actor/user"],
                    "entities": [],
                },
            }
        ),
        encoding="utf-8",
    )
    return service_dir, project_dir


def _post(client: TestClient, project: Path, source: Path) -> Response:
    return cast(
        Response,
        client.post(
            "/api/work/imports",
            params={"project_path": str(project)},
            json={"source": str(source)},
        ),
    )


def _snapshot(root: Path) -> dict[str, tuple[bytes, int]]:
    return {
        str(path.relative_to(root)): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in root.rglob("*")
        if path.is_file()
    }


def test_import_and_repeat_write_nothing_and_notify_once(tmp_path: Path) -> None:
    source, _ = _published(tmp_path)
    hub = BroadcastHub(enable_watchers=False)
    hub.notify_write = AsyncMock()  # type: ignore[method-assign]
    with TestClient(create_http_app(hub=hub)) as client:
        first = _post(client, tmp_path, source)
        assert first.status_code == 201, first.text
        assert first.json() == {"label": "svc-vS1", "release": "vS1", "imported": True}
        ws = Workspace(tmp_path / ".noory" / "solera")
        assert (ws.spec_dir("svc-vS1") / "service" / "manifest.json").is_file()
        assert (ws.spec_dir("svc-vS1") / "project" / "manifest.json").is_file()
        before = _snapshot(ws.root)

        second = _post(client, tmp_path, source)
        assert second.status_code == 200, second.text
        assert second.json() == {"label": "svc-vS1", "release": "vS1", "imported": False}
        assert _snapshot(ws.root) == before
        hub.notify_write.assert_awaited_once_with(ws.root)


@pytest.mark.parametrize("side", ["service", "project"])
def test_same_label_with_different_manifest_conflicts(tmp_path: Path, side: str) -> None:
    source, project_source = _published(tmp_path)
    with TestClient(create_http_app()) as client:
        assert _post(client, tmp_path, source).status_code == 201
        manifest_path = (source if side == "service" else project_source) / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["git_sha"] = "changed"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        ws = Workspace(tmp_path / ".noory" / "solera")
        before = _snapshot(ws.root)

        response = _post(client, tmp_path, source)
        assert response.status_code == 409, response.text
        assert response.json()["code"] == "import_conflict"
        assert _snapshot(ws.root) == before


def test_same_release_identity_elsewhere_with_different_content_conflicts(tmp_path: Path) -> None:
    source, _ = _published(tmp_path)
    ws = Workspace(tmp_path / ".noory" / "solera")
    import_release(ws, source, label="legacy")
    second = tmp_path / "other" / "svc" / "vS1"
    second.mkdir(parents=True)
    (second / "manifest.json").write_text(
        (source / "manifest.json").read_text(encoding="utf-8").replace('"bbbb"', '"cccc"'),
        encoding="utf-8",
    )
    second_project = tmp_path / "other" / "_project" / "vP1"
    second_project.mkdir(parents=True)
    first_project = tmp_path / "published" / "_project" / "vP1" / "manifest.json"
    (second_project / "manifest.json").write_bytes(first_project.read_bytes())
    stale = ws.specs_dir / ".svc-vS1.stale"
    stale.mkdir()
    (stale / "partial").write_text("keep on conflict", encoding="utf-8")
    before = _snapshot(ws.root)
    with TestClient(create_http_app()) as client:
        response = _post(client, tmp_path, second)
        assert response.status_code == 409, response.text
        assert response.json()["code"] == "import_conflict"
        assert _snapshot(ws.root) == before


@pytest.mark.parametrize("outside", ["outside", "missing", "file", "symlink_escape"])
def test_source_must_resolve_to_project_directory(tmp_path: Path, outside: str) -> None:
    project = tmp_path / "project"
    project.mkdir()
    if outside == "outside":
        source = tmp_path / "elsewhere"
        source.mkdir()
    elif outside == "missing":
        source = project / "missing"
    elif outside == "file":
        source = project / "file"
        source.write_text("x", encoding="utf-8")
    else:
        target = tmp_path / "elsewhere"
        target.mkdir()
        source = project / "linked"
        source.symlink_to(target, target_is_directory=True)
    with TestClient(create_http_app()) as client:
        response = _post(client, project, source)
        assert response.status_code == 400, response.text
        assert response.json()["code"] == "import_source_outside"


def test_non_release_folder_is_invalid(tmp_path: Path) -> None:
    source, _ = _published(tmp_path)
    renamed = source.with_name("latest")
    source.rename(renamed)
    with TestClient(create_http_app()) as client:
        response = _post(client, tmp_path, renamed)
        assert response.status_code == 400, response.text
        assert response.json()["code"] == "invalid_release"


def test_missing_based_on_snapshot_is_invalid(tmp_path: Path) -> None:
    source, project_source = _published(tmp_path)
    project_source.rename(project_source.with_name("gone"))
    with TestClient(create_http_app()) as client:
        response = _post(client, tmp_path, source)
        assert response.status_code == 400, response.text
        assert response.json()["code"] == "invalid_release"


@pytest.mark.parametrize(
    "broken",
    [
        "manifest",
        "missing_service_manifest",
        "missing_project_manifest",
        "bundle_symlink",
        "source_symlink",
        "parent_symlink",
    ],
)
def test_malformed_release_or_symlink_is_invalid(tmp_path: Path, broken: str) -> None:
    source, project_snapshot = _published(tmp_path)
    if broken == "manifest":
        (source / "manifest.json").write_text("{}", encoding="utf-8")
    elif broken == "missing_service_manifest":
        (source / "manifest.json").unlink()
    elif broken == "missing_project_manifest":
        (project_snapshot / "manifest.json").unlink()
    elif broken == "bundle_symlink":
        (source / "linked").symlink_to(source / "manifest.json")
    elif broken == "source_symlink":
        link = tmp_path / "published" / "alias" / "vS1"
        link.parent.mkdir()
        link.symlink_to(source, target_is_directory=True)
        source = link
    else:
        link = tmp_path / "other" / "svc"
        link.parent.mkdir()
        link.symlink_to(source.parent, target_is_directory=True)
        shutil.copytree(tmp_path / "published" / "_project", link.parent / "_project")
        source = link / "vS1"
    with TestClient(create_http_app()) as client:
        response = _post(client, tmp_path, source)
        assert response.status_code == 400, response.text
        assert response.json()["code"] == "invalid_release"


@pytest.mark.parametrize("field", ["release", "service"])
def test_manifest_identity_must_match_source_folders(tmp_path: Path, field: str) -> None:
    source, _ = _published(tmp_path)
    path = source / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest[field] = "vS2" if field == "release" else "service/other"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with TestClient(create_http_app()) as client:
        response = _post(client, tmp_path, source)
        assert response.status_code == 400, response.text
        assert response.json()["code"] == "invalid_release"


def test_extra_body_fields_are_invalid_request(tmp_path: Path) -> None:
    source, _ = _published(tmp_path)
    with TestClient(create_http_app()) as client:
        response = client.post(
            "/api/work/imports",
            params={"project_path": str(tmp_path)},
            json={"source": str(source), "label": "different"},
        )
        assert response.status_code == 400, response.text
        assert response.json()["code"] == "invalid_request"


def test_import_enables_connectedness_for_http_check(tmp_path: Path) -> None:
    source, _ = _published(tmp_path)
    query = {"project_path": str(tmp_path)}
    with TestClient(create_http_app()) as client:
        disconnected_parent = client.post(
            "/api/work/items",
            params=query,
            json={"parent": None, "goal": "Disconnected", "accept": "children"},
        ).json()["id"]
        disconnected = client.post(
            "/api/work/items",
            params=query,
            json={"parent": disconnected_parent, "goal": "No design", "accept": "person"},
        ).json()["id"]
        connected_parent = client.post(
            "/api/work/items",
            params=query,
            json={
                "parent": None,
                "goal": "Connected",
                "accept": "children",
                "realizes": ["service/svc"],
            },
        ).json()["id"]
        connected = client.post(
            "/api/work/items",
            params=query,
            json={"parent": connected_parent, "goal": "Inherits design", "accept": "person"},
        ).json()["id"]

        assert _post(client, tmp_path, source).status_code == 201
        blocked = client.post(f"/api/work/items/{disconnected}/check", params=query)
        assert blocked.status_code == 400, blocked.text
        assert blocked.json()["code"] == "check_blocked"
        allowed = client.post(f"/api/work/items/{connected}/check", params=query)
        assert allowed.status_code == 200, allowed.text
        assert allowed.json()["item"]["status"] == "done"
