"""Coach draft persistence, MCP resolution, and read-only HTTP listing."""

from __future__ import annotations

import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from mashbill import draft_store, mcp_tools
from mashbill.broadcast import BroadcastHub
from mashbill.draft_store import list_drafts, read_draft
from mashbill.folder_io import create_node as create_canvas_node
from mashbill.http_app import create_http_app
from mashbill.project_io import create_project
from mashbill.workspace import resolve_plot_root


def _project(tmp_path: Path) -> tuple[Path, str]:
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    return plot_root, "alpha"


def _record(
    project_path: str,
    *,
    canvas_kind: str = "foundation",
    proposed_text: str = "Make difficult planning feel clear.",
    chat_scope: str = "foundation",
    target_node_ids: list[str] | None = None,
    proposed_kind: str | None = "mission",
    service_id: str | None = None,
) -> dict[str, object]:
    return mcp_tools.record_draft(
        project_path,
        "alpha",
        canvas_kind,  # type: ignore[arg-type]
        proposed_text,
        "It matches the outcome described in the conversation.",
        chat_scope,
        target_node_ids,
        proposed_kind,
        service_id,
    )


def test_record_draft_writes_one_file_and_lists_it(tmp_path: Path) -> None:
    plot_root, _ = _project(tmp_path)

    out = _record(str(tmp_path), target_node_ids=["mission_1"])

    draft_id = out["draft_id"]
    assert isinstance(draft_id, str)
    path = plot_root / "drafts" / f"{draft_id}.json"
    assert path.is_file()
    drafts = list_drafts(plot_root, "alpha")
    assert [draft.id for draft in drafts] == [draft_id]
    assert drafts[0].target_node_ids == ["mission_1"]
    assert drafts[0].status == "proposed"
    assert drafts[0].origin == "recorded"


def test_concurrent_record_draft_calls_do_not_lose_records(tmp_path: Path) -> None:
    plot_root, _ = _project(tmp_path)

    with ThreadPoolExecutor(max_workers=8) as executor:
        outputs = list(
            executor.map(
                lambda number: _record(str(tmp_path), proposed_text=f"Draft {number}"),
                range(24),
            )
        )

    expected = {str(output["draft_id"]) for output in outputs}
    assert len(expected) == 24
    assert {draft.id for draft in list_drafts(plot_root, "alpha")} == expected


def test_resolve_draft_changes_status_without_deleting_rejected_draft(tmp_path: Path) -> None:
    plot_root, _ = _project(tmp_path)
    draft_id = str(_record(str(tmp_path))["draft_id"])

    resolved = mcp_tools.resolve_draft(str(tmp_path), "alpha", draft_id, "confirmed", ["mission_1"])
    assert resolved["status"] == "confirmed"
    assert resolved["resolved_node_ids"] == ["mission_1"]
    confirmed_updated = str(resolved["updated"])

    rejected = mcp_tools.resolve_draft(str(tmp_path), "alpha", draft_id, "rejected")
    assert rejected["status"] == "rejected"
    assert str(rejected["updated"]) >= confirmed_updated
    assert read_draft(plot_root, "alpha", draft_id).status == "rejected"
    assert (plot_root / "drafts" / f"{draft_id}.json").is_file()
    assert [draft.id for draft in list_drafts(plot_root, "alpha")] == [draft_id]


def test_resolve_missing_draft_is_an_error(tmp_path: Path) -> None:
    _project(tmp_path)
    with pytest.raises(FileNotFoundError, match="draft"):
        mcp_tools.resolve_draft(str(tmp_path), "alpha", "draft_missing", "rejected")


