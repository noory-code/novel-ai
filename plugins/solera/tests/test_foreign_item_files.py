"""A file in ``items/`` whose name is not a work-item id never stops the workspace.

A synced folder (iCloud, Dropbox) that sees two machines edit the same item
keeps both as ``STORY-001.md`` and ``STORY-001 2.md``. That second name is not a
valid item id, and reading it used to fail every call that loads the work tree.
Such files are now skipped, listed, reported by the audit, and returned by
``GET /api/work`` so the app can show them.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from solera.audit import audit_workspace
from solera.broadcast import BroadcastHub
from solera.formats import WorkItem
from solera.graph import load_items
from solera.http_app import create_http_app
from solera.workspace import Workspace


def _workspace_with_conflict_copy(root: Path) -> Workspace:
    ws = Workspace(root)
    ws.write_item(WorkItem(id="STORY-001", level="story", status="todo", goal="Write the story"))
    ws.write_item(WorkItem(id="STORY-002", level="story", status="todo", goal="Another"))
    original = ws.item_path("STORY-001").read_text()
    (ws.items_dir / "STORY-001 2.md").write_text(original)
    return ws


def test_loading_skips_a_conflict_copy_and_keeps_every_real_item(tmp_path: Path) -> None:
    ws = _workspace_with_conflict_copy(tmp_path)
    assert sorted(load_items(ws)) == ["STORY-001", "STORY-002"]
    assert ws.foreign_item_files() == ["STORY-001 2.md"]


def test_any_other_file_in_the_items_folder_is_listed_too(tmp_path: Path) -> None:
    ws = _workspace_with_conflict_copy(tmp_path)
    (ws.items_dir / "STORY-001 2.txt").write_text("stray")
    (ws.items_dir / "notes").write_text("stray")
    (ws.items_dir / ".STORY-002.md.ab12.tmp").write_text("a write in progress")
    assert sorted(load_items(ws)) == ["STORY-001", "STORY-002"]
    assert ws.foreign_item_files() == ["STORY-001 2.md", "STORY-001 2.txt", "notes"]


def test_the_audit_names_the_conflict_copy(tmp_path: Path) -> None:
    ws = _workspace_with_conflict_copy(tmp_path)
    problems = audit_workspace(ws)
    assert [(p.kind, p.detail.split(":")[0]) for p in problems] == [
        ("foreign-item-file", "STORY-001 2.md")
    ]


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(create_http_app(hub=BroadcastHub(enable_watchers=False))) as test_client:
        yield test_client


def test_the_work_view_still_loads_and_lists_the_skipped_file(
    tmp_path: Path, client: TestClient
) -> None:
    _workspace_with_conflict_copy(tmp_path / ".noory" / "solera")
    response = client.get("/api/work", params={"project_path": str(tmp_path)})
    assert response.status_code == 200
    body = response.json()
    assert sorted(item["id"] for item in body["items"]) == ["STORY-001", "STORY-002"]
    assert body["skipped_files"] == ["STORY-001 2.md"]


def test_a_clean_workspace_reports_no_skipped_files(tmp_path: Path, client: TestClient) -> None:
    Workspace(tmp_path / ".noory" / "solera").write_item(
        WorkItem(id="STORY-001", level="story", status="todo", goal="Only")
    )
    body = client.get("/api/work", params={"project_path": str(tmp_path)}).json()
    assert body["skipped_files"] == []
