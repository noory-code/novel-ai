"""Coach draft persistence, MCP resolution, and read-only HTTP listing."""

from __future__ import annotations

import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from mashbill import draft_store, mcp_canvas_write_tools, mcp_project_tools, mcp_tools
from mashbill.broadcast import BroadcastHub
from mashbill.chat_store import append_user, archive_current_conversation, read_conversation
from mashbill.draft_store import list_drafts, read_draft
from mashbill.folder_io import create_node as create_canvas_node
from mashbill.folder_io import read_canvas, sync_details_with_overview, write_canvas
from mashbill.http_app import create_http_app
from mashbill.mcp_draft_tools import AUTO_DRAFT_RATIONALE
from mashbill.mcp_write_rollback import with_draft_or_rollback
from mashbill.models_draft import DraftDoc
from mashbill.project_io import create_project
from mashbill.references import set_node_references as set_canvas_node_references
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


def test_record_draft_accepts_project_proposal(tmp_path: Path) -> None:
    plot_root, _ = _project(tmp_path)

    out = _record(
        str(tmp_path),
        canvas_kind="project",
        proposed_text="프로젝트 이름: 새이름",
        chat_scope="foundation",
        proposed_kind=None,
    )

    draft = read_draft(plot_root, "alpha", str(out["draft_id"]))
    assert draft.canvas_kind == "project"
    assert draft.target_node_ids == []
    assert draft.proposed_kind is None
    assert draft.service_id is None


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"target_node_ids": ["mission_1"]}, "target_node_ids"),
        ({"proposed_kind": "mission"}, "proposed_kind"),
        ({"service_id": "feature_1", "proposed_kind": None}, "service_id"),
    ],
)
def test_record_draft_rejects_canvas_fields_for_project_proposal(
    tmp_path: Path,
    kwargs: dict[str, object],
    message: str,
) -> None:
    plot_root, _ = _project(tmp_path)

    with pytest.raises(ValueError, match=message):
        _record(
            str(tmp_path),
            canvas_kind="project",
            proposed_text="프로젝트 이름: 새이름",
            chat_scope="foundation",
            **kwargs,  # type: ignore[arg-type]
        )

    assert list_drafts(plot_root, "alpha") == []


