"""The app tells the person what the coach added to a canvas they are not on.

While talking on one canvas the in-app coach can create nodes on another (ten
entities while the person is on Services). The engine compares each canvas's
node ids before and after the turn and attaches the additions outside the
conversation's own canvas to the turn's terminal event and to the saved
message, so the app can show them under the reply and after a reload
(D-2026-10-15-A, user decision 2026-10-14). Additions to the conversation's own
canvas are not reported: the person sees them appear, and announcing saves is
the coach's banned habit (D-2026-07-15-A), not something the app repeats.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from mashbill import mcp_tools
from mashbill.broadcast import BroadcastHub
from mashbill.chat_providers.base import ChatProvider, ChatStreamEvent
from mashbill.chat_store import (
    ChatConversationDoc,
    ChatMessageRecord,
    append_user,
    read_conversation,
    read_recent_transcript,
)
from mashbill.endpoints_chat import stream_chat_turn
from mashbill.folder_io import create_project, write_canvas
from mashbill.models import CanvasDoc, FeatureNode, ServiceNode
from mashbill.storage import _project_dir
from mashbill.workspace import resolve_plot_root

_ENTITY_LABELS = [f"엔티티{i}" for i in range(10)]


class _Hub(BroadcastHub):
    def __init__(self) -> None:
        self.payloads: list[dict[str, Any]] = []

    async def notify_event(
        self, plot_root: Path, event_name: str, payload: dict[str, Any] | None = None
    ) -> None:
        if payload is not None and event_name == "chat_stream_event":
            self.payloads.append(payload)


class _Coach(ChatProvider):
    """Runs ``act`` mid-turn, the way the coach's MCP calls write files, then ends."""

    def __init__(self, act: Callable[[], None], *, fail: bool = False) -> None:
        self._act = act
        self._fail = fail

    async def stream_turn(self, user_message: str) -> Any:
        yield ChatStreamEvent(type="turn_start", turn_id="t1")
        self._act()
        yield ChatStreamEvent(type="delta", turn_id="t1", text="정리했어요.")
        if self._fail:
            yield ChatStreamEvent(type="error", turn_id="t1", error_message="codex exited 1")
        else:
            yield ChatStreamEvent(type="turn_complete", turn_id="t1", text="정리했어요.")


def _project(tmp_path: Path) -> tuple[Path, str]:
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    write_canvas(
        plot_root,
        "alpha",
        CanvasDoc(
            canvas_id="services",
            canvas_kind="services",
            nodes=[
                ServiceNode(id="svc_laundry", label="세탁"),
                FeatureNode(id="feature_x", label="주문하기"),
            ],
        ),
    )
    write_canvas(
        plot_root,
        "alpha",
        CanvasDoc(
            canvas_id="feature_x",
            canvas_kind="feature",
            feature_ref="feature_x",
            nodes=[FeatureNode(id="feature_x", label="주문하기")],
        ),
    )
    return plot_root, str(tmp_path)


def _create(project_path: str, canvas_kind: str, kind: str, label: str, **kw: Any) -> None:
    mcp_tools.create_node(project_path, "alpha", canvas_kind, kind, {"label": label}, **kw)  # type: ignore[arg-type]


def _ten_entities(project_path: str) -> Callable[[], None]:
    def act() -> None:
        for label in _ENTITY_LABELS:
            _create(project_path, "entities", "entity", label)

    return act


async def _turn(
    plot_root: Path, scope: str, act: Callable[[], None], *, fail: bool = False
) -> _Hub:
    append_user(plot_root, "alpha", scope, "codex", "u1", "정리해 주세요")
    hub = _Hub()
    await stream_chat_turn(
        _Coach(act, fail=fail),
        hub,
        plot_root,
        "정리해 주세요",
        scope=scope,
        project_id="alpha",
        provider_name="codex",
        conversation_id=read_conversation(plot_root, "alpha", scope).conversation_id,
    )
    return hub


def _terminal(hub: _Hub) -> dict[str, Any]:
    return next(p for p in hub.payloads if p["type"] in ("turn_complete", "error"))


_TEN_ENTITIES = [
    {"canvas": "entities", "count": 10, "labels": _ENTITY_LABELS[:3]},
]


async def test_entities_made_from_the_services_canvas_are_reported_and_saved(
    tmp_path: Path,
) -> None:
    plot_root, project_path = _project(tmp_path)

    hub = await _turn(plot_root, "services", _ten_entities(project_path))

    assert _terminal(hub)["added_elsewhere"] == _TEN_ENTITIES
    saved = read_conversation(plot_root, "alpha", "services").messages[-1]
    assert saved.model_dump()["added_elsewhere"] == _TEN_ENTITIES
    # The notice is the app's, not the coach's prose: the reply text is untouched
    # and it never reaches the transcript re-fed to a fresh coach session.
    assert saved.text == "정리했어요."
    assert "엔티티0" not in read_recent_transcript(plot_root, "alpha", "services")


async def test_nodes_added_to_the_turns_own_canvas_are_not_reported(
    tmp_path: Path,
) -> None:
    plot_root, project_path = _project(tmp_path)

    hub = await _turn(plot_root, "entities", _ten_entities(project_path))

    assert all("added_elsewhere" not in p for p in hub.payloads)
    raw = json.loads(
        (_project_dir(plot_root, "alpha") / "chat" / "project.json").read_text("utf-8")
    )
    assert "added_elsewhere" not in raw["messages"][-1]


