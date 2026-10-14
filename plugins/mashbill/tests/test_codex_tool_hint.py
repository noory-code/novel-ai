"""W-00000450 — the Codex coach is told how to call the Mashbill tools.

Codex runs the coach in code mode: it calls MCP tools from a small script and
had to look up each tool's shape first (32 of 121 model round trips in the
newcomer walk, about 8 s each). Telling it the call shape up front removed
those lookups (docs/research/coach-codemode/README.md).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mashbill.chat_providers.codex import CODEX_TOOL_HINT, CODEX_TOOL_HINT_ENV, CodexProvider


def _message(tmp_path: Path) -> str:
    p = CodexProvider(workspace_root=tmp_path)
    p.set_system_prompt("SYSTEM")
    return p._build_command("미션이 뭐야?")[-1]


def test_codex_coach_turn_carries_the_tool_call_shape(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(CODEX_TOOL_HINT_ENV, raising=False)
    msg = _message(tmp_path)
    assert CODEX_TOOL_HINT in msg
    assert "await tools.mcp__mashbill__" in CODEX_TOOL_HINT
    # system prompt first, then the hint, then the person's message
    assert msg.index("SYSTEM") < msg.index(CODEX_TOOL_HINT) < msg.index("미션이 뭐야?")


def test_tool_hint_can_be_switched_off_for_experiments(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(CODEX_TOOL_HINT_ENV, "0")
    assert CODEX_TOOL_HINT not in _message(tmp_path)


def test_a_turn_without_a_system_prompt_gets_no_hint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(CODEX_TOOL_HINT_ENV, raising=False)
    p = CodexProvider(workspace_root=tmp_path)
    assert p._build_command("hi")[-1] == "hi"