def test_record_draft_tracks_current_conversation_across_reset(tmp_path: Path) -> None:
    plot_root, _ = _project(tmp_path)
    append_user(plot_root, "alpha", "foundation", "codex", "u1", "First conversation")
    first_conversation_id = read_conversation(plot_root, "alpha", "foundation").conversation_id

    first = _record(str(tmp_path))
    archive_current_conversation(plot_root, "alpha", "foundation")
    append_user(plot_root, "alpha", "foundation", "codex", "u2", "Second conversation")
    second_conversation_id = read_conversation(plot_root, "alpha", "foundation").conversation_id
    second = _record(str(tmp_path))

    assert first_conversation_id is not None
    assert second_conversation_id is not None
    assert second_conversation_id != first_conversation_id
    assert (
        read_draft(plot_root, "alpha", str(first["draft_id"])).chat_conversation_id
        == first_conversation_id
    )
    assert (
        read_draft(plot_root, "alpha", str(second["draft_id"])).chat_conversation_id
        == second_conversation_id
    )


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
    draft_id = str(
        _record(
            str(tmp_path),
            proposed_text="Help people shape products together.",
            target_node_ids=[node_id],
        )["draft_id"]
    )

    result = mcp_tools.update_node(
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
    assert "draft_warning" not in result


def test_update_node_same_value_does_not_confirm_draft_or_record_auto_draft(
    tmp_path: Path,
) -> None:
    plot_root, _ = _project(tmp_path)
    statement = "Help people shape products together."
    node = create_canvas_node(
        plot_root,
        "alpha",
        "foundation",
        "mission",
        {"label": "Mission", "statement": statement},
    )["node"]
    node_id = str(node["id"])
    draft_id = str(
        _record(str(tmp_path), proposed_text=statement, target_node_ids=[node_id])["draft_id"]
    )

    result = mcp_tools.update_node(
        str(tmp_path),
        "alpha",
        "foundation",
        node_id,
        {"statement": statement},
        draft_id=draft_id,
    )

    assert result["draft_warning"] == (
        f"draft {draft_id} was not confirmed: this write changed no design content (layout only)"
    )
    assert read_draft(plot_root, "alpha", draft_id).status == "proposed"
    assert [draft.id for draft in list_drafts(plot_root, "alpha")] == [draft_id]


def test_update_node_splits_matching_and_unmatched_fields_between_drafts(
    tmp_path: Path,
) -> None:
    plot_root, _ = _project(tmp_path)
    node = create_canvas_node(plot_root, "alpha", "foundation", "mission", {"label": "Old label"})[
        "node"
    ]
    node_id = str(node["id"])
    draft_id = str(
        _record(
            str(tmp_path),
            proposed_text="Shared direction",
            target_node_ids=[node_id],
        )["draft_id"]
    )

    result = mcp_tools.update_node(
        str(tmp_path),
        "alpha",
        "foundation",
        node_id,
        {"label": "Shared direction", "statement": "An unrelated mission statement."},
        draft_id=draft_id,
    )

    supplied = read_draft(plot_root, "alpha", draft_id)
    assert supplied.status == "confirmed"
    assert supplied.resolved_node_ids == [node_id]
    auto = next(draft for draft in list_drafts(plot_root, "alpha") if draft.origin == "auto")
    assert auto.proposed_text == "statement: An unrelated mission statement."
    assert auto.resolved_node_ids == [node_id]
    assert result["draft_warning"] == (
        f"some fields did not match draft {draft_id}; recorded an auto draft for them"
    )


def test_update_node_single_matching_field_does_not_record_auto_draft(tmp_path: Path) -> None:
    plot_root, _ = _project(tmp_path)
    node = create_canvas_node(plot_root, "alpha", "foundation", "mission", {"label": "Old label"})[
        "node"
    ]
    node_id = str(node["id"])
    draft_id = str(
        _record(
            str(tmp_path),
            proposed_text="Shared direction",
            target_node_ids=[node_id],
        )["draft_id"]
    )

    result = mcp_tools.update_node(
        str(tmp_path),
        "alpha",
        "foundation",
        node_id,
        {"label": "Shared direction"},
        draft_id=draft_id,
    )

    supplied = read_draft(plot_root, "alpha", draft_id)
    assert supplied.status == "confirmed"
    assert supplied.resolved_node_ids == [node_id]
    assert not any(draft.origin == "auto" for draft in list_drafts(plot_root, "alpha"))
    assert "draft_warning" not in result


def test_update_node_with_different_proposal_text_records_auto_draft(
    tmp_path: Path,
) -> None:
    plot_root, _ = _project(tmp_path)
    node = create_canvas_node(plot_root, "alpha", "foundation", "mission", {"label": "Mission"})[
        "node"
    ]
    node_id = str(node["id"])
    first_text = (
        "사람과 AI와 팀이 지금 만드는 것이 왜 필요한지, 전체에서 어디에 놓이는지 늘 알고 만든다."
    )
    second_text = (
        "무엇을 왜 만드는지 매번 다시 설명하지 않아도, 사람과 AI와 팀이 같은 그림을 보며 만든다."
    )
    first_id = str(
        _record(str(tmp_path), proposed_text=first_text, target_node_ids=[node_id])["draft_id"]
    )
    _record(str(tmp_path), proposed_text=second_text, target_node_ids=[node_id])

    result = mcp_tools.update_node(
        str(tmp_path),
        "alpha",
        "foundation",
        node_id,
        {"statement": second_text},
        draft_id=first_id,
    )

    assert result["draft_warning"] == (
        f"draft {first_id} does not match this write; recorded an auto draft instead. "
        "If the person accepted this draft with edits, call resolve_draft with status='edited'."
    )
    assert read_draft(plot_root, "alpha", first_id).status == "proposed"
    auto = next(draft for draft in list_drafts(plot_root, "alpha") if draft.origin == "auto")
    assert auto.status == "confirmed"
    assert auto.proposed_text == f"statement: {second_text}"
    assert auto.resolved_node_ids == [node_id]


def test_update_node_with_matching_proposal_text_confirms_selected_draft(
    tmp_path: Path,
) -> None:
    plot_root, _ = _project(tmp_path)
    node = create_canvas_node(plot_root, "alpha", "foundation", "mission", {"label": "Mission"})[
        "node"
    ]
    node_id = str(node["id"])
    first_text = (
        "사람과 AI와 팀이 지금 만드는 것이 왜 필요한지, 전체에서 어디에 놓이는지 늘 알고 만든다."
    )
    second_text = (
        "무엇을 왜 만드는지 매번 다시 설명하지 않아도, 사람과 AI와 팀이 같은 그림을 보며 만든다."
    )
    _record(str(tmp_path), proposed_text=first_text, target_node_ids=[node_id])
    second_id = str(
        _record(str(tmp_path), proposed_text=second_text, target_node_ids=[node_id])["draft_id"]
    )

    result = mcp_tools.update_node(
        str(tmp_path),
        "alpha",
        "foundation",
        node_id,
        {"statement": second_text},
        draft_id=second_id,
    )

    assert "draft_warning" not in result
    assert read_draft(plot_root, "alpha", second_id).status == "confirmed"
    assert not any(draft.origin == "auto" for draft in list_drafts(plot_root, "alpha"))


@pytest.mark.parametrize(
    ("proposed_text", "written_label"),
    [
        ("라벨: 한 분야보다 여러 분야", "한 분야보다 여러 분야"),
        ("**여러 분야에 두루 쓰이는 도구**", "여러 분야에 두루 쓰이는 도구."),
    ],
)
def test_update_node_text_normalization_confirms_draft(
    tmp_path: Path, proposed_text: str, written_label: str
) -> None:
    plot_root, _ = _project(tmp_path)
    node = create_canvas_node(
        plot_root, "alpha", "foundation", "core_value", {"label": "Old value"}
    )["node"]
    node_id = str(node["id"])
    draft_id = str(
        _record(
            str(tmp_path),
            proposed_text=proposed_text,
            target_node_ids=[node_id],
            proposed_kind="core_value",
        )["draft_id"]
    )

    result = mcp_tools.update_node(
        str(tmp_path),
        "alpha",
        "foundation",
        node_id,
        {"label": written_label},
        draft_id=draft_id,
    )

    assert "draft_warning" not in result
    assert read_draft(plot_root, "alpha", draft_id).status == "confirmed"


def test_update_node_with_sixty_percent_word_overlap_confirms_draft(tmp_path: Path) -> None:
    plot_root, _ = _project(tmp_path)
    node = create_canvas_node(plot_root, "alpha", "foundation", "mission", {"label": "Mission"})[
        "node"
    ]
    node_id = str(node["id"])
    proposed_text = "사람과 AI가 같은 그림을 보며 함께 제품을 만든다"
    draft_id = str(
        _record(str(tmp_path), proposed_text=proposed_text, target_node_ids=[node_id])["draft_id"]
    )

    result = mcp_tools.update_node(
        str(tmp_path),
        "alpha",
        "foundation",
        node_id,
        {"statement": "사람과 AI가 같은 그림을 보며 빠르게 제품을 완성한다"},
        draft_id=draft_id,
    )

    assert "draft_warning" not in result
    assert read_draft(plot_root, "alpha", draft_id).status == "confirmed"


def test_update_node_with_wrong_target_keeps_draft_and_records_auto_draft(
    tmp_path: Path,
) -> None:
    plot_root, _ = _project(tmp_path)
    first = create_canvas_node(plot_root, "alpha", "foundation", "mission", {"label": "First"})[
        "node"
    ]
    second = create_canvas_node(plot_root, "alpha", "foundation", "mission", {"label": "Second"})[
        "node"
    ]
    draft_id = str(_record(str(tmp_path), target_node_ids=[str(first["id"])])["draft_id"])

    result = mcp_tools.update_node(
        str(tmp_path),
        "alpha",
        "foundation",
        str(second["id"]),
        {"statement": "Changed second mission."},
        draft_id=draft_id,
    )

    assert result["draft_warning"] == (
        f"draft {draft_id} does not match this write; recorded an auto draft instead. "
        "If the person accepted this draft with edits, call resolve_draft with status='edited'."
    )
    supplied = read_draft(plot_root, "alpha", draft_id)
    assert supplied.status == "proposed"
    assert supplied.resolved_node_ids == []
    auto = next(draft for draft in list_drafts(plot_root, "alpha") if draft.origin == "auto")
    assert auto.status == "confirmed"
    assert auto.target_node_ids == [second["id"]]
    assert auto.resolved_node_ids == [second["id"]]


def test_update_node_with_wrong_canvas_keeps_draft_and_records_auto_draft(
    tmp_path: Path,
) -> None:
    plot_root, _ = _project(tmp_path)
    node = create_canvas_node(plot_root, "alpha", "foundation", "mission", {"label": "Mission"})[
        "node"
    ]
    draft_id = str(_record(str(tmp_path), canvas_kind="actors", target_node_ids=[])["draft_id"])

    result = mcp_tools.update_node(
        str(tmp_path),
        "alpha",
        "foundation",
        str(node["id"]),
        {"statement": "Changed mission."},
        draft_id=draft_id,
    )

    assert "draft_warning" in result
    assert read_draft(plot_root, "alpha", draft_id).status == "proposed"
    auto = next(draft for draft in list_drafts(plot_root, "alpha") if draft.origin == "auto")
    assert auto.canvas_kind == "foundation"
    assert auto.resolved_node_ids == [node["id"]]


def test_feature_draft_for_another_service_does_not_match_write(tmp_path: Path) -> None:
    plot_root, _ = _project(tmp_path)
    first_feature = create_canvas_node(
        plot_root, "alpha", "services", "feature", {"label": "First feature"}
    )["node"]
    second_feature = create_canvas_node(
        plot_root, "alpha", "services", "feature", {"label": "Second feature"}
    )["node"]
    sync_details_with_overview(plot_root, "alpha")
    step = create_canvas_node(
        plot_root,
        "alpha",
        "feature",
        "step",
        {"label": "Do work"},
        service_id=str(second_feature["id"]),
    )["node"]
    draft_id = str(
        _record(
            str(tmp_path),
            canvas_kind="feature",
            target_node_ids=[],
            proposed_kind="step",
            service_id=str(first_feature["id"]),
        )["draft_id"]
    )

    result = mcp_tools.update_node(
        str(tmp_path),
        "alpha",
        "feature",
        str(step["id"]),
        {"outcome": "Work is complete."},
        service_id=str(second_feature["id"]),
        draft_id=draft_id,
    )

    assert "draft_warning" in result
    assert read_draft(plot_root, "alpha", draft_id).status == "proposed"
    auto = next(draft for draft in list_drafts(plot_root, "alpha") if draft.origin == "auto")
    assert auto.service_id == second_feature["id"]
    assert auto.resolved_node_ids == [step["id"]]


def test_missing_draft_id_still_fails_before_write(tmp_path: Path) -> None:
    plot_root, _ = _project(tmp_path)
    node = create_canvas_node(plot_root, "alpha", "foundation", "mission", {"label": "Mission"})[
        "node"
    ]

    with pytest.raises(FileNotFoundError, match="draft"):
        mcp_tools.update_node(
            str(tmp_path),
            "alpha",
            "foundation",
            str(node["id"]),
            {"statement": "Must not be written."},
            draft_id="draft_missing",
        )

    canvas = read_canvas(plot_root, "alpha", "foundation")
    saved = next(item for item in canvas.nodes if item.id == node["id"])
    assert saved.model_dump().get("statement") == ""
    assert list_drafts(plot_root, "alpha") == []


def test_update_node_rolls_back_when_draft_recording_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plot_root, _ = _project(tmp_path)
    node = create_canvas_node(plot_root, "alpha", "foundation", "mission", {"label": "Original"})[
        "node"
    ]
    before = read_canvas(plot_root, "alpha", "foundation")

    def fail_to_record(*_args: object, **_kwargs: object) -> None:
        raise OSError("draft storage unavailable")

    monkeypatch.setattr(mcp_canvas_write_tools, "finish_node_write_draft", fail_to_record)

    with pytest.raises(OSError, match="draft storage unavailable"):
        mcp_tools.update_node(
            str(tmp_path),
            "alpha",
            "foundation",
            str(node["id"]),
            {"label": "Changed"},
        )

    assert read_canvas(plot_root, "alpha", "foundation") == before


def test_update_canvas_rolls_back_when_draft_recording_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plot_root, _ = _project(tmp_path)
    create_canvas_node(plot_root, "alpha", "services", "service", {"label": "Original"})
    before = read_canvas(plot_root, "alpha", "services")
    changed = before.model_dump(by_alias=True)
    changed["nodes"][0]["label"] = "Changed"
    sync_calls = 0
    real_sync = mcp_canvas_write_tools.sync_details_with_overview

    def track_sync(sync_plot_root: Path, sync_project_id: str) -> dict[str, list[str]]:
        nonlocal sync_calls
        sync_calls += 1
        return real_sync(sync_plot_root, sync_project_id)

    def fail_to_record(*_args: object, **_kwargs: object) -> None:
        raise OSError("draft storage unavailable")

    monkeypatch.setattr(mcp_canvas_write_tools, "sync_details_with_overview", track_sync)
    monkeypatch.setattr(mcp_canvas_write_tools, "finish_canvas_write_draft", fail_to_record)

    with pytest.raises(OSError, match="draft storage unavailable"):
        mcp_tools.update_canvas(str(tmp_path), "alpha", changed)

    assert read_canvas(plot_root, "alpha", "services") == before
    assert sync_calls == 2


def test_update_canvas_rolls_back_when_detail_sync_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plot_root, _ = _project(tmp_path)
    before = read_canvas(plot_root, "alpha", "services")
    create_canvas_node(plot_root, "alpha", "services", "feature", {"label": "Reading list"})
    changed = read_canvas(plot_root, "alpha", "services").model_dump(by_alias=True)
    write_canvas(plot_root, "alpha", before)
    sync_error = OSError("detail sync unavailable")
    sync_calls = 0
    real_sync = mcp_canvas_write_tools.sync_details_with_overview

    def fail_once(sync_plot_root: Path, sync_project_id: str) -> dict[str, list[str]]:
        nonlocal sync_calls
        sync_calls += 1
        if sync_calls == 1:
            raise sync_error
        return real_sync(sync_plot_root, sync_project_id)

    monkeypatch.setattr(mcp_canvas_write_tools, "sync_details_with_overview", fail_once)

    with pytest.raises(OSError, match="detail sync unavailable") as caught:
        mcp_tools.update_canvas(str(tmp_path), "alpha", changed)

    assert caught.value is sync_error
    assert read_canvas(plot_root, "alpha", "services") == before
    assert sync_calls == 2


def test_update_canvas_rollback_restores_archived_feature_detail(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plot_root, _ = _project(tmp_path)
    feature = create_canvas_node(
        plot_root, "alpha", "services", "feature", {"label": "Reading list"}
    )["node"]
    feature_id = str(feature["id"])
    sync_details_with_overview(plot_root, "alpha")
    detail = read_canvas(plot_root, "alpha", "feature", service_id=feature_id)
    edited_detail = detail.model_copy(
        update={"nodes": [detail.nodes[0].model_copy(update={"label": "Edited detail root"})]}
    )
    write_canvas(plot_root, "alpha", edited_detail)
    before = read_canvas(plot_root, "alpha", "services")
    changed = before.model_dump(by_alias=True)
    changed["nodes"] = [node for node in changed["nodes"] if node["id"] != feature_id]

    def fail_to_record(*_args: object, **_kwargs: object) -> None:
        raise OSError("draft storage unavailable")

    monkeypatch.setattr(mcp_canvas_write_tools, "finish_canvas_write_draft", fail_to_record)

    with pytest.raises(OSError, match="draft storage unavailable"):
        mcp_tools.update_canvas(str(tmp_path), "alpha", changed)

    assert read_canvas(plot_root, "alpha", "services") == before
    assert read_canvas(plot_root, "alpha", "feature", service_id=feature_id) == edited_detail


def test_create_node_rolls_back_when_draft_recording_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plot_root, _ = _project(tmp_path)
    before = read_canvas(plot_root, "alpha", "services")
    sync_calls = 0
    real_sync = mcp_canvas_write_tools.sync_details_with_overview

    def track_sync(sync_plot_root: Path, sync_project_id: str) -> dict[str, list[str]]:
        nonlocal sync_calls
        sync_calls += 1
        return real_sync(sync_plot_root, sync_project_id)

    def fail_to_record(*_args: object, **_kwargs: object) -> None:
        raise OSError("draft storage unavailable")

    monkeypatch.setattr(mcp_canvas_write_tools, "sync_details_with_overview", track_sync)
    monkeypatch.setattr(mcp_canvas_write_tools, "finish_node_write_draft", fail_to_record)

    with pytest.raises(OSError, match="draft storage unavailable"):
        mcp_tools.create_node(
            str(tmp_path), "alpha", "services", "feature", {"label": "Reading list"}
        )

    assert read_canvas(plot_root, "alpha", "services") == before
    assert sync_calls == 2


def test_create_edge_rolls_back_when_draft_recording_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plot_root, _ = _project(tmp_path)
    source = create_canvas_node(plot_root, "alpha", "entities", "entity", {"label": "Customer"})[
        "node"
    ]
    target = create_canvas_node(plot_root, "alpha", "entities", "entity", {"label": "Order"})[
        "node"
    ]
    before = read_canvas(plot_root, "alpha", "entities")

    def fail_to_record(*_args: object, **_kwargs: object) -> None:
        raise OSError("draft storage unavailable")

    monkeypatch.setattr(mcp_canvas_write_tools, "finish_write_draft", fail_to_record)

    with pytest.raises(OSError, match="draft storage unavailable"):
        mcp_tools.create_edge(
            str(tmp_path),
            "alpha",
            "entities",
            str(source["id"]),
            str(target["id"]),
        )

    assert read_canvas(plot_root, "alpha", "entities") == before


def test_set_node_references_rolls_back_when_draft_recording_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plot_root, _ = _project(tmp_path)
    actor = create_canvas_node(plot_root, "alpha", "actors", "actor", {"label": "Reader"})["node"]
    service = create_canvas_node(plot_root, "alpha", "services", "service", {"label": "Reading"})[
        "node"
    ]
    before = read_canvas(plot_root, "alpha", "services")

    def fail_to_record(*_args: object, **_kwargs: object) -> None:
        raise OSError("draft storage unavailable")

    monkeypatch.setattr(mcp_canvas_write_tools, "finish_write_draft", fail_to_record)

    with pytest.raises(OSError, match="draft storage unavailable"):
        mcp_tools.set_node_references(
            str(tmp_path),
            "alpha",
            "services",
            str(service["id"]),
            {"ref_actor_ids": [str(actor["id"])]},
        )

    assert read_canvas(plot_root, "alpha", "services") == before


def test_draft_error_keeps_original_exception_when_rollback_fails() -> None:
    draft_error = OSError("draft storage unavailable")

    def fail_to_record(_written: object) -> None:
        raise draft_error

    def fail_to_rollback() -> None:
        raise RuntimeError("canvas storage unavailable")

    with pytest.raises(OSError, match="draft storage unavailable") as caught:
        with_draft_or_rollback(lambda: object(), fail_to_record, fail_to_rollback)

    assert caught.value is draft_error
    assert caught.value.__notes__ == [
        "rollback after draft persistence failure failed: "
        "RuntimeError('canvas storage unavailable')"
    ]


def test_write_error_calls_rollback_and_keeps_original_exception() -> None:
    write_error = OSError("canvas storage unavailable")
    rollback_called = False

    def fail_to_write() -> object:
        raise write_error

    def record_draft(_written: object) -> None:
        pytest.fail("draft recording must not run after a write failure")

    def rollback() -> None:
        nonlocal rollback_called
        rollback_called = True

    with pytest.raises(OSError, match="canvas storage unavailable") as caught:
        with_draft_or_rollback(fail_to_write, record_draft, rollback)

    assert caught.value is write_error
    assert rollback_called


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
    assert "draft_warning" not in created


def test_create_node_splits_matching_and_unmatched_fields_between_drafts(
    tmp_path: Path,
) -> None:
    plot_root, _ = _project(tmp_path)
    draft_id = str(
        _record(
            str(tmp_path),
            proposed_text="Clarity",
            target_node_ids=[],
            proposed_kind="core_value",
        )["draft_id"]
    )

    result = mcp_tools.create_node(
        str(tmp_path),
        "alpha",
        "foundation",
        "core_value",
        {"label": "Clarity", "body": "An unrelated explanation."},
        draft_id=draft_id,
    )

    node_id = str(result["node"]["id"])
    supplied = read_draft(plot_root, "alpha", draft_id)
    assert supplied.status == "confirmed"
    assert supplied.resolved_node_ids == [node_id]
    auto = next(draft for draft in list_drafts(plot_root, "alpha") if draft.origin == "auto")
    assert auto.proposed_text == "body: An unrelated explanation."
    assert auto.resolved_node_ids == [node_id]
    assert result["draft_warning"] == (
        f"some fields did not match draft {draft_id}; recorded an auto draft for them"
    )


def test_create_node_with_different_proposal_text_records_auto_draft(tmp_path: Path) -> None:
    plot_root, _ = _project(tmp_path)
    draft_id = str(
        _record(
            str(tmp_path),
            proposed_text="Clarity",
            target_node_ids=[],
            proposed_kind="core_value",
        )["draft_id"]
    )

    result = mcp_tools.create_node(
        str(tmp_path),
        "alpha",
        "foundation",
        "core_value",
        {"label": "Breadth"},
        draft_id=draft_id,
    )

    assert "draft_warning" in result
    assert read_draft(plot_root, "alpha", draft_id).status == "proposed"
    auto = next(draft for draft in list_drafts(plot_root, "alpha") if draft.origin == "auto")
    assert auto.status == "confirmed"
    assert auto.proposed_text == "label: Breadth"


def test_create_node_draft_can_target_near_parent(tmp_path: Path) -> None:
    plot_root, _ = _project(tmp_path)
    parent = create_canvas_node(plot_root, "alpha", "foundation", "mission", {"label": "Mission"})[
        "node"
    ]
    draft_id = str(
        _record(
            str(tmp_path),
            proposed_text="Clarity",
            target_node_ids=[str(parent["id"])],
            proposed_kind="core_value",
        )["draft_id"]
    )

    result = mcp_tools.create_node(
        str(tmp_path),
        "alpha",
        "foundation",
        "core_value",
        {"label": "Clarity"},
        near=str(parent["id"]),
        draft_id=draft_id,
    )

    assert "draft_warning" not in result
    draft = read_draft(plot_root, "alpha", draft_id)
    assert draft.status == "confirmed"
    assert draft.resolved_node_ids == [result["node"]["id"]]


def test_rejected_draft_does_not_match_write(tmp_path: Path) -> None:
    plot_root, _ = _project(tmp_path)
    node = create_canvas_node(plot_root, "alpha", "foundation", "mission", {"label": "Mission"})[
        "node"
    ]
    node_id = str(node["id"])
    draft_id = str(_record(str(tmp_path), target_node_ids=[node_id])["draft_id"])
    mcp_tools.resolve_draft(str(tmp_path), "alpha", draft_id, "rejected")

    result = mcp_tools.update_node(
        str(tmp_path),
        "alpha",
        "foundation",
        node_id,
        {"statement": "Changed mission."},
        draft_id=draft_id,
    )

    assert "draft_warning" in result
    assert read_draft(plot_root, "alpha", draft_id).status == "rejected"
    auto = next(draft for draft in list_drafts(plot_root, "alpha") if draft.origin == "auto")
    assert auto.resolved_node_ids == [node_id]


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
    append_user(plot_root, "alpha", "entities", "codex", "u1", "Define Order")
    conversation_id = read_conversation(plot_root, "alpha", "entities").conversation_id

    mcp_tools.create_node(
        str(tmp_path),
        "alpha",
        "entities",
        "entity",
        {"label": "Order"},
        chat_scope="entities",
    )

    draft = list_drafts(plot_root, "alpha")[0]
    assert draft.chat_scope == "entities"
    assert draft.chat_conversation_id == conversation_id


def test_create_edge_without_draft_records_both_endpoints_and_relationship(
    tmp_path: Path,
) -> None:
    plot_root, _ = _project(tmp_path)
    source = create_canvas_node(plot_root, "alpha", "entities", "entity", {"label": "Customer"})[
        "node"
    ]
    target = create_canvas_node(plot_root, "alpha", "entities", "entity", {"label": "Order"})[
        "node"
    ]

    mcp_tools.create_edge(
        str(tmp_path),
        "alpha",
        "entities",
        str(source["id"]),
        str(target["id"]),
        label="places",
    )

    draft = list_drafts(plot_root, "alpha")[0]
    assert draft.status == "confirmed"
    assert draft.origin == "auto"
    assert draft.proposed_kind == "edge"
    assert draft.proposed_text == "관계: Customer → Order (places)"
    assert draft.target_node_ids == [source["id"], target["id"]]
    assert draft.resolved_node_ids == [source["id"], target["id"]]


def test_create_edge_with_wrong_draft_records_auto_draft_and_warning(tmp_path: Path) -> None:
    plot_root, _ = _project(tmp_path)
    source = create_canvas_node(plot_root, "alpha", "entities", "entity", {"label": "Customer"})[
        "node"
    ]
    target = create_canvas_node(plot_root, "alpha", "entities", "entity", {"label": "Order"})[
        "node"
    ]
    other = create_canvas_node(plot_root, "alpha", "entities", "entity", {"label": "Invoice"})[
        "node"
    ]
    draft_id = str(
        _record(
            str(tmp_path),
            canvas_kind="entities",
            target_node_ids=[str(other["id"])],
            proposed_kind="edge",
        )["draft_id"]
    )

    result = mcp_tools.create_edge(
        str(tmp_path),
        "alpha",
        "entities",
        str(source["id"]),
        str(target["id"]),
        draft_id=draft_id,
    )

    assert "draft_warning" in result
    assert read_draft(plot_root, "alpha", draft_id).status == "proposed"
    auto = next(draft for draft in list_drafts(plot_root, "alpha") if draft.origin == "auto")
    assert auto.target_node_ids == [source["id"], target["id"]]
    assert auto.resolved_node_ids == [source["id"], target["id"]]


def test_set_node_references_without_draft_records_reference_change(tmp_path: Path) -> None:
    plot_root, _ = _project(tmp_path)
    actor = create_canvas_node(plot_root, "alpha", "actors", "actor", {"label": "Reader"})["node"]
    service = create_canvas_node(plot_root, "alpha", "services", "service", {"label": "Reading"})[
        "node"
    ]

    mcp_tools.set_node_references(
        str(tmp_path),
        "alpha",
        "services",
        str(service["id"]),
        {"ref_actor_ids": [str(actor["id"])]},
    )

    draft = list_drafts(plot_root, "alpha")[0]
    assert draft.status == "confirmed"
    assert draft.origin == "auto"
    assert draft.proposed_kind == "references"
    assert draft.proposed_text == f"참조: ref_actor_ids = {actor['id']}"
    assert draft.target_node_ids == [service["id"]]
    assert draft.resolved_node_ids == [service["id"]]


def test_set_node_references_with_wrong_draft_records_auto_draft_and_warning(
    tmp_path: Path,
) -> None:
    plot_root, _ = _project(tmp_path)
    actor = create_canvas_node(plot_root, "alpha", "actors", "actor", {"label": "Reader"})["node"]
    service = create_canvas_node(plot_root, "alpha", "services", "service", {"label": "Reading"})[
        "node"
    ]
    draft_id = str(
        _record(
            str(tmp_path),
            canvas_kind="services",
            target_node_ids=["service_other"],
            proposed_kind="references",
        )["draft_id"]
    )

    result = mcp_tools.set_node_references(
        str(tmp_path),
        "alpha",
        "services",
        str(service["id"]),
        {"ref_actor_ids": [str(actor["id"])]},
        draft_id=draft_id,
    )

    assert "draft_warning" in result
    assert read_draft(plot_root, "alpha", draft_id).status == "proposed"
    auto = next(draft for draft in list_drafts(plot_root, "alpha") if draft.origin == "auto")
    assert auto.resolved_node_ids == [service["id"]]


def test_set_node_references_same_value_does_not_confirm_draft_or_record_auto_draft(
    tmp_path: Path,
) -> None:
    plot_root, _ = _project(tmp_path)
    actor = create_canvas_node(plot_root, "alpha", "actors", "actor", {"label": "Reader"})["node"]
    service = create_canvas_node(plot_root, "alpha", "services", "service", {"label": "Reading"})[
        "node"
    ]
    refs = {"ref_actor_ids": [str(actor["id"])]}
    set_canvas_node_references(plot_root, "alpha", "services", str(service["id"]), refs)
    draft_id = str(
        _record(
            str(tmp_path),
            canvas_kind="services",
            proposed_text="Keep Reader linked",
            target_node_ids=[str(service["id"])],
            proposed_kind="references",
        )["draft_id"]
    )

    result = mcp_tools.set_node_references(
        str(tmp_path),
        "alpha",
        "services",
        str(service["id"]),
        refs,
        draft_id=draft_id,
    )

    assert result["draft_warning"] == (
        f"draft {draft_id} was not confirmed: this write changed no design content (layout only)"
    )
    assert read_draft(plot_root, "alpha", draft_id).status == "proposed"
    assert [draft.id for draft in list_drafts(plot_root, "alpha")] == [draft_id]


def test_update_canvas_records_content_diff_but_not_position_only_change(tmp_path: Path) -> None:
    plot_root, _ = _project(tmp_path)
    existing = create_canvas_node(plot_root, "alpha", "actors", "actor", {"label": "Old name"})[
        "node"
    ]
    before = read_canvas(plot_root, "alpha", "actors").model_dump(by_alias=True)
    before["nodes"][0]["label"] = "Renamed"
    before["nodes"].append({"id": "actor_added", "kind": "actor", "label": "Added"})

    mcp_tools.update_canvas(str(tmp_path), "alpha", before)

    draft = list_drafts(plot_root, "alpha")[0]
    assert draft.status == "confirmed"
    assert draft.origin == "auto"
    assert draft.proposed_kind == "canvas"
    assert draft.proposed_text.startswith("더함: Added / 바꿈: Renamed.label / 뺌: 없음")
    assert "선:" in draft.proposed_text
    assert draft.target_node_ids == ["actor_added", existing["id"]]
    assert draft.resolved_node_ids == ["actor_added", existing["id"]]

    moved = read_canvas(plot_root, "alpha", "actors").model_dump(by_alias=True)
    moved["nodes"][0]["x"] += 200
    mcp_tools.update_canvas(str(tmp_path), "alpha", moved)

    assert len(list_drafts(plot_root, "alpha")) == 1


def test_update_canvas_layout_only_keeps_empty_target_draft_proposed(tmp_path: Path) -> None:
    plot_root, _ = _project(tmp_path)
    create_canvas_node(plot_root, "alpha", "actors", "actor", {"label": "Reader"})
    draft_id = str(
        _record(
            str(tmp_path),
            canvas_kind="actors",
            proposed_text="A new actor",
            target_node_ids=[],
            proposed_kind="canvas",
        )["draft_id"]
    )
    canvas = read_canvas(plot_root, "alpha", "actors").model_dump(by_alias=True)
    canvas["nodes"][0]["x"] += 200

    result = mcp_tools.update_canvas(str(tmp_path), "alpha", canvas, draft_id=draft_id)

    assert result["draft_warning"] == (
        f"draft {draft_id} was not confirmed: this write changed no design content (layout only)"
    )
    assert read_draft(plot_root, "alpha", draft_id).status == "proposed"
    assert [draft.id for draft in list_drafts(plot_root, "alpha")] == [draft_id]


def test_update_canvas_layout_only_keeps_targeted_draft_proposed(tmp_path: Path) -> None:
    plot_root, _ = _project(tmp_path)
    actor = create_canvas_node(plot_root, "alpha", "actors", "actor", {"label": "Reader"})["node"]
    draft_id = str(
        _record(
            str(tmp_path),
            canvas_kind="actors",
            proposed_text="Refine Reader",
            target_node_ids=[str(actor["id"])],
            proposed_kind="canvas",
        )["draft_id"]
    )
    canvas = read_canvas(plot_root, "alpha", "actors").model_dump(by_alias=True)
    canvas["nodes"][0]["x"] += 200

    result = mcp_tools.update_canvas(str(tmp_path), "alpha", canvas, draft_id=draft_id)

    assert result["draft_warning"] == (
        f"draft {draft_id} was not confirmed: this write changed no design content (layout only)"
    )
    assert read_draft(plot_root, "alpha", draft_id).status == "proposed"
    assert [draft.id for draft in list_drafts(plot_root, "alpha")] == [draft_id]


def test_update_canvas_with_wrong_draft_records_auto_draft_and_warning(tmp_path: Path) -> None:
    plot_root, _ = _project(tmp_path)
    changed = create_canvas_node(plot_root, "alpha", "actors", "actor", {"label": "Old name"})[
        "node"
    ]
    other = create_canvas_node(plot_root, "alpha", "actors", "actor", {"label": "Other"})["node"]
    draft_id = str(
        _record(
            str(tmp_path),
            canvas_kind="actors",
            target_node_ids=[str(other["id"])],
            proposed_kind="canvas",
        )["draft_id"]
    )
    canvas = read_canvas(plot_root, "alpha", "actors").model_dump(by_alias=True)
    canvas["nodes"][0]["label"] = "New name"

    result = mcp_tools.update_canvas(str(tmp_path), "alpha", canvas, draft_id=draft_id)

    assert "draft_warning" in result
    assert read_draft(plot_root, "alpha", draft_id).status == "proposed"
    auto = next(draft for draft in list_drafts(plot_root, "alpha") if draft.origin == "auto")
    assert auto.target_node_ids == [changed["id"]]
    assert auto.resolved_node_ids == [changed["id"]]


def test_update_canvas_with_different_proposal_text_records_auto_draft(tmp_path: Path) -> None:
    plot_root, _ = _project(tmp_path)
    changed = create_canvas_node(
        plot_root, "alpha", "actors", "actor", {"label": "Old name", "body": "Old body"}
    )["node"]
    draft_id = str(
        _record(
            str(tmp_path),
            canvas_kind="actors",
            proposed_text="A completely different actor",
            target_node_ids=[str(changed["id"])],
            proposed_kind="canvas",
        )["draft_id"]
    )
    canvas = read_canvas(plot_root, "alpha", "actors").model_dump(by_alias=True)
    canvas["nodes"][0]["label"] = "New name"
    canvas["nodes"][0]["body"] = "People who need a clear next step"

    result = mcp_tools.update_canvas(str(tmp_path), "alpha", canvas, draft_id=draft_id)

    assert "draft_warning" in result
    assert read_draft(plot_root, "alpha", draft_id).status == "proposed"
    auto = next(draft for draft in list_drafts(plot_root, "alpha") if draft.origin == "auto")
    assert auto.status == "confirmed"
    assert auto.resolved_node_ids == [changed["id"]]


def test_update_canvas_splits_matching_and_unmatched_fields_between_drafts(
    tmp_path: Path,
) -> None:
    plot_root, _ = _project(tmp_path)
    changed = create_canvas_node(
        plot_root, "alpha", "actors", "actor", {"label": "Old name", "body": "Old body"}
    )["node"]
    written_body = "People who need a clear next step"
    draft_id = str(
        _record(
            str(tmp_path),
            canvas_kind="actors",
            proposed_text=written_body,
            target_node_ids=[str(changed["id"])],
            proposed_kind="canvas",
        )["draft_id"]
    )
    canvas = read_canvas(plot_root, "alpha", "actors").model_dump(by_alias=True)
    canvas["nodes"][0]["label"] = "New name"
    canvas["nodes"][0]["body"] = written_body

    result = mcp_tools.update_canvas(str(tmp_path), "alpha", canvas, draft_id=draft_id)

    supplied = read_draft(plot_root, "alpha", draft_id)
    assert supplied.status == "confirmed"
    assert supplied.resolved_node_ids == [changed["id"]]
    autos = [draft for draft in list_drafts(plot_root, "alpha") if draft.origin == "auto"]
    assert len(autos) == 1
    assert autos[0].proposed_text == "더함: 없음 / 바꿈: New name.label / 뺌: 없음"
    assert autos[0].target_node_ids == [changed["id"]]
    assert autos[0].resolved_node_ids == [changed["id"]]
    assert result["draft_warning"] == (
        f"some fields did not match draft {draft_id}; recorded an auto draft for them"
    )


def test_update_canvas_single_matching_field_does_not_record_auto_draft(tmp_path: Path) -> None:
    plot_root, _ = _project(tmp_path)
    changed = create_canvas_node(
        plot_root, "alpha", "actors", "actor", {"label": "Old name", "body": "Old body"}
    )["node"]
    written_body = "People who need a clear next step"
    draft_id = str(
        _record(
            str(tmp_path),
            canvas_kind="actors",
            proposed_text=written_body,
            target_node_ids=[str(changed["id"])],
            proposed_kind="canvas",
        )["draft_id"]
    )
    canvas = read_canvas(plot_root, "alpha", "actors").model_dump(by_alias=True)
    canvas["nodes"][0]["body"] = written_body

    result = mcp_tools.update_canvas(str(tmp_path), "alpha", canvas, draft_id=draft_id)

    supplied = read_draft(plot_root, "alpha", draft_id)
    assert supplied.status == "confirmed"
    assert supplied.resolved_node_ids == [changed["id"]]
    assert not any(draft.origin == "auto" for draft in list_drafts(plot_root, "alpha"))
    assert "draft_warning" not in result


def test_update_canvas_splits_matching_and_unmatched_node_changes(tmp_path: Path) -> None:
    plot_root, _ = _project(tmp_path)
    matched = create_canvas_node(
        plot_root, "alpha", "actors", "actor", {"label": "Matched", "body": "Old body"}
    )["node"]
    unmatched = create_canvas_node(
        plot_root, "alpha", "actors", "actor", {"label": "Unmatched", "body": "Old body"}
    )["node"]
    matched_text = "People who need a clear next step"
    draft_id = str(
        _record(
            str(tmp_path),
            canvas_kind="actors",
            proposed_text=matched_text,
            target_node_ids=[str(matched["id"])],
            proposed_kind="canvas",
        )["draft_id"]
    )
    canvas = read_canvas(plot_root, "alpha", "actors").model_dump(by_alias=True)
    nodes = {str(node["id"]): node for node in canvas["nodes"]}
    nodes[str(matched["id"])]["body"] = matched_text
    nodes[str(unmatched["id"])]["body"] = "A separate actor change"

    result = mcp_tools.update_canvas(str(tmp_path), "alpha", canvas, draft_id=draft_id)

    supplied = read_draft(plot_root, "alpha", draft_id)
    assert supplied.status == "confirmed"
    assert supplied.resolved_node_ids == [matched["id"]]
    auto = next(draft for draft in list_drafts(plot_root, "alpha") if draft.origin == "auto")
    assert auto.proposed_text == "더함: 없음 / 바꿈: Unmatched.body / 뺌: 없음"
    assert auto.target_node_ids == [unmatched["id"]]
    assert auto.resolved_node_ids == [unmatched["id"]]
    assert result["draft_warning"] == (
        f"some fields did not match draft {draft_id}; recorded an auto draft for them"
    )


def test_update_canvas_assigns_incident_edge_to_matching_added_node_draft(
    tmp_path: Path,
) -> None:
    plot_root, _ = _project(tmp_path)
    existing = create_canvas_node(plot_root, "alpha", "actors", "actor", {"label": "Existing"})[
        "node"
    ]
    draft_id = str(
        _record(
            str(tmp_path),
            canvas_kind="actors",
            proposed_text="New collaborator",
            target_node_ids=[],
            proposed_kind="canvas",
        )["draft_id"]
    )
    canvas = read_canvas(plot_root, "alpha", "actors").model_dump(by_alias=True)
    canvas["nodes"].append({"id": "actor_new", "kind": "actor", "label": "New collaborator"})
    canvas["edges"].append({"id": "edge_new", "source": str(existing["id"]), "target": "actor_new"})

    result = mcp_tools.update_canvas(str(tmp_path), "alpha", canvas, draft_id=draft_id)

    supplied = read_draft(plot_root, "alpha", draft_id)
    assert supplied.status == "confirmed"
    assert supplied.resolved_node_ids == ["actor_new"]
    assert not any(draft.origin == "auto" for draft in list_drafts(plot_root, "alpha"))
    assert "draft_warning" not in result


def test_update_canvas_keeps_unrelated_edge_in_unmatched_auto_draft(tmp_path: Path) -> None:
    plot_root, _ = _project(tmp_path)
    matched = create_canvas_node(
        plot_root, "alpha", "actors", "actor", {"label": "Matched", "body": "Old body"}
    )["node"]
    unmatched = create_canvas_node(
        plot_root, "alpha", "actors", "actor", {"label": "Unmatched", "body": "Old body"}
    )["node"]
    first = create_canvas_node(plot_root, "alpha", "actors", "actor", {"label": "First"})["node"]
    second = create_canvas_node(plot_root, "alpha", "actors", "actor", {"label": "Second"})["node"]
    matched_text = "People who need a clear next step"
    draft_id = str(
        _record(
            str(tmp_path),
            canvas_kind="actors",
            proposed_text=matched_text,
            target_node_ids=[str(matched["id"])],
            proposed_kind="canvas",
        )["draft_id"]
    )
    canvas = read_canvas(plot_root, "alpha", "actors").model_dump(by_alias=True)
    nodes = {str(node["id"]): node for node in canvas["nodes"]}
    nodes[str(matched["id"])]["body"] = matched_text
    nodes[str(unmatched["id"])]["body"] = "A separate actor change"
    canvas["edges"].append(
        {
            "id": "edge_unrelated",
            "source": str(first["id"]),
            "target": str(second["id"]),
        }
    )

    result = mcp_tools.update_canvas(str(tmp_path), "alpha", canvas, draft_id=draft_id)

    supplied = read_draft(plot_root, "alpha", draft_id)
    assert supplied.status == "confirmed"
    assert supplied.resolved_node_ids == [matched["id"]]
    auto = next(draft for draft in list_drafts(plot_root, "alpha") if draft.origin == "auto")
    assert auto.proposed_text == (
        "더함: 없음 / 바꿈: Unmatched.body / 뺌: 없음\n선: 더함 1 / 바꿈 0 / 뺌 0"
    )
    assert auto.target_node_ids == [unmatched["id"]]
    assert auto.resolved_node_ids == [unmatched["id"]]
    assert result["draft_warning"] == (
        f"some fields did not match draft {draft_id}; recorded an auto draft for them"
    )


@pytest.mark.parametrize("tool_name", ["create_edge", "set_node_references", "update_canvas"])
def test_canvas_write_with_draft_id_confirms_without_creating_auto_draft(
    tmp_path: Path, tool_name: str
) -> None:
    plot_root, _ = _project(tmp_path)
    first = create_canvas_node(plot_root, "alpha", "actors", "actor", {"label": "First"})["node"]
    second = create_canvas_node(plot_root, "alpha", "actors", "actor", {"label": "Second"})["node"]
    draft_canvas_kind = "services" if tool_name == "set_node_references" else "actors"
    draft_id = str(
        _record(
            str(tmp_path),
            canvas_kind=draft_canvas_kind,
            proposed_text=(
                "Changed" if tool_name == "update_canvas" else "Apply the canvas change"
            ),
            target_node_ids=[],
            proposed_kind=tool_name,
        )["draft_id"]
    )

    if tool_name == "create_edge":
        mcp_tools.create_edge(
            str(tmp_path),
            "alpha",
            "actors",
            str(first["id"]),
            str(second["id"]),
            draft_id=draft_id,
        )
        expected_ids = [first["id"], second["id"]]
    elif tool_name == "set_node_references":
        service = create_canvas_node(
            plot_root, "alpha", "services", "service", {"label": "Reading"}
        )["node"]
        mcp_tools.set_node_references(
            str(tmp_path),
            "alpha",
            "services",
            str(service["id"]),
            {"ref_actor_ids": [str(first["id"])]},
            draft_id=draft_id,
        )
        expected_ids = [service["id"]]
    else:
        canvas = read_canvas(plot_root, "alpha", "actors").model_dump(by_alias=True)
        canvas["nodes"][0]["label"] = "Changed"
        mcp_tools.update_canvas(str(tmp_path), "alpha", canvas, draft_id=draft_id)
        expected_ids = [first["id"]]

    draft = read_draft(plot_root, "alpha", draft_id)
    assert draft.status == "confirmed"
    assert draft.resolved_node_ids == expected_ids
    assert [item.id for item in list_drafts(plot_root, "alpha")] == [draft_id]


def test_chat_scope_environment_wins_and_explicit_fills_when_environment_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plot_root, _ = _project(tmp_path)
    node = create_canvas_node(plot_root, "alpha", "actors", "actor", {"label": "Reader"})["node"]
    monkeypatch.setenv("MASHBILL_CHAT_SCOPE", "foundation")

    environment_over_explicit = mcp_tools.record_draft(
        str(tmp_path),
        "alpha",
        "actors",
        "Reader needs a clear next step.",
        "The conversation established the need.",
        chat_scope="actors",
    )
    environment_over_empty = mcp_tools.record_draft(
        str(tmp_path),
        "alpha",
        "actors",
        "Writer needs a clear next step.",
        "The conversation established the need.",
    )
    mcp_tools.update_node(
        str(tmp_path),
        "alpha",
        "actors",
        str(node["id"]),
        {"label": "Updated reader"},
        chat_scope="actors",
    )

    monkeypatch.delenv("MASHBILL_CHAT_SCOPE")
    explicit_without_environment = mcp_tools.record_draft(
        str(tmp_path),
        "alpha",
        "actors",
        "Editor needs a clear next step.",
        "The conversation established the need.",
        chat_scope="actors",
    )

    drafts = {draft.id: draft for draft in list_drafts(plot_root, "alpha")}
    auto = next(draft for draft in drafts.values() if draft.origin == "auto")
    assert drafts[str(environment_over_explicit["draft_id"])].chat_scope == "foundation"
    assert drafts[str(explicit_without_environment["draft_id"])].chat_scope == "actors"
    assert drafts[str(environment_over_empty["draft_id"])].chat_scope == "foundation"
    assert auto.chat_scope == "foundation"


def test_legacy_draft_without_origin_reads_as_recorded(tmp_path: Path) -> None:
    plot_root, _ = _project(tmp_path)
    draft_id = str(_record(str(tmp_path))["draft_id"])
    path = plot_root / "drafts" / f"{draft_id}.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw.pop("origin", None)
    path.write_text(json.dumps(raw), encoding="utf-8")

    assert read_draft(plot_root, "alpha", draft_id).origin == "recorded"


def test_existing_auto_draft_file_still_reads_with_origin(tmp_path: Path) -> None:
    plot_root, _ = _project(tmp_path)
    raw = DraftDoc(
        id="draft_auto_existing",
        created="2026-09-29T00:00:00+00:00",
        updated="2026-09-29T00:00:00+00:00",
        canvas_kind="actors",
        proposed_text="label: Reader",
        rationale="Recorded after a write.",
        status="confirmed",
        origin="auto",
        chat_scope="actors",
    ).model_dump()
    path = plot_root / "drafts" / "draft_auto_existing.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(raw), encoding="utf-8")

    assert read_draft(plot_root, "alpha", "draft_auto_existing").origin == "auto"


@pytest.mark.parametrize("canvas_kind", ["foundation", "actors", "services", "entities", "feature"])
def test_existing_canvas_draft_files_still_read(tmp_path: Path, canvas_kind: str) -> None:
    plot_root, _ = _project(tmp_path)
    draft_id = f"draft_existing_{canvas_kind}"
    path = plot_root / "drafts" / f"{draft_id}.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "id": draft_id,
                "created": "2026-09-29T00:00:00+00:00",
                "updated": "2026-09-29T00:00:00+00:00",
                "canvas_kind": canvas_kind,
                "service_id": "feature_1" if canvas_kind == "feature" else None,
                "target_node_ids": [],
                "proposed_kind": None,
                "proposed_text": "Existing proposal",
                "rationale": "Existing rationale",
                "status": "proposed",
                "origin": "recorded",
                "chat_scope": canvas_kind,
                "resolved_node_ids": [],
            }
        ),
        encoding="utf-8",
    )

    draft = read_draft(plot_root, "alpha", draft_id)
    assert draft.canvas_kind == canvas_kind
    assert draft.chat_conversation_id is None


