"""v0.24.0 (D-2026-05-17-L) — /api/files/raw endpoint tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from starlette.testclient import TestClient

from mashbill.folder_io import create_project
from mashbill.http_app import create_http_app


@pytest.fixture()
def plot_root(tmp_path: Path) -> Path:
    # D-2026-06-11-C/D: workspace is the user's opened folder and IS the
    # git repo; .noory/plot/ lives inside it. Novel never auto-inits — but
    # tests that exercise publish/tag need a real repo, so we init here.
    from mashbill.git_store import init_workspace_repo
    from mashbill.workspace import resolve_plot_root

    init_workspace_repo(tmp_path)
    return resolve_plot_root(str(tmp_path))


@pytest.fixture()
def client(plot_root: Path) -> TestClient:
    app = create_http_app()
    return TestClient(app)


# 1x1 transparent PNG.
_TINY_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d49444154789c6300010000000500010d0a2db40000000049454e44ae426082"
)


def _seed_image(plot_root: Path, project_id: str, rel_path: str) -> Path:
    create_project(plot_root, project_id, project_id)
    target = plot_root / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(_TINY_PNG)
    return target


def test_raw_endpoint_serves_png_bytes(plot_root: Path, client: TestClient) -> None:
    _seed_image(plot_root, "alpha", "img/test.png")
    resp = client.get(
        "/api/files/raw",
        params={
            "project_path": str(plot_root.parent.parent),
            "project_id": "alpha",
            "path": "img/test.png",
        },
    )
    assert resp.status_code == 200
    assert resp.content == _TINY_PNG
    assert resp.headers["content-type"].startswith("image/")


def test_raw_endpoint_404_for_missing_file(plot_root: Path, client: TestClient) -> None:
    create_project(plot_root, "alpha", "alpha")
    resp = client.get(
        "/api/files/raw",
        params={
            "project_path": str(plot_root.parent.parent),
            "project_id": "alpha",
            "path": "img/ghost.png",
        },
    )
    assert resp.status_code == 404


def test_raw_endpoint_400_for_disallowed_extension(plot_root: Path, client: TestClient) -> None:
    """Only image extensions are served by /api/files/raw."""
    create_project(plot_root, "alpha", "alpha")
    (plot_root / "notes.md").write_text("# md", encoding="utf-8")
    resp = client.get(
        "/api/files/raw",
        params={
            "project_path": str(plot_root.parent.parent),
            "project_id": "alpha",
            "path": "notes.md",
        },
    )
    assert resp.status_code == 400


def test_raw_endpoint_400_for_path_traversal(plot_root: Path, client: TestClient) -> None:
    create_project(plot_root, "alpha", "alpha")
    resp = client.get(
        "/api/files/raw",
        params={
            "project_path": str(plot_root.parent.parent),
            "project_id": "alpha",
            "path": "../../../etc/passwd",
        },
    )
    assert resp.status_code == 400
