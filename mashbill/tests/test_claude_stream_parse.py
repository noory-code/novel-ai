"""Claude Code stream-json delta parsing — no double-counting (D-2026-06-21-B).

With ``--include-partial-messages`` the CLI emits text TWICE per block: as a
sequence of ``content_block_delta`` partials AND as a final full ``assistant``
recap message. Counting both doubles the text ("살펴볼게요.살펴볼게요."). The
parser must take the streaming text from the partials only and ignore the
recap — the accumulated turn text must equal the produced text exactly once.
"""

from __future__ import annotations

import json

from mashbill.chat_providers.claude_code import _parse_claude_line


def _partial(text: str) -> bytes:
    return json.dumps(
        {
            "type": "stream_event",
            "event": {"type": "content_block_delta", "delta": {"type": "text_delta", "text": text}},
        }
    ).encode()


def _assistant_full(text: str) -> bytes:
    return json.dumps(
        {"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}}
    ).encode()


def test_partials_then_full_assistant_recap_is_not_doubled() -> None:
    acc: list[str] = []
    _parse_claude_line("t1", _partial("Hello "), acc)
    _parse_claude_line("t1", _partial("world"), acc)
    # the recap message carries the same complete block text — must be ignored
    _parse_claude_line("t1", _assistant_full("Hello world"), acc)
    assert "".join(acc) == "Hello world"


def test_partial_delta_still_yields_a_delta_event() -> None:
    acc: list[str] = []
    ev = _parse_claude_line("t1", _partial("Hi"), acc)
    assert ev is not None and ev.type == "delta" and ev.text == "Hi"
    assert acc == ["Hi"]


def test_full_assistant_message_alone_yields_no_text_event() -> None:
    """The recap frame is not a streaming delta source (partials are)."""
    acc: list[str] = []
    ev = _parse_claude_line("t1", _assistant_full("recap only"), acc)
    assert ev is None
    assert acc == []


# --- pre-tool planning monologue is not reply text (B-9) --------------------
# Before calling canvas tools the model often emits a short English planning
# block ("The user confirmed. Let me add it.") and the pipeline used to
# concatenate it with the post-tool reply — internals leaking into the chat
# through a channel the D-2026-07-02-D prompt rule can't reach. A ``tool_use``
# ``content_block_start`` resets the accumulated turn text: only text produced
# after the LAST tool call is the coach's reply. Frame shape verified against
# the live CLI (stream_event → content_block_start → content_block.type).


def _tool_use_start(name: str = "mcp__mashbill__update_node") -> bytes:
    return json.dumps(
        {
            "type": "stream_event",
            "event": {
                "type": "content_block_start",
                "content_block": {"type": "tool_use", "id": "toolu_1", "name": name, "input": {}},
            },
        }
    ).encode()


def test_pre_tool_planning_text_is_dropped_from_the_reply() -> None:
    acc: list[str] = []
    _parse_claude_line("t1", _partial("The user confirmed. Let me add it."), acc)
    _parse_claude_line("t1", _tool_use_start(), acc)
    _parse_claude_line("t1", _partial("네, 올라갔어요."), acc)
    assert "".join(acc) == "네, 올라갔어요."


def test_text_between_tool_calls_is_dropped_too() -> None:
    acc: list[str] = []
    _parse_claude_line("t1", _partial("First I'll read the canvas."), acc)
    _parse_claude_line("t1", _tool_use_start("mcp__mashbill__get_canvas"), acc)
    _parse_claude_line("t1", _partial("Now the edges."), acc)
    _parse_claude_line("t1", _tool_use_start("mcp__mashbill__create_edge"), acc)
    _parse_claude_line("t1", _partial("연결까지 끝났어요."), acc)
    assert "".join(acc) == "연결까지 끝났어요."


def test_turn_without_tool_calls_keeps_all_text() -> None:
    acc: list[str] = []
    _parse_claude_line("t1", _partial("좋아요, "), acc)
    _parse_claude_line("t1", _partial("이어가죠."), acc)
    assert "".join(acc) == "좋아요, 이어가죠."


def test_text_block_start_does_not_reset_the_accumulator() -> None:
    """Only tool_use blocks mark planning text; text/thinking block starts
    arrive before every block and must not wipe legitimate reply text."""
    acc: list[str] = []
    _parse_claude_line("t1", _partial("이어서 "), acc)
    for block in (
        {"type": "text", "text": ""},
        {"type": "thinking", "thinking": "", "signature": ""},
    ):
        _parse_claude_line(
            "t1",
            json.dumps(
                {
                    "type": "stream_event",
                    "event": {"type": "content_block_start", "content_block": block},
                }
            ).encode(),
            acc,
        )
    _parse_claude_line("t1", _partial("말씀드릴게요."), acc)
    assert "".join(acc) == "이어서 말씀드릴게요."


# --- init `model` reporting (D-2026-06-21-Z) -------------------------------
# Claude Code's first stream-json line is a ``system`` / ``init`` frame that
# names the model the CLI actually loaded. Novel surfaces it so the viewer can
# show the real default (codex / gemini don't report theirs).


def _init(model: str) -> bytes:
    return json.dumps(
        {"type": "system", "subtype": "init", "session_id": "s", "model": model}
    ).encode()


def test_init_frame_yields_a_meta_event_with_the_model() -> None:
    acc: list[str] = []
    ev = _parse_claude_line("t1", _init("claude-opus-4-8"), acc)
    assert ev is not None
    assert ev.type == "meta"
    assert ev.model == "claude-opus-4-8"
    assert ev.text == "", "a meta event carries no streamed text"
    assert acc == [], "the init frame is not accumulated as reply text"


def test_init_frame_without_model_yields_nothing() -> None:
    acc: list[str] = []
    ev = _parse_claude_line("t1", json.dumps({"type": "system", "subtype": "init"}).encode(), acc)
    assert ev is None