def test_mcp_rename_project_records_confirmed_project_draft(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plot_root, _ = _project(tmp_path)
    monkeypatch.setenv("MASHBILL_CHAT_SCOPE", "project")
    append_user(plot_root, "alpha", "project", "codex", "u1", "Rename the project")
    conversation_id = read_conversation(plot_root, "alpha", "project").conversation_id

    renamed = mcp_tools.rename_project(str(tmp_path), "alpha", "Renamed Alpha")

    assert renamed["name"] == "Renamed Alpha"
    drafts = list_drafts(plot_root, "alpha")
    assert len(drafts) == 1
    draft = drafts[0]
    assert draft.origin == "auto"
    assert draft.status == "confirmed"
    assert draft.canvas_kind == "project"
    assert draft.proposed_text == "프로젝트 이름: Alpha → Renamed Alpha"
    assert draft.rationale == AUTO_DRAFT_RATIONALE
    assert draft.target_node_ids == []
    assert draft.resolved_node_ids == []
    assert draft.chat_scope == "project"
    assert draft.chat_conversation_id == conversation_id


def test_mcp_rename_project_to_same_name_records_no_draft(tmp_path: Path) -> None:
    plot_root, _ = _project(tmp_path)

    renamed = mcp_tools.rename_project(str(tmp_path), "alpha", "Alpha")

    assert renamed["name"] == "Alpha"
    assert list_drafts(plot_root, "alpha") == []


def test_mcp_rename_project_confirms_supplied_project_draft(tmp_path: Path) -> None:
    plot_root, _ = _project(tmp_path)
    draft_id = str(
        _record(
            str(tmp_path),
            canvas_kind="project",
            proposed_text="프로젝트 이름: 새이름",
            chat_scope="foundation",
            proposed_kind=None,
        )["draft_id"]
    )

    renamed = mcp_tools.rename_project(str(tmp_path), "alpha", "새이름", draft_id=draft_id)

    assert renamed["name"] == "새이름"
    drafts = list_drafts(plot_root, "alpha")
    assert [draft.id for draft in drafts] == [draft_id]
    assert drafts[0].status == "confirmed"
    assert drafts[0].origin == "recorded"


def test_mcp_rename_project_confirms_matching_open_project_draft(tmp_path: Path) -> None:
    plot_root, _ = _project(tmp_path)
    draft_id = str(
        _record(
            str(tmp_path),
            canvas_kind="project",
            proposed_text="프로젝트 이름: **새이름**",
            chat_scope="foundation",
            proposed_kind=None,
        )["draft_id"]
    )

    renamed = mcp_tools.rename_project(str(tmp_path), "alpha", "새이름")

    assert renamed["name"] == "새이름"
    drafts = list_drafts(plot_root, "alpha")
    assert [draft.id for draft in drafts] == [draft_id]
    assert drafts[0].status == "confirmed"


def test_mcp_rename_project_records_applied_draft_without_matching_open_draft(
    tmp_path: Path,
) -> None:
    plot_root, _ = _project(tmp_path)
    proposed_id = str(
        _record(
            str(tmp_path),
            canvas_kind="project",
            proposed_text="프로젝트 이름: 다른 이름",
            chat_scope="foundation",
            proposed_kind=None,
        )["draft_id"]
    )

    renamed = mcp_tools.rename_project(str(tmp_path), "alpha", "새이름")

    assert renamed["name"] == "새이름"
    drafts = list_drafts(plot_root, "alpha")
    assert len(drafts) == 2
    assert read_draft(plot_root, "alpha", proposed_id).status == "proposed"
    applied = next(draft for draft in drafts if draft.id != proposed_id)
    assert applied.canvas_kind == "project"
    assert applied.status == "confirmed"
    assert applied.origin == "auto"


def test_mcp_rename_project_rejects_non_project_draft_before_write(tmp_path: Path) -> None:
    plot_root, _ = _project(tmp_path)
    draft_id = str(_record(str(tmp_path))["draft_id"])

    with pytest.raises(ValueError, match="project draft"):
        mcp_tools.rename_project(str(tmp_path), "alpha", "새이름", draft_id=draft_id)

    assert mcp_tools.get_project(str(tmp_path), "alpha")["name"] == "Alpha"
    assert [draft.id for draft in list_drafts(plot_root, "alpha")] == [draft_id]


def test_mcp_rename_project_raises_when_draft_recording_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plot_root, _ = _project(tmp_path)

    def fail_to_record(*_args: object, **_kwargs: object) -> None:
        raise OSError("draft storage unavailable")

    monkeypatch.setattr(mcp_project_tools, "persist_applied_draft", fail_to_record)

    with pytest.raises(OSError, match="draft storage unavailable"):
        mcp_tools.rename_project(str(tmp_path), "alpha", "Renamed Alpha")

    assert mcp_tools.get_project(str(tmp_path), "alpha")["name"] == "Alpha"
    assert list_drafts(plot_root, "alpha") == []


def test_mcp_rename_project_rolls_back_when_draft_confirmation_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plot_root, _ = _project(tmp_path)
    draft_id = str(
        _record(
            str(tmp_path),
            canvas_kind="project",
            proposed_text="프로젝트 이름: 새이름",
            chat_scope="foundation",
            proposed_kind=None,
        )["draft_id"]
    )

    def fail_to_confirm(*_args: object, **_kwargs: object) -> None:
        raise OSError("draft storage unavailable")

    monkeypatch.setattr(mcp_project_tools, "persist_resolution", fail_to_confirm)

    with pytest.raises(OSError, match="draft storage unavailable"):
        mcp_tools.rename_project(str(tmp_path), "alpha", "새이름", draft_id=draft_id)

    assert mcp_tools.get_project(str(tmp_path), "alpha")["name"] == "Alpha"
    assert read_draft(plot_root, "alpha", draft_id).status == "proposed"


def test_project_drafts_can_be_filtered_in_store_and_http(tmp_path: Path) -> None:
    plot_root, _ = _project(tmp_path)
    renamed = mcp_tools.rename_project(str(tmp_path), "alpha", "Renamed Alpha")
    assert renamed["name"] == "Renamed Alpha"
    other = _record(str(tmp_path))

    project_drafts = list_drafts(plot_root, "alpha", canvas_kind="project")
    assert len(project_drafts) == 1
    assert project_drafts[0].canvas_kind == "project"
    assert project_drafts[0].id != other["draft_id"]

    client = TestClient(create_http_app(hub=BroadcastHub(enable_watchers=False)))
    response = client.get(
        "/api/projects/alpha/drafts",
        params={"project_path": str(tmp_path), "canvas_kind": "project"},
    )

    assert response.status_code == 200
    assert [row["id"] for row in response.json()["drafts"]] == [project_drafts[0].id]


def test_http_rename_project_records_no_draft(tmp_path: Path) -> None:
    plot_root, _ = _project(tmp_path)
    client = TestClient(create_http_app(hub=BroadcastHub(enable_watchers=False)))

    response = client.patch(
        "/api/projects/alpha",
        params={"project_path": str(tmp_path)},
        json={"name": "Renamed Alpha"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Renamed Alpha"
    assert list_drafts(plot_root, "alpha") == []


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
    }
    assert record.parameters["properties"]["canvas_kind"] == {
        "anyOf": [
            {
                "enum": ["foundation", "actors", "services", "entities", "feature"],
                "type": "string",
            },
            {"const": "project", "type": "string"},
        ]
    }

    rename = asyncio.run(mcp_tools.mcp.get_tool("rename_project"))
    assert rename is not None
    assert set(rename.parameters["properties"]) == {
        "project_path",
        "project_id",
        "name",
        "draft_id",
    }
    assert set(rename.parameters["required"]) == {"project_path", "project_id", "name"}

    for tool_name in ("create_edge", "set_node_references", "update_canvas"):
        tool = asyncio.run(mcp_tools.mcp.get_tool(tool_name))
        assert tool is not None
        assert {"draft_id", "chat_scope"} <= set(tool.parameters["properties"])
        assert "draft_id" not in tool.parameters["required"]
        assert "chat_scope" not in tool.parameters["required"]

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