async def test_a_service_thread_counts_the_services_canvas_as_its_own(tmp_path: Path) -> None:
    plot_root, project_path = _project(tmp_path)

    def act() -> None:
        _create(project_path, "services", "service", "배송")
        _create(project_path, "entities", "entity", "세탁 주문")

    hub = await _turn(plot_root, "service:svc_laundry", act)

    assert _terminal(hub)["added_elsewhere"] == [
        {"canvas": "entities", "count": 1, "labels": ["세탁 주문"]}
    ]


async def test_a_feature_thread_reports_entities_but_not_its_own_flow(tmp_path: Path) -> None:
    plot_root, project_path = _project(tmp_path)

    def act() -> None:
        _create(project_path, "feature", "step", "주문을 넣는다", service_id="feature_x")
        _create(project_path, "entities", "entity", "세탁 주문")

    hub = await _turn(plot_root, "feature:feature_x", act)

    assert _terminal(hub)["added_elsewhere"] == [
        {"canvas": "entities", "count": 1, "labels": ["세탁 주문"]}
    ]


async def test_another_features_flow_is_reported_with_that_features_name(
    tmp_path: Path,
) -> None:
    plot_root, project_path = _project(tmp_path)

    def act() -> None:
        _create(project_path, "feature", "step", "주문을 넣는다", service_id="feature_x")

    hub = await _turn(plot_root, "entities", act)

    assert _terminal(hub)["added_elsewhere"] == [
        {
            "canvas": "feature:feature_x",
            "count": 1,
            "labels": ["주문을 넣는다"],
            "canvas_label": "주문하기",
        }
    ]


async def test_the_seed_node_of_a_new_feature_canvas_is_not_reported(tmp_path: Path) -> None:
    """A new feature on Services seeds its flow canvas with a copy of the feature
    node (same id). That copy is the feature itself, not a second addition."""
    plot_root, project_path = _project(tmp_path)

    def act() -> None:
        _create(project_path, "services", "feature", "결제하기")

    hub = await _turn(plot_root, "services", act)

    seeded = [
        p
        for p in (_project_dir(plot_root, "alpha") / "services").glob("*/detail.json")
        if p.parent.name != "feature_x"
    ]
    assert len(seeded) == 1  # the scenario happened: a new flow canvas holds the seed
    assert "added_elsewhere" not in _terminal(hub)


async def test_the_project_thread_reports_every_canvas(tmp_path: Path) -> None:
    """The project thread belongs to no canvas, so nothing it adds is on its own canvas."""
    plot_root, project_path = _project(tmp_path)

    def act() -> None:
        _create(project_path, "actors", "actor", "고객")
        _create(project_path, "entities", "entity", "세탁 주문")

    hub = await _turn(plot_root, "project", act)

    assert _terminal(hub)["added_elsewhere"] == [
        {"canvas": "actors", "count": 1, "labels": ["고객"]},
        {"canvas": "entities", "count": 1, "labels": ["세탁 주문"]},
    ]


async def test_a_failed_turn_still_reports_what_it_wrote(tmp_path: Path) -> None:
    plot_root, project_path = _project(tmp_path)

    hub = await _turn(plot_root, "services", _ten_entities(project_path), fail=True)

    assert _terminal(hub)["type"] == "error"
    assert _terminal(hub)["added_elsewhere"] == _TEN_ENTITIES
    saved = read_conversation(plot_root, "alpha", "services").messages[-1]
    assert saved.error == "codex exited 1"
    assert saved.model_dump()["added_elsewhere"] == _TEN_ENTITIES


async def test_a_canvas_unreadable_before_the_turn_is_left_out(tmp_path: Path) -> None:
    """Without a before-picture every node would look new, so that canvas is skipped."""
    plot_root, project_path = _project(tmp_path)
    entities_file = _project_dir(plot_root, "alpha") / "entities" / "canvas.json"
    good = entities_file.read_text("utf-8")
    entities_file.write_text("{not json", "utf-8")

    def act() -> None:
        entities_file.write_text(good, "utf-8")
        _create(project_path, "entities", "entity", "세탁 주문")
        _create(project_path, "actors", "actor", "고객")

    hub = await _turn(plot_root, "services", act)

    assert _terminal(hub)["added_elsewhere"] == [
        {"canvas": "actors", "count": 1, "labels": ["고객"]}
    ]


async def test_a_turn_with_no_project_streams_without_the_field(tmp_path: Path) -> None:
    plot_root = resolve_plot_root(str(tmp_path))
    hub = _Hub()

    await stream_chat_turn(_Coach(lambda: None), hub, plot_root, "hi", scope="services")

    assert all("added_elsewhere" not in p for p in hub.payloads)


def test_a_saved_message_keeps_its_additions_through_a_round_trip() -> None:
    record = ChatMessageRecord.model_validate(
        {
            "id": "turn_t1",
            "role": "assistant",
            "text": "정리했어요.",
            "ts": "2026-10-15T00:00:00+00:00",
            "added_elsewhere": [
                {
                    "canvas": "feature:feature_x",
                    "count": 2,
                    "labels": ["주문을 넣는다", "결제한다"],
                    "canvas_label": "주문하기",
                }
            ],
        }
    )

    again = ChatMessageRecord.model_validate(json.loads(json.dumps(record.model_dump())))

    assert again == record


def test_a_chat_file_saved_before_the_field_still_reads() -> None:
    doc = ChatConversationDoc.model_validate(
        {
            "schema_version": 1,
            "scope": "services",
            "created": "2026-10-01T00:00:00+00:00",
            "updated": "2026-10-01T00:00:00+00:00",
            "messages": [{"id": "turn_t1", "role": "assistant", "text": "hi", "ts": "x"}],
        }
    )

    assert doc.messages[0].added_elsewhere is None
    assert "added_elsewhere" not in doc.model_dump()["messages"][0]
