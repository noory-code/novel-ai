"""Shared subprocess-driving base for every CLI chat provider.

This module owns the public wire types (``ChatStreamEvent``,
``ChatStreamEventType``, ``ChatProvider`` ABC) and the spawn-parse-yield
loop (``_SubprocessChatProvider``). Concrete per-CLI classes live in
sibling modules and only override two small hooks.
"""

from __future__ import annotations

import asyncio
import json
import os
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Awaitable
from pathlib import Path
from typing import Any, Literal, Protocol
from uuid import uuid4

from pydantic import BaseModel

ChatStreamEventType = Literal["turn_start", "delta", "turn_complete", "error", "meta"]

# Conversation scope (D-2026-06-13-H, Layer 1 per-instance refinement
# D-2026-06-15-B). Chat threads are partitioned per canvas kind plus one
# shared ``project`` scope for cross-canvas work. ``feature`` is the
# one *parametric* member: on the wire it carries the service instance id as
# ``feature:<id>`` so each feature canvas gets its own thread.
# This ``ChatScope`` literal is the **base** member set (the parity SSOT vs
# the TS ``CanvasKind ∪ {project}``); the full wire value is a plain ``str``
# validated by :func:`is_valid_scope`. The viewer sends the active scope on
# each turn and demultiplexes incoming events on it; the engine keys sessions
# on (workspace, provider, scope). Parity is pinned by
# ``tests/test_chat_scope_parity.py``.
ChatScope = Literal[
    "project",
    "foundation",
    "actors",
    "services",
    "entities",
    "feature",
]

# Scope assumed when a client omits it on the wire (Postel's Law,
# D-2026-06-13-H Q1) — cross-canvas work lands in the shared bucket.
DEFAULT_CHAT_SCOPE: ChatScope = "project"

# Singleton scopes are valid bare on the wire. Two members are parametric —
# they require a ``:<id>`` suffix naming a specific instance thread:
# ``feature:<id>`` (one per feature detail canvas) and ``service:<id>`` (one
# per selected service, D-2026-06-26-A).
_PARAMETRIC_PREFIXES: tuple[str, ...] = ("feature:", "service:")
_SINGLETON_SCOPES: frozenset[str] = frozenset(
    {"project", "foundation", "actors", "services", "entities"}
)


def is_valid_scope(raw: str) -> bool:
    """True for a well-formed wire scope (Layer 1, CHAT_ARCH.md).

    A scope is either a singleton base member (``project`` / ``foundation`` /
    ``actors`` / ``services`` / ``entities``) or a parametric instance scope
    (``feature:<id>`` / ``service:<id>``) with a non-empty id. A bare parametric
    member (no id) is rejected — it names no specific thread (Fail Fast). The
    engine keys sessions on the full string, so an unknown id simply gets its
    own (orphaned) thread; resolving stale ids back to the ``services`` scope is
    the viewer's job (CHAT_ARCH.md decision 6).
    """
    if raw in _SINGLETON_SCOPES:
        return True
    for prefix in _PARAMETRIC_PREFIXES:
        if raw.startswith(prefix):
            return bool(raw[len(prefix) :])
    return False


class ChatStreamEvent(BaseModel):
    """One streamed event in a chat turn.

    The viewer renders ``turn_start`` as "an assistant turn is forming", each
    ``delta`` appends ``text`` to the active turn, ``turn_complete`` carries
    the full accumulated text (so a late-joining subscriber can reconcile),
    and ``error`` aborts the turn and surfaces ``error_message`` in the UI.
    A ``meta`` event carries no streamed text — it reports the model the CLI
    actually loaded in ``model`` (D-2026-06-21-Z), so the viewer can show the
    real default when the user hasn't overridden it. Only providers whose CLI
    reports the model emit it (claude-code does; codex / gemini don't).

    ``scope`` echoes which conversation bucket the turn belongs to so the
    viewer can route the event to the matching canvas thread (D-2026-06-13-H).
    It is a plain ``str`` so it can carry a parametric ``feature:<id>``
    value (Layer 1, D-2026-06-15-B), not just a base ``ChatScope`` member.
    """

    type: ChatStreamEventType
    turn_id: str
    text: str = ""
    error_message: str | None = None
    scope: str = DEFAULT_CHAT_SCOPE
    # Set only on ``meta`` events — the model id the CLI reported (D-2026-06-21-Z).
    model: str | None = None


