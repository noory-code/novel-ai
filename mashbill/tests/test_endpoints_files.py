"""HTTP tests for the text-file + folder endpoints (``endpoints_files.py``).

These Starlette handlers power the Inspector MD editor (read/write of
project-relative ``.md``/``.txt`` files), the raw image serving for Live
Preview ``<img>`` embeds, and folder creation. Each handler scopes every
request to ``.noory/plot/{project}`` and short-circuits on missing params,
a missing project, path-traversal, disallowed extensions, and oversized
payloads.

Every test asserts a specific status code + error/served body so it fails
if a guard branch is dropped or weakened.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from starlette.testclient import TestClient

from mashbill.broadcast import BroadcastHub
from mashbill.file_io import MAX_FILE_BYTES
from mashbill.http_app import create_http_app
from mashbill.project_io import create_project
from mashbill.workspace import resolve_plot_root

PROJECT_ID = "alpha"


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    """A bare workspace directory the endpoints will resolve ``.noory/plot``
    under. The project is created on demand via :func:`make_project`."""
    ws = tmp_path / "ws"
    ws.mkdir()
    return ws


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_http_app(hub=BroadcastHub(enable_watchers=False)))


def make_project(workspace: Path) -> Path:
    """Seed ``project.json`` (flat layout) and return the resolved plot_root."""
    plot_root = resolve_plot_root(str(workspace))
    create_project(plot_root, PROJECT_ID, "Alpha")
    return plot_root


# ---------------------------------------------------------------------------
# GET /api/files — read text file
# ---------------------------------------------------------------------------


def test_file_get_missing_project_path_400(client: TestClient) -> None:
    resp = client.get(f"/api/files?project_id={PROJECT_ID}&path=details.md")
    assert resp.status_code == 400
    assert "project_path" in resp.json()["error"]


def test_file_get_nonexistent_project_path_404(client: TestClient, tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist"
    resp = client.get(
        f"/api/files?project_path={missing}&project_id={PROJECT_ID}&path=details.md"
    )
    assert resp.status_code == 404


def test_file_get_missing_project_id_400(client: TestClient, workspace: Path) -> None:
    resp = client.get(f"/api/files?project_path={workspace}&path=details.md")
    assert resp.status_code == 400
    assert "project_id" in resp.json()["error"]


def test_file_get_missing_path_400(client: TestClient, workspace: Path) -> None:
    resp = client.get(f"/api/files?project_path={workspace}&project_id={PROJECT_ID}")
    assert resp.status_code == 400
    assert "path" in resp.json()["error"]


def test_file_get_unknown_project_404(client: TestClient, workspace: Path) -> None:
    # Workspace resolves (so plot_root exists) but no project.json was written.
    resolve_plot_root(str(workspace))
    resp = client.get(
        f"/api/files?project_path={workspace}&project_id={PROJECT_ID}&path=details.md"
    )
    assert resp.status_code == 404
    assert PROJECT_ID in resp.json()["error"]


def test_file_get_returns_written_content(client: TestClient, workspace: Path) -> None:
    plot_root = make_project(workspace)
    (plot_root / "details.md").write_text("# Hello\nbody", encoding="utf-8")
    resp = client.get(
        f"/api/files?project_path={workspace}&project_id={PROJECT_ID}&path=details.md"
    )
    assert resp.status_code == 200
    assert resp.json() == {"path": "details.md", "content": "# Hello\nbody"}


def test_file_get_missing_file_returns_empty_string(
    client: TestClient, workspace: Path
) -> None:
    # read_text_file returns "" for a not-yet-created file (open-node flow).
    make_project(workspace)
    resp = client.get(
        f"/api/files?project_path={workspace}&project_id={PROJECT_ID}&path=notes.md"
    )
    assert resp.status_code == 200
    assert resp.json() == {"path": "notes.md", "content": ""}


def test_file_get_path_traversal_400(client: TestClient, workspace: Path) -> None:
    make_project(workspace)
    resp = client.get(
        f"/api/files?project_path={workspace}&project_id={PROJECT_ID}&path=../escape.md"
    )
    assert resp.status_code == 400
    assert "rel_path" in resp.json()["error"]


def test_file_get_disallowed_extension_400(client: TestClient, workspace: Path) -> None:
    make_project(workspace)
    resp = client.get(
        f"/api/files?project_path={workspace}&project_id={PROJECT_ID}&path=secret.py"
    )
    assert resp.status_code == 400
    assert "not allowed" in resp.json()["error"]


def test_file_get_oversize_413(client: TestClient, workspace: Path) -> None:
    plot_root = make_project(workspace)
    big = plot_root / "big.md"
    big.write_text("x" * (MAX_FILE_BYTES + 1), encoding="utf-8")
    resp = client.get(
        f"/api/files?project_path={workspace}&project_id={PROJECT_ID}&path=big.md"
    )
    assert resp.status_code == 413
    assert "exceeds" in resp.json()["error"]


# ---------------------------------------------------------------------------
# GET /api/files/raw — serve raw image bytes
# ---------------------------------------------------------------------------


def test_file_raw_missing_project_path_400(client: TestClient) -> None:
    resp = client.get(f"/api/files/raw?project_id={PROJECT_ID}&path=logo.png")
    assert resp.status_code == 400
    assert "project_path" in resp.json()["error"]


def test_file_raw_nonexistent_project_path_404(client: TestClient, tmp_path: Path) -> None:
    missing = tmp_path / "nope"
    resp = client.get(
        f"/api/files/raw?project_path={missing}&project_id={PROJECT_ID}&path=logo.png"
    )
    assert resp.status_code == 404


def test_file_raw_missing_project_id_400(client: TestClient, workspace: Path) -> None:
    resp = client.get(f"/api/files/raw?project_path={workspace}&path=logo.png")
    assert resp.status_code == 400
    assert "project_id" in resp.json()["error"]


def test_file_raw_missing_path_400(client: TestClient, workspace: Path) -> None:
    resp = client.get(f"/api/files/raw?project_path={workspace}&project_id={PROJECT_ID}")
    assert resp.status_code == 400
    assert "path" in resp.json()["error"]


def test_file_raw_unknown_project_404(client: TestClient, workspace: Path) -> None:
    resolve_plot_root(str(workspace))
    resp = client.get(
        f"/api/files/raw?project_path={workspace}&project_id={PROJECT_ID}&path=logo.png"
    )
    assert resp.status_code == 404
    assert PROJECT_ID in resp.json()["error"]


def test_file_raw_path_traversal_400(client: TestClient, workspace: Path) -> None:
    make_project(workspace)
    resp = client.get(
        f"/api/files/raw?project_path={workspace}&project_id={PROJECT_ID}&path=../x.png"
    )
    assert resp.status_code == 400
    assert "rel_path" in resp.json()["error"]


def test_file_raw_non_image_extension_400(client: TestClient, workspace: Path) -> None:
    # A .md path is safe but not an allowed image extension for raw serving.
    make_project(workspace)
    resp = client.get(
        f"/api/files/raw?project_path={workspace}&project_id={PROJECT_ID}&path=details.md"
    )
    assert resp.status_code == 400
    assert "not allowed for raw image read" in resp.json()["error"]


def test_file_raw_missing_image_404(client: TestClient, workspace: Path) -> None:
    # Allowed extension + safe path, but the file does not exist on disk.
    make_project(workspace)
    resp = client.get(
        f"/api/files/raw?project_path={workspace}&project_id={PROJECT_ID}&path=logo.png"
    )
    assert resp.status_code == 404
    assert "file not found" in resp.json()["error"]


def test_file_raw_serves_existing_image_bytes(client: TestClient, workspace: Path) -> None:
    plot_root = make_project(workspace)
    payload = b"\x89PNG\r\n\x1a\nFAKE-IMAGE-BYTES"
    (plot_root / "logo.png").write_bytes(payload)
    resp = client.get(
        f"/api/files/raw?project_path={workspace}&project_id={PROJECT_ID}&path=logo.png"
    )
    assert resp.status_code == 200
    assert resp.content == payload


# ---------------------------------------------------------------------------
# PUT /api/files — write text file
# ---------------------------------------------------------------------------


def test_file_put_missing_project_path_400(client: TestClient) -> None:
    resp = client.put(
        f"/api/files?project_id={PROJECT_ID}&path=details.md",
        json={"content": "x"},
    )
    assert resp.status_code == 400
    assert "project_path" in resp.json()["error"]


def test_file_put_nonexistent_project_path_404(client: TestClient, tmp_path: Path) -> None:
    missing = tmp_path / "nope"
    resp = client.put(
        f"/api/files?project_path={missing}&project_id={PROJECT_ID}&path=details.md",
        json={"content": "x"},
    )
    assert resp.status_code == 404


def test_file_put_missing_project_id_400(client: TestClient, workspace: Path) -> None:
    resp = client.put(
        f"/api/files?project_path={workspace}&path=details.md",
        json={"content": "x"},
    )
    assert resp.status_code == 400
    assert "project_id" in resp.json()["error"]


def test_file_put_missing_path_400(client: TestClient, workspace: Path) -> None:
    resp = client.put(
        f"/api/files?project_path={workspace}&project_id={PROJECT_ID}",
        json={"content": "x"},
    )
    assert resp.status_code == 400
    assert "path" in resp.json()["error"]


def test_file_put_invalid_json_400(client: TestClient, workspace: Path) -> None:
    resp = client.put(
        f"/api/files?project_path={workspace}&project_id={PROJECT_ID}&path=details.md",
        content=b"{not json",
        headers={"content-type": "application/json"},
    )
    assert resp.status_code == 400
    assert "invalid JSON body" in resp.json()["error"]


def test_file_put_non_string_content_400(client: TestClient, workspace: Path) -> None:
    resp = client.put(
        f"/api/files?project_path={workspace}&project_id={PROJECT_ID}&path=details.md",
        json={"content": 123},
    )
    assert resp.status_code == 400
    assert "'content' must be a string" in resp.json()["error"]


def test_file_put_unknown_project_404(client: TestClient, workspace: Path) -> None:
    resolve_plot_root(str(workspace))
    resp = client.put(
        f"/api/files?project_path={workspace}&project_id={PROJECT_ID}&path=details.md",
        json={"content": "x"},
    )
    assert resp.status_code == 404
    assert PROJECT_ID in resp.json()["error"]


def test_file_put_path_traversal_400(client: TestClient, workspace: Path) -> None:
    make_project(workspace)
    resp = client.put(
        f"/api/files?project_path={workspace}&project_id={PROJECT_ID}&path=../escape.md",
        json={"content": "x"},
    )
    assert resp.status_code == 400
    assert "rel_path" in resp.json()["error"]


def test_file_put_disallowed_extension_400(client: TestClient, workspace: Path) -> None:
    make_project(workspace)
    resp = client.put(
        f"/api/files?project_path={workspace}&project_id={PROJECT_ID}&path=evil.py",
        json={"content": "import os"},
    )
    assert resp.status_code == 400
    assert "not allowed" in resp.json()["error"]


def test_file_put_oversize_413(client: TestClient, workspace: Path) -> None:
    make_project(workspace)
    resp = client.put(
        f"/api/files?project_path={workspace}&project_id={PROJECT_ID}&path=big.md",
        json={"content": "x" * (MAX_FILE_BYTES + 1)},
    )
    assert resp.status_code == 413
    assert "exceeds" in resp.json()["error"]


def test_file_put_writes_to_disk_and_roundtrips(client: TestClient, workspace: Path) -> None:
    plot_root = make_project(workspace)
    resp = client.put(
        f"/api/files?project_path={workspace}&project_id={PROJECT_ID}&path=sub/details.md",
        json={"content": "saved body"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"path": "sub/details.md", "ok": True}
    # The write actually landed under the project root, nested dir auto-created.
    assert (plot_root / "sub" / "details.md").read_text(encoding="utf-8") == "saved body"
    # And a subsequent GET returns the same content.
    got = client.get(
        f"/api/files?project_path={workspace}&project_id={PROJECT_ID}&path=sub/details.md"
    )
    assert got.json()["content"] == "saved body"


# ---------------------------------------------------------------------------
# POST /api/folders — create folder (with uniquify suffix)
# ---------------------------------------------------------------------------


def test_folder_post_missing_project_path_404_or_400(client: TestClient) -> None:
    resp = client.post("/api/folders", json={"project_id": PROJECT_ID, "path": "ideas"})
    assert resp.status_code == 400
    assert "project_path" in resp.json()["error"]


def test_folder_post_invalid_json_400(client: TestClient, workspace: Path) -> None:
    resp = client.post(
        f"/api/folders?project_path={workspace}",
        content=b"{nope",
        headers={"content-type": "application/json"},
    )
    assert resp.status_code == 400
    assert "invalid JSON body" in resp.json()["error"]


def test_folder_post_missing_project_id_400(client: TestClient, workspace: Path) -> None:
    resp = client.post(f"/api/folders?project_path={workspace}", json={"path": "ideas"})
    assert resp.status_code == 400
    assert "project_id" in resp.json()["error"]


def test_folder_post_blank_project_id_400(client: TestClient, workspace: Path) -> None:
    resp = client.post(
        f"/api/folders?project_path={workspace}",
        json={"project_id": "   ", "path": "ideas"},
    )
    # whitespace is a non-empty string so it passes the project_id guard, but
    # the project does not exist → 404. Either way it must not 2xx.
    assert resp.status_code in (400, 404)


def test_folder_post_missing_path_400(client: TestClient, workspace: Path) -> None:
    resp = client.post(
        f"/api/folders?project_path={workspace}",
        json={"project_id": PROJECT_ID},
    )
    assert resp.status_code == 400
    assert "path" in resp.json()["error"]


def test_folder_post_blank_path_400(client: TestClient, workspace: Path) -> None:
    resp = client.post(
        f"/api/folders?project_path={workspace}",
        json={"project_id": PROJECT_ID, "path": "   "},
    )
    assert resp.status_code == 400
    assert "path" in resp.json()["error"]


def test_folder_post_unknown_project_404(client: TestClient, workspace: Path) -> None:
    resolve_plot_root(str(workspace))
    resp = client.post(
        f"/api/folders?project_path={workspace}",
        json={"project_id": PROJECT_ID, "path": "ideas"},
    )
    assert resp.status_code == 404
    assert PROJECT_ID in resp.json()["error"]


def test_folder_post_path_traversal_400(client: TestClient, workspace: Path) -> None:
    make_project(workspace)
    resp = client.post(
        f"/api/folders?project_path={workspace}",
        json={"project_id": PROJECT_ID, "path": "../escape"},
    )
    assert resp.status_code == 400
    assert "rel_folder" in resp.json()["error"]


def test_folder_post_creates_folder_with_index_md(client: TestClient, workspace: Path) -> None:
    plot_root = make_project(workspace)
    resp = client.post(
        f"/api/folders?project_path={workspace}",
        json={"project_id": PROJECT_ID, "path": "ideas"},
    )
    assert resp.status_code == 201
    assert resp.json() == {"path": "ideas"}
    created = plot_root / "ideas"
    assert created.is_dir()
    assert (created / "index.md").is_file()


def test_folder_post_uniquifies_when_name_taken(client: TestClient, workspace: Path) -> None:
    plot_root = make_project(workspace)
    (plot_root / "ideas").mkdir()
    resp = client.post(
        f"/api/folders?project_path={workspace}",
        json={"project_id": PROJECT_ID, "path": "ideas"},
    )
    assert resp.status_code == 201
    assert resp.json() == {"path": "ideas-2"}
    assert (plot_root / "ideas-2").is_dir()
