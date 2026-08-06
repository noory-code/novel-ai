"""Codex CLI driver (``codex exec --json``).

Codex emits JSONL events with ``thread.started`` / ``turn.started`` /
``item.completed`` / ``turn.completed``. The first event of the first
turn carries ``thread_id`` — we capture it so later turns can
``codex exec resume <id>``. ``--skip-git-repo-check`` keeps Codex from
refusing to run when the user opened Novel on a folder that isn't a git
repo (yet). The working directory is set via ``cwd=`` on the spawn, not
Codex's ``-C`` flag, so every provider shares one root-resolution path.
"""

from __future__ import annotations

import json
from pathlib import Path

from mashbill.chat_providers.base import (
    ChatStreamEvent,
    _decode_jsonl,
    _SubprocessChatProvider,
    _SubprocessFactory,
)
from mashbill.mcp_registration import codex_mashbill_config

# Reasoning levels codex accepts via `-c model_reasoning_effort=<level>`. The
# chat model selector encodes the user's pick as "<slug>:<effort>"
# (D-2026-06-22-C); this set lets the provider split a known effort suffix back
# out from the slug. Mirrors the labels in ``chat_models._EFFORT_LABEL``.
_CODEX_EFFORTS = frozenset({"low", "medium", "high", "xhigh"})


class CodexProvider(_SubprocessChatProvider):
    """``codex exec --json`` driver with thread-id continuity."""

    def __init__(
        self,
        workspace_root: Path,
        *,
        cli_path: str = "codex",
        subprocess_factory: _SubprocessFactory | None = None,
    ) -> None:
        super().__init__(
            workspace_root,
            cli_path=cli_path,
            subprocess_factory=subprocess_factory,
        )

    def _model_args(self) -> list[str]:
        # Split the composite "<slug>:<effort>" the selector produces
        # (D-2026-06-22-C): a known effort suffix becomes a separate
        # ``-c model_reasoning_effort=`` override; anything else is a bare model.
        if not self._model:
            return []
        slug, sep, effort = self._model.rpartition(":")
        if sep and slug and effort in _CODEX_EFFORTS:
            return ["--model", slug, "-c", f"model_reasoning_effort={effort}"]
        return ["--model", self._model]

    def _build_command(self, user_message: str) -> list[str]:
        # Until we've captured a thread_id, every turn starts a fresh session
        # — this also covers the "first turn never emitted thread.started"
        # crash-recovery path so we don't try to ``resume None``.
        # codex exec has no system-prompt flag — the prompt is the trailing
        # positional arg — so the Layer-3 system prompt (Lever 2) rides in front
        # of the user message via the base ``_prepend_system`` fallback.
        message = self._prepend_system(user_message)
        mcp_entry = codex_mashbill_config()["mcp_servers"]["mashbill"]
        command = [
            self._cli_path,
            "exec",
        ]
        turn_args = [
            "--json",
            "--skip-git-repo-check",
            # D-2026-07-21-B — stdin is DEVNULL, so a headless coach cannot answer
            # an approval prompt. ``codex exec`` has no ``--ask-for-approval``;
            # its documented non-interactive escape is this bypass flag (verified
            # against the installed CLI — the injected Mashbill MCP owns canvas
            # mutations; Codex's own shell is not what writes the canvas).
            "--dangerously-bypass-approvals-and-sandbox",
            # Ignore ~/.codex/config.toml for this turn, then inject THIS
            # engine build's stdio server with Codex's TOML config overrides.
            # JSON strings/arrays are valid TOML values and safely preserve
            # spaces in frozen binary paths and plugin-root arguments.
            "--ignore-user-config",
            "-c",
            f"mcp_servers.mashbill.command={json.dumps(mcp_entry['command'])}",
            "-c",
            f"mcp_servers.mashbill.args={json.dumps(mcp_entry['args'])}",
            *self._model_args(),
        ]
        if self._first_turn or self._session_id is None:
            return [*command, *turn_args, message]
        return [
            *command,
            "resume",
            self._session_id,
            *turn_args,
            message,
        ]

    def _parse_line(
        self, turn_id: str, line: bytes, accumulator: list[str]
    ) -> ChatStreamEvent | None:
        obj = _decode_jsonl(line)
        if obj is None:
            return None
        event_type = obj.get("type")
        if event_type == "thread.started":
            tid = obj.get("thread_id")
            if isinstance(tid, str) and tid:
                self._session_id = tid
            return None
        if event_type == "item.completed":
            item = obj.get("item")
            if isinstance(item, dict) and item.get("type") == "agent_message":
                text = item.get("text")
                if isinstance(text, str) and text:
                    # Codex routinely emits TWO agent messages in one turn — a
                    # short ack before its MCP canvas work, then a
                    # restate-and-continue after. Joined bare they read as the
                    # coach stuttering (workspace O-34; every instrumented turn
                    # of the 2026-08-06 figma plate had exactly this shape).
                    # Dropping either loses content — the second does not always
                    # restate the first — so a paragraph break rides IN the
                    # delta, keeping turn_complete.text exactly the
                    # concatenation of the deltas (base.py reconciliation
                    # contract).
                    if accumulator:
                        text = "\n\n" + text
                    accumulator.append(text)
                    return ChatStreamEvent(type="delta", turn_id=turn_id, text=text)
        return None