class _SubprocessFactory(Protocol):
    """Match the slice of ``asyncio.create_subprocess_exec`` we need.

    Defined as a Protocol so callers can pass a fake in tests without faking
    every keyword argument the stdlib version accepts.
    """

    def __call__(
        self,
        *cmd: str,
        cwd: str | None = ...,
        env: dict[str, str] | None = ...,
        stdout: int | None = ...,
        stderr: int | None = ...,
        stdin: int | None = ...,
    ) -> Awaitable[Any]: ...


class ChatProvider(ABC):
    """Drives one external CLI for one workspace."""

    @abstractmethod
    def stream_turn(self, user_message: str) -> AsyncIterator[ChatStreamEvent]:
        """Send one user message, yield assistant stream events.

        Implementations MUST yield ``turn_start`` first and end with either
        ``turn_complete`` (success) or ``error`` (failure). If the consumer
        closes the iterator early, the underlying process is killed.
        """
        ...

    @property
    def is_first_turn(self) -> bool:
        """Whether this provider has yet to run a turn (D-2026-06-26-F).

        Default ``False`` so fakes / non-subprocess providers don't trigger a
        transcript re-feed. Subprocess providers override it to report real CLI
        session freshness, so the send endpoint re-feeds the saved transcript
        only on a genuinely fresh session.
        """
        return False

    def set_model(self, model: str | None) -> None:
        """Set the CLI model override for subsequent turns (D-2026-06-16-C).

        Default no-op so fakes / future non-subprocess providers don't have to
        implement it. The send endpoint calls this each turn with the
        workspace's persisted choice; an empty / ``None`` value means "use the
        CLI's own configured default".
        """
        ...

    def set_system_prompt(self, text: str | None) -> None:
        """Set the Layer-3 system prompt for subsequent turns (Lever 2).

        Default no-op for the same reason as :meth:`set_model`. The send
        endpoint calls this each turn with the scope's framing + hallucination
        guard (:func:`mashbill.chat_context.build_system_prompt`); an empty /
        ``None`` value means "no system prompt".
        """
        ...