def test_update_node_with_draft_id_confirms_and_links_node(tmp_path: Path) -> None:
    plot_root, _ = _project(tmp_path)
    created = create_canvas_node(plot_root, "alpha", "foundation", "mission", {"label": "Mission"})
    node_id = str(created["node"]["id"])
    draft_id = str(_record(str(tmp_path), target_node_ids=[node_id])["draft_id"])

    mcp_tools.update_node(
        str(tmp_path),
        "alpha",
        "foundation",
        node_id,
        {"statement": "Help people shape products together."},
        draft_id=draft_id,
    )

    draft = read_draft(plot_root, "alpha", draft_id)
    assert draft.status == "confirmed"
    assert draft.resolved_node_ids == [node_id]
    assert [item.id for item in list_drafts(plot_root, "alpha")] == [draft_id]


def test_create_node_with_draft_id_confirms_and_links_minted_node(tmp_path: Path) -> None:
    plot_root, _ = _project(tmp_path)
    draft_id = str(
        _record(
            str(tmp_path),
            proposed_text="Clarity",
            target_node_ids=[],
            proposed_kind="core_value",
        )["draft_id"]
    )

    created = mcp_tools.create_node(
        str(tmp_path),
        "alpha",
        "foundation",
        "core_value",
        {"label": "Clarity"},
        draft_id=draft_id,
    )

    node_id = str(created["node"]["id"])
    draft = read_draft(plot_root, "alpha", draft_id)
    assert draft.status == "confirmed"
    assert draft.resolved_node_ids == [node_id]
    assert [item.id for item in list_drafts(plot_root, "alpha")] == [draft_id]


def test_update_node_without_draft_id_records_confirmed_auto_draft(tmp_path: Path) -> None:
    plot_root, _ = _project(tmp_path)
    created = create_canvas_node(plot_root, "alpha", "actors", "actor", {"label": "Old label"})
    mcp_tools.update_node(
        str(tmp_path),
        "alpha",
        "actors",
        str(created["node"]["id"]),
        {"label": "Reader", "body": "Needs a clear next step."},
    )

    drafts = list_drafts(plot_root, "alpha")
    assert len(drafts) == 1
    draft = drafts[0]
    node_id = str(created["node"]["id"])
    assert draft.status == "confirmed"
    assert draft.origin == "auto"
    assert draft.target_node_ids == [node_id]
    assert draft.resolved_node_ids == [node_id]
    assert draft.proposed_kind == "actor"
    assert draft.proposed_text == "label: Reader\nbody: Needs a clear next step."
    assert draft.rationale
    assert draft.chat_scope == ""


def test_create_node_without_draft_id_records_confirmed_auto_draft(tmp_path: Path) -> None:
    plot_root, _ = _project(tmp_path)

    created = mcp_tools.create_node(
        str(tmp_path),
        "alpha",
        "foundation",
        "core_value",
        {"label": "Clarity", "body": "Make the next step visible."},
    )

    drafts = list_drafts(plot_root, "alpha")
    assert len(drafts) == 1
    draft = drafts[0]
    node_id = str(created["node"]["id"])
    assert draft.status == "confirmed"
    assert draft.origin == "auto"
    assert draft.target_node_ids == [node_id]
    assert draft.resolved_node_ids == [node_id]
    assert draft.proposed_kind == "core_value"
    assert draft.proposed_text == "label: Clarity\nbody: Make the next step visible."
    assert draft.rationale
    assert draft.chat_scope == ""


def test_auto_draft_keeps_supplied_chat_scope(tmp_path: Path) -> None:
    plot_root, _ = _project(tmp_path)

    mcp_tools.create_node(
        str(tmp_path),
        "alpha",
        "entities",
        "entity",
        {"label": "Order"},
        chat_scope="entities",
    )

    assert list_drafts(plot_root, "alpha")[0].chat_scope == "entities"


def test_legacy_draft_without_origin_reads_as_recorded(tmp_path: Path) -> None:
    plot_root, _ = _project(tmp_path)
    draft_id = str(_record(str(tmp_path))["draft_id"])
    path = plot_root / "drafts" / f"{draft_id}.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw.pop("origin", None)
    path.write_text(json.dumps(raw), encoding="utf-8")

    assert read_draft(plot_root, "alpha", draft_id).origin == "recorded"


