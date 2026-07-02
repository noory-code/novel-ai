"""Claude Code CLI driver (``claude --print``).

The first turn passes ``--session-id <uuid>`` so Novel mints the
conversation id; every later turn passes ``--resume <uuid>`` so the CLI
loads its persisted transcript and the conversation continues naturally.
``--include-partial-messages`` flips the JSONL stream into incremental
``content_block_delta`` events so the dock shows text as it's produced.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any
from uuid import uuid4

from mashbill.chat_providers.base import (
    ChatStreamEvent,
    _decode_jsonl,
    _SubprocessChatProvider,
    _SubprocessFactory,
)
from mashbill.mcp_registration import mashbill_config


class ClaudeCodeProvider(_SubprocessChatProvider):
    """One subprocess per turn, conversation continuity via ``--session-id``."""

    def __init__(
        self,
        workspace_root: Path,
        *,
        session_id: str | None = None,
        cli_path: str = "claude",
        subprocess_factory: _SubprocessFactory | None = None,
    ) -> None:
        super().__init__(
            workspace_root,
            cli_path=cli_path,
            subprocess_factory=subprocess_factory,
        )
        # Claude is the only CLI where Novel mints the session id; the others
        # report theirs through the first event of the first turn.
        self._session_id = session_id or str(uuid4())

    def _build_command(self, user_message: str) -> list[str]:
        cmd = [
            self._cli_path,
            "--print",
            "--output-format",
            "stream-json",
            "--include-partial-messages",
            "--verbose",  # stream-json requires verbose mode
            # D-2026-06-21-C — auto-allow the user's own mashbill MCP tools. Headless
            # ``-p`` can't show a permission prompt, so without this the agent
            # dead-ends ("press Allow" with nothing to press). Scoped to
            # ``mcp__mashbill__*`` ONLY — Bash / Write / filesystem keep default
            # behaviour, so the in-app agent can't silently touch anything
            # outside the user's .noory/plot data (which is git-recoverable and
            # surfaced on the canvas per build-through-discussion).
            "--allowedTools",
            "mcp__mashbill__*",
            # D-2026-06-26-E — attach THIS engine's own mashbill MCP server directly,
            # and use ONLY it. The in-app coach used to inherit ``plot`` from the
            # user's global ``~/.claude.json``; that pointer drifts (a deleted /
            # older app build) and silently leaves the coach with no canvas tools
            # — the "in-app chat can't write to the canvas" failure. ``--mcp-config``
            # injects the running build's stdio server; ``--strict-mcp-config``
            # ignores every other MCP source, so the coach carries exactly Novel's
            # tools (and none of the user's unrelated servers), never depending on
            # the global registration.
            "--mcp-config",
            self._mcp_config_path(),
            "--strict-mcp-config",
            # D-2026-06-21-I — ground the in-app agent ONLY in the workspace:
            # load only workspace-local settings (no parent / global CLAUDE.md
            # auto-discovery, no user-scope config) and keep the memory paths /
            # cwd / env out of the system prompt. OAuth subscription auth is
            # untouched (this is NOT --bare, which would force an API key).
            # Auto-memory is killed via the ``CLAUDE_CODE_DISABLE_AUTO_MEMORY``
            # env (see ``_spawn_env``).
            "--setting-sources",
            "local",
            # Lever 2 (docs/idea/chat/01-levers.md) — deliver the Layer-3
            # framing + hallucination guard as an authoritative system prompt
            # rather than gluing it into the user message. claude has a native
            # flag for exactly this; ``--append-system-prompt`` augments (not
            # replaces) claude's own system prompt.
            *(["--append-system-prompt", self._system_prompt] if self._system_prompt else []),
            # NOTE: do NOT add `--exclude-dynamic-system-prompt-sections` here.
            # It is not a real claude CLI flag (D-2026-06-21-I assumed it without
            # verifying); the CLI rejects it with "unknown option" and the whole
            # chat turn dies. Workspace grounding is carried by --setting-sources
            # local + CLAUDE_CODE_DISABLE_AUTO_MEMORY (see _spawn_env). D-2026-06-23-E.
            *self._model_args(),
        ]
        if self._first_turn:
            assert self._session_id is not None  # ctor guarantees this
            cmd += ["--session-id", self._session_id]
        else:
            assert self._session_id is not None
            cmd += ["--resume", self._session_id]
        cmd.append(user_message)
        return cmd

    def _mcp_config_path(self) -> str:
        """Write the in-app mashbill MCP config to a temp file and return its path
        (D-2026-06-26-E). Passed to claude via ``--mcp-config`` so the coach
        always carries this build's Novel tools.

        Content is stable per install (the engine's own stdio command), so the
        file is content-addressed under the OS temp dir — idempotent across turns
        and safe if a dev + frozen build ever run side by side (different hash →
        different file). Cross-platform: ``tempfile.gettempdir()`` (never a
        hardcoded ``/tmp``)."""
        raw = json.dumps(mashbill_config(), indent=2)
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
        path = Path(tempfile.gettempdir()) / f"mashbill-inapp-mcp-{digest}.json"
        if not path.is_file() or path.read_text(encoding="utf-8") != raw:
            path.write_text(raw, encoding="utf-8")
        return str(path)

    def _spawn_env(self) -> dict[str, str] | None:
        # D-2026-06-21-I — disable Claude Code auto-memory for the in-app agent
        # so it can't pull in the user's saved memories from outside the
        # workspace. Merge over the sanitized base env (strips the engine's own
        # runtime toggles — see the base docstring; a plain dict would REPLACE
        # the env, so the full merge matters).
        return {**(super()._spawn_env() or {}), "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"}

    def _parse_line(
        self, turn_id: str, line: bytes, accumulator: list[str]
    ) -> ChatStreamEvent | None:
        return _parse_claude_line(turn_id, line, accumulator)


def _parse_claude_line(turn_id: str, line: bytes, accumulator: list[str]) -> ChatStreamEvent | None:
    """Decode one Claude Code ``stream-json`` line into a ``delta`` event.

    Streaming text comes from the **partial** frames only (D-2026-06-21-B):
      ``{"type":"stream_event", "event":{"type":"content_block_delta",
         "delta":{"type":"text_delta", "text":"..."}}}``

    With ``--include-partial-messages`` the CLI ALSO emits a final full
    ``assistant`` recap message carrying the same complete block text. Counting
    both doubles the reply ("살펴볼게요.살펴볼게요."), so the recap is ignored
    here — the partials are the single source of the streamed text.
    """
    obj = _decode_jsonl(line)
    if obj is None:
        return None
    # The first line is a ``system`` / ``init`` frame naming the model the CLI
    # loaded — surface it as a ``meta`` event so the viewer can show the real
    # default (D-2026-06-21-Z). It carries no reply text, so report it before
    # the text path.
    model = _extract_anthropic_model(obj)
    if model:
        return ChatStreamEvent(type="meta", turn_id=turn_id, model=model)
    text = _extract_anthropic_text(obj)
    if not text:
        return None
    accumulator.append(text)
    return ChatStreamEvent(type="delta", turn_id=turn_id, text=text)


def _extract_anthropic_model(obj: dict[str, Any]) -> str | None:
    """The model id from the ``system`` / ``init`` frame, or ``None``.

    Claude Code's first stream-json line is
    ``{"type":"system","subtype":"init",...,"model":"claude-..."}`` (D-2026-06-21-Z).
    """
    if obj.get("type") == "system" and obj.get("subtype") == "init":
        model = obj.get("model")
        if isinstance(model, str) and model:
            return model
    return None


def _extract_anthropic_text(obj: dict[str, Any]) -> str:
    """Streamed text from a partial ``content_block_delta`` frame, or ``""``.

    The full ``assistant`` recap message is intentionally NOT a source — the
    partials already carry the complete text, and counting the recap doubles
    the reply (D-2026-06-21-B)."""
    event = obj.get("event")
    if isinstance(event, dict):
        delta = event.get("delta")
        if isinstance(delta, dict) and delta.get("type") == "text_delta":
            t = delta.get("text")
            if isinstance(t, str):
                return t
    return ""