class _SubprocessChatProvider(ChatProvider):
    """Shared spawn → parse → yield loop for every CLI-backed provider.

    Subclasses override two hooks:

      * ``_build_command(user_message)`` — produce the argv. Subclasses use
        ``self._first_turn`` and ``self._session_id`` (which they may have
        captured from earlier output) to switch between "start a new
        session" and "resume the previous one".
      * ``_parse_line(turn_id, line, accumulator)`` — turn one stdout line
        into a ``ChatStreamEvent`` (``delta`` only — ``turn_start`` /
        ``turn_complete`` / ``error`` are emitted by this base). Subclasses
        may mutate ``self._session_id`` when they spot the CLI's
        session-id event (codex ``thread.started``, gemini ``init``, …).
    """

    def __init__(
        self,
        workspace_root: Path,
        *,
        cli_path: str,
        subprocess_factory: _SubprocessFactory | None = None,
    ) -> None:
        self._workspace = workspace_root
        self._cli_path = cli_path
        self._first_turn = True
        self._session_id: str | None = None
        self._model: str | None = None
        self._system_prompt: str | None = None
        self._spawn: _SubprocessFactory = (
            subprocess_factory if subprocess_factory is not None else _default_spawn
        )

    @property
    def session_id(self) -> str | None:
        return self._session_id

    @property
    def is_first_turn(self) -> bool:
        """True before this provider has run any turn. A fresh provider (e.g. after
        an engine restart wiped the in-memory registry) has no CLI session memory,
        so the caller re-feeds the saved transcript on this turn (D-2026-06-26-F)."""
        return self._first_turn

    def set_model(self, model: str | None) -> None:
        """Store the CLI model override (D-2026-06-16-C). Empty → unset."""
        self._model = model or None

    def set_system_prompt(self, text: str | None) -> None:
        """Store the Layer-3 system prompt (Lever 2). Empty → unset."""
        self._system_prompt = text or None

    def _prepend_system(self, user_message: str) -> str:
        """Fallback delivery for CLIs without a system-prompt flag.

        Providers whose CLI takes the prompt as a bare positional arg (codex
        ``exec``) have no equivalent of claude's ``--append-system-prompt``, so
        the system prompt rides in front of the user message. Returns the
        message unchanged when no system prompt is set.
        """
        if not self._system_prompt:
            return user_message
        return f"{self._system_prompt}\n\n{user_message}"

    def _model_args(self) -> list[str]:
        """``["--model", <model>]`` when a model is set, else ``[]``.

        Every supported CLI (``claude`` / ``codex`` / ``gemini``) accepts
        ``--model`` (verified against the installed binaries), so the flag name
        is shared; concrete providers splice this into their argv.
        """
        return ["--model", self._model] if self._model else []

    @abstractmethod
    def _build_command(self, user_message: str) -> list[str]: ...

    @abstractmethod
    def _parse_line(
        self, turn_id: str, line: bytes, accumulator: list[str]
    ) -> ChatStreamEvent | None: ...

    def _spawn_env(self) -> dict[str, str] | None:
        """Environment for the CLI subprocess: the engine's env MINUS its own
        runtime toggles. A provider may override to add vars (e.g. claude-code's
        memory-disable, D-2026-06-21-I) — it must merge over this base
        (``{**super()._spawn_env(), ...}``), since a dict replaces the env.

        The strip matters (found by the coach-sim harness, 2026-07-02): the CLI
        spawns the engine's own mashbill MCP stdio server as a child, which
        inherits this env transitively. An engine started HTTP-only
        (``MASHBILL_NO_MCP=1`` — the documented dev loop) leaked that toggle
        down, so the coach's tool server booted with "no transports to start"
        and exited — the coach silently lost every canvas tool and could only
        talk. ``MASHBILL_PORT`` is stripped for the same reason (the child
        would collide with the engine's own busy port instead of using its
        default).
        """
        return {
            k: v
            for k, v in os.environ.items()
            if k not in ("MASHBILL_NO_MCP", "MASHBILL_PORT")
        }

    async def stream_turn(self, user_message: str) -> AsyncIterator[ChatStreamEvent]:
        turn_id = str(uuid4())
        cmd = self._build_command(user_message)

        proc = await self._spawn(
            *cmd,
            cwd=str(self._workspace),
            env=self._spawn_env(),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            # The prompt is passed as an arg, so the child must never read stdin.
            # Without an explicit EOF it inherits the engine sidecar's stdin and
            # blocks — `codex exec` does exactly this ("Reading additional input
            # from stdin...") and yields no response. DEVNULL gives every provider
            # an immediate EOF. D-2026-06-23-F.
            stdin=asyncio.subprocess.DEVNULL,
        )

        # Flip the first-turn flag before reading output so a crash mid-stream
        # still leaves the CLI's session store intact for the next turn.
        self._first_turn = False

        yield ChatStreamEvent(type="turn_start", turn_id=turn_id)
        accumulator: list[str] = []
        try:
            if proc.stdout is not None:
                async for line in proc.stdout:
                    event = self._parse_line(turn_id, line, accumulator)
                    if event is not None:
                        yield event
            rc = await proc.wait()
            if rc != 0:
                stderr_text = ""
                if proc.stderr is not None:
                    raw = await proc.stderr.read()
                    stderr_text = raw.decode("utf-8", errors="replace").strip()
                yield ChatStreamEvent(
                    type="error",
                    turn_id=turn_id,
                    error_message=stderr_text or f"{self._cli_path} exited {rc}",
                )
            else:
                yield ChatStreamEvent(
                    type="turn_complete",
                    turn_id=turn_id,
                    text="".join(accumulator),
                )
        finally:
            if proc.returncode is None:
                try:
                    proc.kill()
                except ProcessLookupError:
                    pass


async def _default_spawn(
    *cmd: str,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
    stdout: int | None = None,
    stderr: int | None = None,
    stdin: int | None = None,
) -> asyncio.subprocess.Process:
    """Thin wrapper around ``asyncio.create_subprocess_exec`` so the type of
    the default factory exactly matches the ``_SubprocessFactory`` protocol.
    ``env=None`` inherits the parent environment.
    """
    return await asyncio.create_subprocess_exec(
        *cmd,
        cwd=cwd,
        env=env,
        stdout=stdout,
        stderr=stderr,
        stdin=stdin,
    )


def _decode_jsonl(line: bytes) -> dict[str, Any] | None:
    """Strict line → dict decode. Skips blank lines + JSON errors silently."""
    raw = line.decode("utf-8", errors="replace").strip()
    if not raw:
        return None
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(obj, dict):
        return None
    return obj
