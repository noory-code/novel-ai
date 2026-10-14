"""Codex CLI driver (``codex exec --json``).

Codex emits JSONL events with ``thread.started`` / ``turn.started`` /
``item.completed`` / ``turn.completed`` / ``turn.failed`` / ``error``.
The first event of the first
turn carries ``thread_id`` — we capture it so later turns can
``codex exec resume <id>``. ``--skip-git-repo-check`` keeps Codex from
refusing to run when the user opened Novel on a folder that isn't a git
repo (yet). The working directory is set via ``cwd=`` on the spawn, not
Codex's ``-C`` flag, so every provider shares one root-resolution path.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from mashbill.chat_providers.base import (
    ChatStreamEvent,
    _decode_jsonl,
    _ParsedCliError,
    _SubprocessChatProvider,
    _SubprocessFactory,
)
from mashbill.chat_scope_env import CHAT_SCOPE_ENV
from mashbill.mcp_registration import IN_APP_COACH_ENV, codex_mashbill_config
from mashbill.tool_log import TOOL_LOG_ENV

# Reasoning levels codex accepts via `-c model_reasoning_effort=<level>`. The
# chat model selector encodes the user's pick as "<slug>:<effort>"
# (D-2026-06-22-C); this set lets the provider split a known effort suffix back
# out from the slug.
# Mirrors the effort levels the Codex model catalogue reports (supported_reasoning_levels).
_CODEX_EFFORTS = frozenset({"low", "medium", "high", "xhigh", "max", "ultra"})

# W-00000450 — Codex runs the coach in code mode: it calls MCP tools from a
# small script and looked up each tool's shape first (32 of 121 model round
# trips in the newcomer walk, ~8 s each). Stating the call shape removes those
# lookups (docs/research/coach-codemode/README.md). It rides after the system
# prompt, outside the shared prompt word budget, because only Codex needs it.
CODEX_TOOL_HINT = (
    "Tool calls: in code mode call a Mashbill tool directly as "
    "`await tools.mcp__mashbill__<tool>({...})` with the argument names shown in "
    "this prompt, without searching ALL_TOOLS for it first."
)
# Set to "0" to leave the hint out (simulator A/B runs only).
CODEX_TOOL_HINT_ENV = "MASHBILL_CODEX_TOOL_HINT"


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

    def _tool_log_args(self) -> list[str]:
        """Hand the injected tool server the path to record its calls to.

        The server is a grandchild — engine spawns codex, codex spawns the
        server — and whether it inherits our environment is codex's business,
        not ours. State it explicitly rather than trust two spawns we do not
        control (W-00000177). Empty unless a simulator run asked for recording,
        so a user's own session carries no stray override.
        """
        path = os.environ.get(TOOL_LOG_ENV)
        if not path:
            return []
        return ["-c", f"mcp_servers.mashbill.env.{TOOL_LOG_ENV}={json.dumps(path)}"]

    def _chat_scope_args(self) -> list[str]:
        """Hand the injected tool server this turn's conversation scope."""
        if not self._chat_scope:
            return []
        return [
            "-c",
            f"mcp_servers.mashbill.env.{CHAT_SCOPE_ENV}={json.dumps(self._chat_scope)}",
        ]

    def _model_args(self) -> list[str]:
        # Split the composite "<slug>:<effort>" the selector produces
        # (D-2026-06-22-C): a known effort suffix becomes a separate
        # ``-c model_reasoning_effort=`` override; anything else is a bare model.
        return self._model_args_for(self._model)

    def _model_args_for(self, model: str | None) -> list[str]:
        if not model:
            return []
        slug, sep, effort = model.rpartition(":")
        if sep and slug and effort in _CODEX_EFFORTS:
            return ["--model", slug, "-c", f"model_reasoning_effort={effort}"]
        return ["--model", model]

    def _build_command(self, user_message: str) -> list[str]:
        # Until we've captured a thread_id, every turn starts a fresh session
        # — this also covers the "first turn never emitted thread.started"
        # crash-recovery path so we don't try to ``resume None``.
        # codex exec has no system-prompt flag — the prompt is the trailing
        # positional arg — so the Layer-3 system prompt (Lever 2) rides in front
        # of the user message via the base ``_prepend_system`` fallback.
        message = self._prepend_system(user_message)
        if self._system_prompt and os.environ.get(CODEX_TOOL_HINT_ENV) != "0":
            message = f"{self._system_prompt}\n\n{CODEX_TOOL_HINT}\n\n{user_message}"
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
            # D-2026-10-10-A / D-2026-06-21-I: keep chat grounded in the
            # workspace without loading parent skills or any AGENTS.md.
            "-c",
            "project_root_markers=[]",
            "-c",
            "project_doc_max_bytes=0",
            "-c",
            f"mcp_servers.mashbill.command={json.dumps(mcp_entry['command'])}",
            "-c",
            f"mcp_servers.mashbill.args={json.dumps(mcp_entry['args'])}",
            "-c",
            f"mcp_servers.mashbill.env.{IN_APP_COACH_ENV}={json.dumps('1')}",
            *self._tool_log_args(),
            *self._chat_scope_args(),
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
    ) -> ChatStreamEvent | _ParsedCliError | None:
        obj = _decode_jsonl(line)
        if obj is None:
            return None
        event_type = obj.get("type")
        if event_type in ("error", "turn.failed"):
            detail = obj.get("error") if event_type == "turn.failed" else obj
            message = detail.get("message") if isinstance(detail, dict) else None
            return _ParsedCliError(
                message=message if isinstance(message, str) and message.strip() else None,
                turn_failed=event_type == "turn.failed",
            )
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
                    # Codex emits a commentary message before its tool work and
                    # a final answer after (exec JSON has no phase field to tell
                    # them apart). Every message still streams live as a delta so
                    # the person sees progress, but a later message makes the
                    # earlier one commentary: the accumulator — which becomes
                    # turn_complete.text, what the viewer settles on and what is
                    # stored — keeps only the latest message. Joining them
                    # (workspace O-34) repeated the reply in 33 of 42 newcomer-walk
                    # turns and sometimes contradicted it (W-00000454).
                    live = "\n\n" + text if accumulator else text
                    accumulator.clear()
                    accumulator.append(text)
                    return ChatStreamEvent(type="delta", turn_id=turn_id, text=live)
        return None

    async def complete_once(self, prompt: str, *, model: str | None = None) -> str:
        """Run an ephemeral, read-only Codex completion without injected MCP tools."""
        with tempfile.TemporaryDirectory(prefix="mashbill-slug-suggest-") as isolated_root:
            raw = await self._capture_once(
                [
                    self._cli_path,
                    "exec",
                    "--json",
                    "--skip-git-repo-check",
                    "--ephemeral",
                    "--ignore-user-config",
                    "--ignore-rules",
                    "--sandbox",
                    "read-only",
                    "--cd",
                    isolated_root,
                    *self._model_args_for(model),
                    prompt,
                ]
            )
        messages: list[str] = []
        for line in raw.splitlines():
            obj = _decode_jsonl(line.encode())
            if obj is None or obj.get("type") != "item.completed":
                continue
            item = obj.get("item")
            if not isinstance(item, dict) or item.get("type") != "agent_message":
                continue
            text = item.get("text")
            if isinstance(text, str) and text:
                messages.append(text)
        return "\n\n".join(messages)
