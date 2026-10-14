"""The app shows the person the flow draft the engine holds, under the coach's reply.

The coach records a flow draft with propose_flow from its own MCP process. When a
feature-scope turn completes, the chat layer appends the rendering of a proposal
recorded during that turn, so the person confirms exactly what draw_proposed_flow
will draw (D-2026-10-11-B, user decision 2026-10-11).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from mashbill import mcp_tools
from mashbill.broadcast import BroadcastHub
from mashbill.chat_providers.base import ChatProvider, ChatStreamEvent
from mashbill.chat_store import append_user, read_conversation
from mashbill.endpoints_chat import stream_chat_turn
from mashbill.folder_io import create_project, write_canvas
from mashbill.mcp_registration import IN_APP_COACH_ENV
from mashbill.models import CanvasDoc, FeatureNode
from mashbill.workspace import resolve_plot_root

_SCOPE = "feature:feature_x"


class _Hub(BroadcastHub):
    def __init__(self) -> None:
        self.payloads: list[dict[str, Any]] = []

    async def notify_event(
        self, plot_root: Path, event_name: str, payload: dict[str, Any] | None = None
    ) -> None:
        if payload is not None:
            self.payloads.append(payload)


class _Coach(ChatProvider):
    """Records a flow proposal mid-turn (as the coach's MCP call would), then replies."""

    def __init__(self, project_path: str, propose: bool) -> None:
        self._project_path = project_path
        self._propose = propose

    async def stream_turn(self, user_message: str) -> Any:
        yield ChatStreamEvent(type="turn_start", turn_id="t1")
        if self._propose:
            _propose(self._project_path)
        yield ChatStreamEvent(type="delta", turn_id="t1", text="초안을 맡겼어요.\n")
        yield ChatStreamEvent(type="turn_complete", turn_id="t1", text="초안을 맡겼어요.\n")


def _project(tmp_path: Path) -> tuple[Path, str]:
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    write_canvas(
        plot_root,
        "alpha",
        CanvasDoc(
            canvas_id="services",
            canvas_kind="services",
            nodes=[FeatureNode(id="feature_x", label="흐름 그리기", proposed="흐름을 정한다.")],
        ),
    )
    write_canvas(
        plot_root,
        "alpha",
        CanvasDoc(
            canvas_id="feature_x",
            canvas_kind="feature",
            feature_ref="feature_x",
            nodes=[FeatureNode(id="feature_x", label="흐름 그리기")],
        ),
    )
    append_user(plot_root, "alpha", _SCOPE, "claude-code", "u1", "흐름을 제안해 주세요")
    return plot_root, str(tmp_path)


def _propose(project_path: str) -> dict[str, Any]:
    return mcp_tools.propose_flow(
        project_path,
        "alpha",
        "feature_x",
        nodes=[{"key": "settle", "kind": "step", "label": "흐름을 정한다", "covers": [1]}],
        edges=[{"source": "feature_x", "target": "settle"}],
        open_items=[{"at": "settle", "question": "그다음은 무엇인가요?"}],
    )


async def _turn(plot_root: Path, project_path: str, propose: bool, scope: str = _SCOPE) -> _Hub:
    hub = _Hub()
    conversation_id = read_conversation(plot_root, "alpha", _SCOPE).conversation_id
    await stream_chat_turn(
        _Coach(project_path, propose),
        hub,
        plot_root,
        "흐름을 제안해 주세요",
        scope=scope,
        project_id="alpha",
        provider_name="claude-code",
        conversation_id=conversation_id,
    )
    return hub


async def test_a_turn_that_records_a_proposal_shows_its_rendering(tmp_path: Path) -> None:
    plot_root, project_path = _project(tmp_path)

    hub = await _turn(plot_root, project_path, propose=True)

    saved = read_conversation(plot_root, "alpha", _SCOPE).messages[-1].text
    assert saved.startswith("초안을 맡겼어요.\n")
    assert "```\n" in saved and "[1] 흐름을 정한다" in saved and "… 그다음은 무엇인가요?" in saved
    # O-00000137: the block under the reply shows numbers, never the coach's own key.
    assert "settle" not in saved
    complete = next(p for p in hub.payloads if p.get("type") == "turn_complete")
    assert complete["text"] == saved
    streamed = "".join(p["text"] for p in hub.payloads if p.get("type") == "delta")
    assert streamed == saved


async def test_a_turn_without_a_new_proposal_shows_nothing_extra(tmp_path: Path) -> None:
    plot_root, project_path = _project(tmp_path)
    _propose(project_path)  # recorded before this turn

    await _turn(plot_root, project_path, propose=False)

    assert read_conversation(plot_root, "alpha", _SCOPE).messages[-1].text == "초안을 맡겼어요.\n"


async def test_a_drawn_proposal_is_not_shown_again(tmp_path: Path) -> None:
    plot_root, project_path = _project(tmp_path)

    class _DrawingCoach(_Coach):
        async def stream_turn(self, user_message: str) -> Any:
            yield ChatStreamEvent(type="turn_start", turn_id="t1")
            _propose(project_path)
            mcp_tools.draw_proposed_flow(project_path, "alpha", "feature_x")
            yield ChatStreamEvent(type="turn_complete", turn_id="t1", text="그렸어요.")

    hub = _Hub()
    await stream_chat_turn(
        _DrawingCoach(project_path, propose=False),
        hub,
        plot_root,
        "그려 주세요",
        scope=_SCOPE,
        project_id="alpha",
        provider_name="claude-code",
        conversation_id=read_conversation(plot_root, "alpha", _SCOPE).conversation_id,
    )

    assert read_conversation(plot_root, "alpha", _SCOPE).messages[-1].text == "그렸어요."


def test_the_in_app_coach_is_told_the_app_shows_the_draft(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, project_path = _project(tmp_path)

    monkeypatch.setenv(IN_APP_COACH_ENV, "1")
    in_app = _propose(project_path)["show"]
    monkeypatch.delenv(IN_APP_COACH_ENV)
    headless = _propose(project_path)["show"]

    assert "app shows" in in_app and "do not restate" in in_app
    assert "Show the person this draft" in headless


async def test_a_services_turn_that_proposes_a_set_shows_its_rendering(tmp_path: Path) -> None:
    plot_root, project_path = _project(tmp_path)
    append_user(plot_root, "alpha", "services", "codex", "u2", "구성을 정리해 주세요")

    class _ServicesCoach(ChatProvider):
        async def stream_turn(self, user_message: str) -> Any:
            yield ChatStreamEvent(type="turn_start", turn_id="t2")
            mcp_tools.propose_services(
                project_path, "alpha", services=[{"key": "pay", "label": "돈 보내기"}]
            )
            yield ChatStreamEvent(type="turn_complete", turn_id="t2", text="구성을 맡겼어요.")

    await stream_chat_turn(
        _ServicesCoach(),
        _Hub(),
        plot_root,
        "구성을 정리해 주세요",
        scope="services",
        project_id="alpha",
        provider_name="codex",
        conversation_id=read_conversation(plot_root, "alpha", "services").conversation_id,
    )

    saved = read_conversation(plot_root, "alpha", "services").messages[-1].text
    assert saved.startswith("구성을 맡겼어요.") and "[1] 돈 보내기" in saved and "```" in saved


class _KeyQuotingCoach(ChatProvider):
    """Writes its own draft key into the reply, as the walk's coach did (O-00000137)."""

    def __init__(self, project_path: str, draw: bool) -> None:
        self._project_path = project_path
        self._draw = draw

    async def stream_turn(self, user_message: str) -> Any:
        yield ChatStreamEvent(type="turn_start", turn_id="t1")
        _propose(self._project_path)
        if self._draw:
            mcp_tools.draw_proposed_flow(self._project_path, "alpha", "feature_x")
        reply = "[settle] 갈래를 봐 주세요. [1]과 [other]는 그대로예요."
        yield ChatStreamEvent(type="delta", turn_id="t1", text=reply)
        yield ChatStreamEvent(type="turn_complete", turn_id="t1", text=reply)


async def _quoting_turn(plot_root: Path, project_path: str, draw: bool) -> _Hub:
    hub = _Hub()
    await stream_chat_turn(
        _KeyQuotingCoach(project_path, draw),
        hub,
        plot_root,
        "흐름을 제안해 주세요",
        scope=_SCOPE,
        project_id="alpha",
        provider_name="codex",
        conversation_id=read_conversation(plot_root, "alpha", _SCOPE).conversation_id,
    )
    return hub


async def test_a_draft_key_the_coach_writes_reads_as_the_shown_number(tmp_path: Path) -> None:
    plot_root, project_path = _project(tmp_path)

    hub = await _quoting_turn(plot_root, project_path, draw=False)

    saved = read_conversation(plot_root, "alpha", _SCOPE).messages[-1].text
    assert saved.startswith("[1] 갈래를 봐 주세요. [1]과 [other]는 그대로예요.")
    assert "settle" not in saved
    streamed = "".join(p["text"] for p in hub.payloads if p.get("type") == "delta")
    assert streamed == saved


async def test_a_draft_key_of_a_drawn_draft_reads_as_its_step_name(tmp_path: Path) -> None:
    plot_root, project_path = _project(tmp_path)

    await _quoting_turn(plot_root, project_path, draw=True)

    saved = read_conversation(plot_root, "alpha", _SCOPE).messages[-1].text
    # No draft box is shown once drawn, so a number would point at nothing.
    assert saved == "'흐름을 정한다' 갈래를 봐 주세요. [1]과 [other]는 그대로예요."


async def test_a_draft_key_split_across_streamed_pieces_still_reads_as_the_number(
    tmp_path: Path,
) -> None:
    plot_root, project_path = _project(tmp_path)

    class _ChunkingCoach(ChatProvider):
        """Streams token pieces, as the Claude coach does; a key spans two pieces.

        The save-announcement filter upstream buffers the stream to sentence
        boundaries, so a key without a terminator reaches the renaming whole.
        """

        async def stream_turn(self, user_message: str) -> Any:
            yield ChatStreamEvent(type="turn_start", turn_id="t1")
            _propose(project_path)
            pieces = ["갈래 [set", "tle]를 봐 주세요. [", "끝"]
            for piece in pieces:
                yield ChatStreamEvent(type="delta", turn_id="t1", text=piece)
            yield ChatStreamEvent(type="turn_complete", turn_id="t1", text="".join(pieces))

    hub = _Hub()
    await stream_chat_turn(
        _ChunkingCoach(),
        hub,
        plot_root,
        "흐름을 제안해 주세요",
        scope=_SCOPE,
        project_id="alpha",
        provider_name="claude-code",
        conversation_id=read_conversation(plot_root, "alpha", _SCOPE).conversation_id,
    )

    deltas = [p["text"] for p in hub.payloads if p.get("type") == "delta"]
    assert not any("set" in piece for piece in deltas)
    saved = read_conversation(plot_root, "alpha", _SCOPE).messages[-1].text
    assert saved.startswith("갈래 [1]를 봐 주세요. [끝")
    assert "".join(deltas) == saved


async def test_a_draft_key_cut_at_its_own_period_still_reads_as_the_number(
    tmp_path: Path,
) -> None:
    # The sentence buffer upstream splits after a period, so a key such as
    # "choice.v2" reaches the renaming in two pieces; the open "[" is held back.
    from datetime import UTC, datetime

    from mashbill.chat_proposals import append_proposal

    plot_root, project_path = _project(tmp_path)
    mcp_tools.propose_flow(
        project_path,
        "alpha",
        "feature_x",
        nodes=[{"key": "choice.v2", "kind": "step", "label": "흐름을 정한다", "covers": [1]}],
        edges=[{"source": "feature_x", "target": "choice.v2"}],
        open_items=[{"at": "choice.v2", "question": "그다음은 무엇인가요?"}],
    )
    pieces = ["갈래 [choice.", "v2]를 봐 주세요.", " 끝 ["]

    async def events() -> Any:
        for piece in pieces:
            yield ChatStreamEvent(type="delta", turn_id="t1", text=piece)
        yield ChatStreamEvent(type="turn_complete", turn_id="t1", text="".join(pieces))

    out = [
        e async for e in append_proposal(events(), plot_root, "alpha", _SCOPE, datetime.now(UTC))
    ]

    deltas = [e.text for e in out if e.type == "delta"]
    assert not any("choice" in piece for piece in deltas)
    assert "".join(deltas) == "갈래 [1]를 봐 주세요. 끝 ["
    assert out[-1].type == "turn_complete" and out[-1].text == "갈래 [1]를 봐 주세요. 끝 ["


async def test_a_long_draft_key_cut_at_its_period_still_reads_as_the_number(
    tmp_path: Path,
) -> None:
    from datetime import UTC, datetime

    from mashbill.chat_proposals import append_proposal

    plot_root, project_path = _project(tmp_path)
    key = "branch" + "x" * 80 + ".v2"
    mcp_tools.propose_flow(
        project_path,
        "alpha",
        "feature_x",
        nodes=[{"key": key, "kind": "step", "label": "흐름을 정한다", "covers": [1]}],
        edges=[{"source": "feature_x", "target": key}],
        open_items=[{"at": key, "question": "그다음은 무엇인가요?"}],
    )
    pieces = ["갈래 [branch" + "x" * 80 + ".", "v2]를 봐 주세요."]

    async def events() -> Any:
        for piece in pieces:
            yield ChatStreamEvent(type="delta", turn_id="t1", text=piece)
        yield ChatStreamEvent(type="turn_complete", turn_id="t1", text="".join(pieces))

    out = [
        e async for e in append_proposal(events(), plot_root, "alpha", _SCOPE, datetime.now(UTC))
    ]

    deltas = [e.text for e in out if e.type == "delta"]
    assert not any("branch" in piece for piece in deltas)
    assert "".join(deltas) == "갈래 [1]를 봐 주세요."
