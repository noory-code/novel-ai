"""Post-turn proposal extraction and open-draft context."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, get_args

import pytest

from mashbill import draft_extraction, endpoints_chat
from mashbill.broadcast import BroadcastHub
from mashbill.chat_providers.base import ChatProvider, ChatStreamEvent
from mashbill.chat_selection import OPEN_DRAFTS_CAP, build_turn_preamble
from mashbill.chat_store import append_user, read_conversation
from mashbill.draft_extraction import (
    DRAFT_EXTRACTION_KNOWN_CAP,
    extract_turn_drafts,
)
from mashbill.draft_store import (
    list_drafts,
    record_applied_draft,
    record_draft,
    resolve_draft,
)
from mashbill.endpoints_chat import stream_chat_turn
from mashbill.folder_io import create_node, sync_details_with_overview
from mashbill.models_canvas import CanvasKind
from mashbill.models_kinds import NodeKind
from mashbill.project_io import create_project
from mashbill.workspace import resolve_plot_root


class _FakeHub(BroadcastHub):
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []
        self.notifications: list[tuple[str, dict[str, Any] | None]] = []

    async def notify_event(
        self,
        plot_root: Path,
        event_name: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        self.notifications.append((event_name, payload))
        if payload is not None:
            self.events.append(payload)


class _ExtractingProvider(ChatProvider):
    def __init__(
        self,
        extraction_result: str = "[]",
        *,
        on_turn: Callable[[], None] | None = None,
        extraction_error: Exception | None = None,
    ) -> None:
        self.extraction_result = extraction_result
        self.on_turn = on_turn
        self.extraction_error = extraction_error
        self.extraction_calls: list[tuple[str, str | None]] = []
        self.extraction_called = asyncio.Event()

    async def stream_turn(self, user_message: str) -> Any:
        if self.on_turn is not None:
            self.on_turn()
        yield ChatStreamEvent(type="turn_complete", turn_id="turn_1", text="Mission idea")

    async def complete_once(self, prompt: str, *, model: str | None = None) -> str:
        self.extraction_calls.append((prompt, model))
        self.extraction_called.set()
        if self.extraction_error is not None:
            raise self.extraction_error
        return self.extraction_result


def _project(tmp_path: Path) -> Path:
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    return plot_root


async def _wait_for_drafts(plot_root: Path, count: int) -> None:
    async with asyncio.timeout(1):
        while len(list_drafts(plot_root, "alpha")) < count:
            await asyncio.sleep(0)


async def _wait_for_extraction_tasks() -> None:
    async with asyncio.timeout(1):
        while endpoints_chat._draft_extraction_tasks:
            await asyncio.sleep(0)


def _prompt_input(provider: _ExtractingProvider) -> dict[str, Any]:
    prompt, _model = provider.extraction_calls[0]
    return json.loads(prompt.rsplit("\nInput:\n", 1)[1])


def _create_primary_canvas_nodes(plot_root: Path) -> dict[str, str]:
    cases: dict[CanvasKind, str] = {
        "foundation": "core_value",
        "actors": "actor",
        "services": "service",
        "entities": "entity",
    }
    return {
        canvas_kind: str(
            create_node(
                plot_root,
                "alpha",
                canvas_kind,
                node_kind,
                {"label": f"{canvas_kind.title()} node"},
            )["node"]["id"]
        )
        for canvas_kind, node_kind in cases.items()
    }


def _create_feature_canvas_node(plot_root: Path) -> tuple[str, str]:
    feature = create_node(
        plot_root,
        "alpha",
        "services",
        "feature",
        {"label": "Review submission"},
    )
    feature_id = str(feature["node"]["id"])
    sync_details_with_overview(plot_root, "alpha")
    step = create_node(
        plot_root,
        "alpha",
        "feature",
        "step",
        {"label": "Check required fields"},
        service_id=feature_id,
    )
    return feature_id, str(step["node"]["id"])


def _create_empty_feature_canvas(plot_root: Path, label: str) -> str:
    feature = create_node(
        plot_root,
        "alpha",
        "services",
        "feature",
        {"label": label},
    )
    feature_id = str(feature["node"]["id"])
    sync_details_with_overview(plot_root, "alpha")
    return feature_id


async def test_project_scope_extracts_with_all_primary_canvas_nodes(tmp_path: Path) -> None:
    plot_root = _project(tmp_path)
    node_ids = _create_primary_canvas_nodes(plot_root)
    provider = _ExtractingProvider()

    count = await extract_turn_drafts(
        provider,
        plot_root,
        "alpha",
        "project",
        "A project-wide proposal.",
        datetime.now(UTC).isoformat(),
    )

    assert count == 0
    assert len(provider.extraction_calls) == 1
    prompt, _model = provider.extraction_calls[0]
    assert "- canvas_kind: one of foundation, actors, services, entities" in prompt
    assert _prompt_input(provider)["canvas_nodes"] == [
        {
            "id": node_ids[canvas_kind],
            "name": f"{canvas_kind.title()} node",
            "canvas": canvas_kind,
        }
        for canvas_kind in ("foundation", "actors", "services", "entities")
    ]


async def test_project_scope_includes_feature_canvas_nodes_after_primary_nodes(
    tmp_path: Path,
) -> None:
    plot_root = _project(tmp_path)
    _create_primary_canvas_nodes(plot_root)
    feature_id, step_id = _create_feature_canvas_node(plot_root)
    provider = _ExtractingProvider()

    count = await extract_turn_drafts(
        provider,
        plot_root,
        "alpha",
        "project",
        "A feature-flow proposal.",
        datetime.now(UTC).isoformat(),
    )

    assert count == 0
    prompt, _model = provider.extraction_calls[0]
    assert "canvas_kind: feature" in prompt
    assert "feature_id" in prompt
    canvas_nodes = _prompt_input(provider)["canvas_nodes"]
    first_feature_index = next(
        index for index, node in enumerate(canvas_nodes) if node["canvas"] == "feature"
    )
    assert all(node["canvas"] != "feature" for node in canvas_nodes[:first_feature_index])
    assert canvas_nodes[first_feature_index:] == [
        {
            "id": feature_id,
            "name": "Review submission",
            "canvas": "feature",
            "feature_id": feature_id,
        },
        {
            "id": step_id,
            "name": "Check required fields",
            "canvas": "feature",
            "feature_id": feature_id,
        },
    ]


async def test_project_scope_lists_empty_feature_canvas_in_features(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plot_root = _project(tmp_path)
    feature_id = _create_empty_feature_canvas(plot_root, "Review submission")
    original_canvas_nodes = draft_extraction._canvas_nodes

    def canvas_nodes_without_feature_flow(
        plot_root: Path,
        project_id: str,
        canvas_kind: CanvasKind,
        service_id: str | None,
    ) -> list[dict[str, str]]:
        if canvas_kind == "feature":
            return []
        return original_canvas_nodes(plot_root, project_id, canvas_kind, service_id)

    monkeypatch.setattr(draft_extraction, "_canvas_nodes", canvas_nodes_without_feature_flow)
    provider = _ExtractingProvider()

    await extract_turn_drafts(
        provider,
        plot_root,
        "alpha",
        "project",
        "Propose the first flow step.",
        datetime.now(UTC).isoformat(),
    )

    prompt_input = _prompt_input(provider)
    assert prompt_input["features"] == [{"feature_id": feature_id, "name": "Review submission"}]
    assert all(node.get("feature_id") != feature_id for node in prompt_input["canvas_nodes"])


async def test_project_scope_persists_draft_for_empty_feature_canvas(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plot_root = _project(tmp_path)
    feature_id = _create_empty_feature_canvas(plot_root, "Review submission")
    original_canvas_nodes = draft_extraction._canvas_nodes

    def canvas_nodes_without_feature_flow(
        plot_root: Path,
        project_id: str,
        canvas_kind: CanvasKind,
        service_id: str | None,
    ) -> list[dict[str, str]]:
        if canvas_kind == "feature":
            return []
        return original_canvas_nodes(plot_root, project_id, canvas_kind, service_id)

    monkeypatch.setattr(draft_extraction, "_canvas_nodes", canvas_nodes_without_feature_flow)
    provider = _ExtractingProvider(
        json.dumps(
            [
                {
                    "proposed_text": "Start by validating required fields.",
                    "canvas_kind": "feature",
                    "feature_id": feature_id,
                    "target_node_ids": [feature_id, "unknown"],
                    "rationale": "It is a concrete first flow step.",
                }
            ]
        )
    )

    count = await extract_turn_drafts(
        provider,
        plot_root,
        "alpha",
        "project",
        "Propose the first flow step.",
        datetime.now(UTC).isoformat(),
    )

    assert count == 1
    draft = list_drafts(plot_root, "alpha")[0]
    assert draft.canvas_kind == "feature"
    assert draft.service_id == feature_id
    assert draft.target_node_ids == []


async def test_project_scope_persists_selected_canvas_and_filters_target_ids(
    tmp_path: Path,
) -> None:
    plot_root = _project(tmp_path)
    node_ids = _create_primary_canvas_nodes(plot_root)
    provider = _ExtractingProvider(
        json.dumps(
            [
                {
                    "proposed_text": "Clarify the primary actor.",
                    "canvas_kind": "actors",
                    "target_node_ids": [node_ids["actors"], node_ids["foundation"]],
                    "rationale": "It is concrete actor copy.",
                }
            ]
        )
    )

    count = await extract_turn_drafts(
        provider,
        plot_root,
        "alpha",
        "project",
        "Clarify the primary actor.",
        datetime.now(UTC).isoformat(),
    )

    assert count == 1
    draft = list_drafts(plot_root, "alpha")[0]
    assert draft.origin == "extracted"
    assert draft.canvas_kind == "actors"
    assert draft.chat_scope == "project"
    assert draft.service_id is None
    assert draft.target_node_ids == [node_ids["actors"]]


async def test_project_scope_persists_feature_draft_and_filters_target_ids(
    tmp_path: Path,
) -> None:
    plot_root = _project(tmp_path)
    node_ids = _create_primary_canvas_nodes(plot_root)
    feature_id, step_id = _create_feature_canvas_node(plot_root)
    provider = _ExtractingProvider(
        json.dumps(
            [
                {
                    "proposed_text": "Reject submissions with missing fields.",
                    "canvas_kind": "feature",
                    "feature_id": feature_id,
                    "target_node_ids": [step_id, node_ids["foundation"], "unknown"],
                    "rationale": "It is a concrete flow decision.",
                }
            ]
        )
    )

    count = await extract_turn_drafts(
        provider,
        plot_root,
        "alpha",
        "project",
        "Reject submissions with missing fields.",
        datetime.now(UTC).isoformat(),
    )

    assert count == 1
    draft = list_drafts(plot_root, "alpha")[0]
    assert draft.origin == "extracted"
    assert draft.canvas_kind == "feature"
    assert draft.service_id == feature_id
    assert draft.chat_scope == "project"
    assert draft.target_node_ids == [step_id]


@pytest.mark.parametrize("feature_fields", [{}, {"feature_id": "unknown"}])
async def test_project_scope_skips_feature_proposals_without_known_feature_id(
    tmp_path: Path,
    feature_fields: dict[str, str],
) -> None:
    plot_root = _project(tmp_path)
    _create_primary_canvas_nodes(plot_root)
    _create_feature_canvas_node(plot_root)
    provider = _ExtractingProvider(
        json.dumps(
            [
                {
                    "proposed_text": "Do not persist this feature proposal.",
                    "canvas_kind": "feature",
                    "rationale": "It lacks a known feature id.",
                    **feature_fields,
                }
            ]
        )
    )

    count = await extract_turn_drafts(
        provider,
        plot_root,
        "alpha",
        "project",
        "A feature proposal.",
        datetime.now(UTC).isoformat(),
    )

    assert count == 0
    assert list_drafts(plot_root, "alpha") == []


@pytest.mark.parametrize("invalid_item", [{}, {"canvas_kind": "feature"}])
async def test_project_scope_skips_proposals_without_primary_canvas_kind(
    tmp_path: Path,
    invalid_item: dict[str, str],
) -> None:
    plot_root = _project(tmp_path)
    node_ids = _create_primary_canvas_nodes(plot_root)
    provider = _ExtractingProvider(
        json.dumps(
            [
                {
                    "proposed_text": "Do not persist this.",
                    "rationale": "It lacks a valid project canvas.",
                    **invalid_item,
                },
                {
                    "proposed_text": "Persist this actor proposal.",
                    "canvas_kind": "actors",
                    "target_node_ids": [node_ids["actors"]],
                    "rationale": "It has a valid project canvas.",
                },
            ]
        )
    )

    count = await extract_turn_drafts(
        provider,
        plot_root,
        "alpha",
        "project",
        "Two proposals.",
        datetime.now(UTC).isoformat(),
    )

    assert count == 1
    assert [draft.proposed_text for draft in list_drafts(plot_root, "alpha")] == [
        "Persist this actor proposal."
    ]


async def test_project_scope_caps_combined_canvas_nodes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plot_root = _project(tmp_path)
    _create_primary_canvas_nodes(plot_root)
    assert draft_extraction.DRAFT_EXTRACTION_PROJECT_NODE_CAP == 400
    monkeypatch.setattr(draft_extraction, "DRAFT_EXTRACTION_PROJECT_NODE_CAP", 3)
    provider = _ExtractingProvider()

    await extract_turn_drafts(
        provider,
        plot_root,
        "alpha",
        "project",
        "A project-wide proposal.",
        datetime.now(UTC).isoformat(),
    )

    assert len(_prompt_input(provider)["canvas_nodes"]) == 3


async def test_project_scope_persists_feature_draft_when_its_nodes_are_capped(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plot_root = _project(tmp_path)
    _create_primary_canvas_nodes(plot_root)
    _create_empty_feature_canvas(plot_root, "First feature")
    capped_feature_id = _create_empty_feature_canvas(plot_root, "Capped feature")
    monkeypatch.setattr(draft_extraction, "DRAFT_EXTRACTION_PROJECT_NODE_CAP", 3)
    provider = _ExtractingProvider(
        json.dumps(
            [
                {
                    "proposed_text": "Start the capped feature flow.",
                    "canvas_kind": "feature",
                    "feature_id": capped_feature_id,
                    "target_node_ids": [capped_feature_id],
                    "rationale": "It is a concrete flow step.",
                }
            ]
        )
    )

    count = await extract_turn_drafts(
        provider,
        plot_root,
        "alpha",
        "project",
        "Propose a flow step.",
        datetime.now(UTC).isoformat(),
    )

    assert count == 1
    assert len(_prompt_input(provider)["canvas_nodes"]) == 3
    assert {feature["feature_id"] for feature in _prompt_input(provider)["features"]} >= {
        capped_feature_id
    }
    draft = list_drafts(plot_root, "alpha")[0]
    assert draft.canvas_kind == "feature"
    assert draft.service_id == capped_feature_id
    assert draft.target_node_ids == []


async def test_single_canvas_scope_does_not_include_features_input(tmp_path: Path) -> None:
    plot_root = _project(tmp_path)
    provider = _ExtractingProvider()

    await extract_turn_drafts(
        provider,
        plot_root,
        "alpha",
        "foundation",
        "A foundation proposal.",
        datetime.now(UTC).isoformat(),
    )

    assert "features" not in _prompt_input(provider)


async def test_project_scope_omits_only_an_unreadable_canvas(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plot_root = _project(tmp_path)
    _create_primary_canvas_nodes(plot_root)
    original_read_canvas = draft_extraction.read_canvas
    requested_canvases: list[CanvasKind] = []

    def read_canvas_with_failure(
        plot_root: Path,
        project_id: str,
        canvas_kind: CanvasKind,
        service_id: str | None = None,
    ) -> Any:
        requested_canvases.append(canvas_kind)
        if canvas_kind == "services":
            raise OSError("services canvas is unreadable")
        return original_read_canvas(plot_root, project_id, canvas_kind, service_id)

    monkeypatch.setattr(draft_extraction, "read_canvas", read_canvas_with_failure)
    provider = _ExtractingProvider()

    await extract_turn_drafts(
        provider,
        plot_root,
        "alpha",
        "project",
        "A project-wide proposal.",
        datetime.now(UTC).isoformat(),
    )

    assert {node["canvas"] for node in _prompt_input(provider)["canvas_nodes"]} == {
        "foundation",
        "actors",
        "entities",
    }
    assert requested_canvases == ["foundation", "actors", "services", "entities"]


async def test_turn_complete_extracts_unrecorded_proposal_in_background(tmp_path: Path) -> None:
    plot_root = _project(tmp_path)
    created = create_node(
        plot_root,
        "alpha",
        "foundation",
        "core_value",
        {"label": "Clarity"},
    )
    node_id = str(created["node"]["id"])
    provider = _ExtractingProvider(
        '[{"proposed_text":"Make the next step visible.",'
        '"proposed_kind":"core_value","target_node_ids":["'
        + node_id
        + '"],"rationale":"It is concrete canvas copy."}]'
    )
    hub = _FakeHub()

    await stream_chat_turn(
        provider,
        hub,
        plot_root,
        "hello",
        scope="foundation",
        project_id="alpha",
        provider_name="codex",
        model="gpt-test:high",
    )

    await asyncio.wait_for(provider.extraction_called.wait(), timeout=1)
    await _wait_for_drafts(plot_root, 1)
    draft = list_drafts(plot_root, "alpha")[0]
    assert draft.origin == "extracted"
    assert draft.status == "proposed"
    assert draft.chat_scope == "foundation"
    assert draft.proposed_text == "Make the next step visible."
    assert draft.target_node_ids == [node_id]
    prompt, model = provider.extraction_calls[0]
    assert "Mission idea" in prompt
    assert node_id in prompt
    assert "Clarity" in prompt
    assert model == "gpt-test:high"


async def test_slow_extraction_does_not_delay_stream_or_conversation_save(tmp_path: Path) -> None:
    plot_root = _project(tmp_path)
    append_user(plot_root, "alpha", "foundation", "codex", "user_1", "hello")
    release = asyncio.Event()

    class _SlowProvider(_ExtractingProvider):
        async def complete_once(self, prompt: str, *, model: str | None = None) -> str:
            self.extraction_calls.append((prompt, model))
            self.extraction_called.set()
            await release.wait()
            return "[]"

    provider = _SlowProvider()
    hub = _FakeHub()

    await asyncio.wait_for(
        stream_chat_turn(
            provider,
            hub,
            plot_root,
            "hello",
            scope="foundation",
            project_id="alpha",
            provider_name="codex",
        ),
        timeout=0.1,
    )

    await asyncio.wait_for(provider.extraction_called.wait(), timeout=0.1)
    assert hub.events[-1]["type"] == "turn_complete"
    assert read_conversation(plot_root, "alpha", "foundation").messages[-1].text == "Mission idea"
    release.set()
    await asyncio.sleep(0)


async def test_turn_drafts_are_passed_to_extractor_for_deduplication(tmp_path: Path) -> None:
    plot_root = _project(tmp_path)

    def record_during_turn() -> None:
        record_draft(
            plot_root,
            "alpha",
            "foundation",
            "Already recorded proposal.",
            "The coach showed exact text.",
            "foundation",
        )
        record_applied_draft(
            plot_root,
            "alpha",
            "foundation",
            "Auto-recorded proposal.",
            "A write landed during this turn.",
            "foundation",
            [],
            "mission",
        )

    provider = _ExtractingProvider(
        '[{"proposed_text":"Already recorded proposal.",'
        '"rationale":"Duplicate returned by the fake."}]',
        on_turn=record_during_turn,
    )

    await stream_chat_turn(
        provider,
        _FakeHub(),
        plot_root,
        "hello",
        scope="foundation",
        project_id="alpha",
        provider_name="claude-code",
    )

    await asyncio.wait_for(provider.extraction_called.wait(), timeout=1)
    prompt, _model = provider.extraction_calls[0]
    assert "Already recorded proposal." in prompt
    assert "Auto-recorded proposal." in prompt
    assert {draft.proposed_text for draft in list_drafts(plot_root, "alpha")} == {
        "Already recorded proposal.",
        "Auto-recorded proposal.",
    }


async def test_extractor_receives_recent_scope_drafts_with_status_and_cap(tmp_path: Path) -> None:
    plot_root = _project(tmp_path)
    for number in range(DRAFT_EXTRACTION_KNOWN_CAP + 1):
        record_draft(
            plot_root,
            "alpha",
            "foundation",
            f"Older proposal {number}.",
            "Prior coach proposal.",
            "foundation",
        )
    prior = record_draft(
        plot_root,
        "alpha",
        "foundation",
        "Prior proposed draft.",
        "Prior coach proposal.",
        "foundation",
    )
    rejected = record_draft(
        plot_root,
        "alpha",
        "foundation",
        "Rejected draft.",
        "The user discarded it.",
        "foundation",
    )
    resolve_draft(plot_root, "alpha", rejected.id, "rejected")
    record_draft(
        plot_root,
        "alpha",
        "actors",
        "Other scope draft.",
        "It belongs to another scope.",
        "actors",
    )
    expected = [
        {"text": draft.proposed_text, "status": draft.status}
        for draft in list_drafts(plot_root, "alpha")
        if draft.chat_scope == "foundation"
    ][:DRAFT_EXTRACTION_KNOWN_CAP]
    provider = _ExtractingProvider()

    count = await extract_turn_drafts(
        provider,
        plot_root,
        "alpha",
        "foundation",
        "No new proposal.",
        datetime.now(UTC).isoformat(),
    )

    existing = _prompt_input(provider)["existing_drafts"]
    assert count == 0
    assert existing == expected
    assert len(existing) == DRAFT_EXTRACTION_KNOWN_CAP
    assert {"text": prior.proposed_text, "status": "proposed"} in existing
    assert {"text": rejected.proposed_text, "status": "rejected"} in existing
    assert all(item["text"] != "Other scope draft." for item in existing)


async def test_extractor_does_not_revive_rejected_duplicate(tmp_path: Path) -> None:
    plot_root = _project(tmp_path)
    rejected = record_draft(
        plot_root,
        "alpha",
        "foundation",
        "Discard this proposal.",
        "The user discarded it.",
        "foundation",
    )
    resolve_draft(plot_root, "alpha", rejected.id, "rejected")
    provider = _ExtractingProvider(
        '[{"proposed_text":"Discard this proposal.",'
        '"rationale":"Duplicate returned by the fake."}]'
    )

    count = await extract_turn_drafts(
        provider,
        plot_root,
        "alpha",
        "foundation",
        "Use a different direction instead.",
        datetime.now(UTC).isoformat(),
    )

    assert count == 0
    assert [draft.id for draft in list_drafts(plot_root, "alpha")] == [rejected.id]


@pytest.mark.parametrize(
    ("result", "error", "expected_events"),
    [
        (
            '[{"proposed_text":"A new mission.",'
            '"rationale":"It is concrete canvas copy."}]',
            None,
            1,
        ),
        ("[]", None, 0),
        ("", RuntimeError("extractor failed"), 0),
    ],
)
async def test_extracted_drafts_notify_viewer_only_when_persisted(
    tmp_path: Path,
    result: str,
    error: Exception | None,
    expected_events: int,
) -> None:
    plot_root = _project(tmp_path)
    hub = _FakeHub()
    provider = _ExtractingProvider(result, extraction_error=error)

    await stream_chat_turn(
        provider,
        hub,
        plot_root,
        "hello",
        scope="foundation",
        project_id="alpha",
        provider_name="codex",
    )
    await _wait_for_extraction_tasks()

    draft_events = [
        payload for event_name, payload in hub.notifications if event_name == "drafts_changed"
    ]
    assert len(draft_events) == expected_events
    if expected_events:
        assert draft_events == [{"project_id": "alpha", "scope": "foundation"}]


@pytest.mark.parametrize(
    ("proposed_kind", "expected_kind"),
    [("label", None), (get_args(NodeKind)[1], get_args(NodeKind)[1])],
)
async def test_extractor_keeps_only_real_node_kinds(
    tmp_path: Path,
    proposed_kind: str,
    expected_kind: str | None,
) -> None:
    plot_root = _project(tmp_path)
    provider = _ExtractingProvider(
        json.dumps(
            [
                {
                    "proposed_text": f"Proposal for {proposed_kind}.",
                    "proposed_kind": proposed_kind,
                    "rationale": "It is a concrete proposal.",
                }
            ]
        )
    )

    count = await extract_turn_drafts(
        provider,
        plot_root,
        "alpha",
        "foundation",
        "A concrete proposal.",
        datetime.now(UTC).isoformat(),
    )

    assert count == 1
    assert list_drafts(plot_root, "alpha")[0].proposed_kind == expected_kind


@pytest.mark.parametrize(
    ("result", "error"),
    [
        ("not JSON", None),
        ("", RuntimeError("extractor failed")),
    ],
)
async def test_extraction_failure_does_not_affect_stream_or_conversation(
    tmp_path: Path,
    result: str,
    error: Exception | None,
) -> None:
    plot_root = _project(tmp_path)
    append_user(plot_root, "alpha", "foundation", "codex", "user_1", "hello")
    hub = _FakeHub()
    provider = _ExtractingProvider(result, extraction_error=error)

    await stream_chat_turn(
        provider,
        hub,
        plot_root,
        "hello",
        scope="foundation",
        project_id="alpha",
        provider_name="codex",
    )

    assert hub.events[-1]["type"] == "turn_complete"
    assert read_conversation(plot_root, "alpha", "foundation").messages[-1].text == "Mission idea"
    await asyncio.wait_for(provider.extraction_called.wait(), timeout=1)
    await asyncio.sleep(0)
    assert list_drafts(plot_root, "alpha") == []


def test_turn_preamble_lists_only_recent_open_drafts_for_scope(tmp_path: Path) -> None:
    plot_root = _project(tmp_path)
    open_drafts = [
        record_draft(
            plot_root,
            "alpha",
            "foundation",
            f"Open proposal {number} " + "x" * 200,
            "Concrete proposal.",
            "foundation",
        )
        for number in range(OPEN_DRAFTS_CAP + 2)
    ]
    closed = record_draft(
        plot_root,
        "alpha",
        "foundation",
        "Closed proposal",
        "Already decided.",
        "foundation",
    )
    resolve_draft(plot_root, "alpha", closed.id, "rejected")
    other_scope = record_draft(
        plot_root,
        "alpha",
        "actors",
        "Other scope proposal",
        "Belongs elsewhere.",
        "actors",
    )

    preamble = build_turn_preamble(plot_root, "foundation", [])
    block = preamble.split("[Open drafts]", 1)[1]

    assert "Closed proposal" not in block
    assert other_scope.id not in block
    assert all(draft.id in block for draft in open_drafts[-OPEN_DRAFTS_CAP:])
    assert all(draft.id not in block for draft in open_drafts[:-OPEN_DRAFTS_CAP])
    assert "x" * 200 not in block


def test_turn_preamble_omits_open_drafts_block_when_none_exist(tmp_path: Path) -> None:
    plot_root = _project(tmp_path)
    assert "[Open drafts]" not in build_turn_preamble(plot_root, "foundation", [])