def test_viewer_canvas_put_does_not_create_draft(tmp_path: Path) -> None:
    plot_root, _ = _project(tmp_path)
    client = TestClient(create_http_app(hub=BroadcastHub(enable_watchers=False)))
    url = "/api/projects/alpha/canvases/actors"
    canvas = client.get(url, params={"project_path": str(tmp_path)}).json()
    canvas["nodes"].append({"id": "reader", "kind": "actor", "label": "Reader"})

    response = client.put(url, params={"project_path": str(tmp_path)}, json=canvas)

    assert response.status_code == 200
    assert list_drafts(plot_root, "alpha") == []
    assert not (plot_root / "drafts").exists()


def test_drafts_http_list_sorts_and_filters(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plot_root, _ = _project(tmp_path)
    timestamps = iter(
        [
            "2026-09-29T00:00:01+00:00",
            "2026-09-29T00:00:02+00:00",
            "2026-09-29T00:00:03+00:00",
            "2026-09-29T00:00:04+00:00",
        ]
    )
    monkeypatch.setattr(draft_store, "_now", lambda: next(timestamps))
    first = _record(str(tmp_path), target_node_ids=["mission_1"])
    second = _record(
        str(tmp_path),
        canvas_kind="entities",
        proposed_text="Order",
        chat_scope="entities",
        target_node_ids=[],
        proposed_kind="entity",
    )
    third = _record(
        str(tmp_path),
        canvas_kind="feature",
        proposed_text="Confirm order",
        chat_scope="feature:feature_1",
        target_node_ids=["step_1"],
        proposed_kind="step",
        service_id="feature_1",
    )
    mcp_tools.resolve_draft(
        str(tmp_path), "alpha", str(first["draft_id"]), "confirmed", ["mission_1"]
    )

    client = TestClient(create_http_app(hub=BroadcastHub(enable_watchers=False)))
    url = "/api/projects/alpha/drafts"
    all_rows = client.get(url, params={"project_path": str(tmp_path)})
    assert all_rows.status_code == 200
    assert [row["id"] for row in all_rows.json()["drafts"]] == [
        first["draft_id"],
        third["draft_id"],
        second["draft_id"],
    ]

    confirmed = client.get(
        url, params={"project_path": str(tmp_path), "status": "confirmed"}
    ).json()["drafts"]
    assert [row["id"] for row in confirmed] == [first["draft_id"]]

    entities = client.get(
        url, params={"project_path": str(tmp_path), "canvas_kind": "entities"}
    ).json()["drafts"]
    assert [row["id"] for row in entities] == [second["draft_id"]]

    by_target = client.get(url, params={"project_path": str(tmp_path), "node_id": "step_1"}).json()[
        "drafts"
    ]
    assert [row["id"] for row in by_target] == [third["draft_id"]]

    by_resolved = client.get(
        url, params={"project_path": str(tmp_path), "node_id": "mission_1"}
    ).json()["drafts"]
    assert [row["id"] for row in by_resolved] == [first["draft_id"]]


def test_draft_tools_have_pinned_mcp_schemas() -> None:
    record = asyncio.run(mcp_tools.mcp.get_tool("record_draft"))
    assert record is not None
    assert set(record.parameters["properties"]) == {
        "project_path",
        "project_id",
        "canvas_kind",
        "proposed_text",
        "rationale",
        "chat_scope",
        "target_node_ids",
        "proposed_kind",
        "service_id",
    }
    assert set(record.parameters["required"]) == {
        "project_path",
        "project_id",
        "canvas_kind",
        "proposed_text",
        "rationale",
        "chat_scope",
    }

    resolve = asyncio.run(mcp_tools.mcp.get_tool("resolve_draft"))
    assert resolve is not None
    assert set(resolve.parameters["properties"]) == {
        "project_path",
        "project_id",
        "draft_id",
        "status",
        "node_ids",
    }
    assert set(resolve.parameters["required"]) == {
        "project_path",
        "project_id",
        "draft_id",
        "status",
    }
