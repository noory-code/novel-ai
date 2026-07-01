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
        {"type": "stream_event", "event": {"type": "content_block_delta",
         "delta": {"type": "text_delta", "text": text}}}
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
    ev = _parse_claude_line(
        "t1", json.dumps({"type": "system", "subtype": "init"}).encode(), acc
    )
    assert ev is None
