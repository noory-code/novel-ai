"""R7 chat — public surface (D-2026-06-12-D + v0.64.1).

Thin facade over ``mashbill.chat_providers/*``. Exports the wire types
(``ChatStreamEvent``, ``ChatStreamEventType``), the ABC (``ChatProvider``),
each concrete CLI driver (``ClaudeCodeProvider`` / ``CodexProvider`` /
``GeminiProvider``), and the per-process registry (``ChatSessionRegistry``
+ ``chat_registry()`` accessor). The split happened to keep every file
under the engine's 500-line module rule once Codex and Gemini joined the
party; callers see one import surface.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from mashbill.chat_providers.base import (
    DEFAULT_CHAT_SCOPE,
    ChatProvider,
    ChatScope,
    ChatStreamEvent,
    ChatStreamEventType,
)
from mashbill.chat_providers.claude_code import ClaudeCodeProvider, _parse_claude_line
from mashbill.chat_providers.codex import CodexProvider
from mashbill.mcp_registration import ProviderName

# Back-compat alias — v0.64.0 tests imported ``_parse_stream_line`` from
# this module. The concrete function lives in ``chat_providers.claude_code``
# now (which is the only caller that matters), but the alias stays so any
# external integration code keeps linking.
_parse_stream_line = _parse_claude_line


__all__ = [
    "DEFAULT_CHAT_SCOPE",
    "ChatProvider",
    "ChatScope",
    "ChatSessionRegistry",
    "ChatStreamEvent",
    "ChatStreamEventType",
    "ClaudeCodeProvider",
    "CodexProvider",
    "chat_registry",
    "_parse_stream_line",
]


# ---------------------------------------------------------------------------
# Session registry — keyed by (workspace, provider) so the user can switch
# CLIs and come back without losing either conversation.
# ---------------------------------------------------------------------------


ProviderFactory = Callable[[Path, ProviderName], ChatProvider]


def _default_provider_factory(workspace_root: Path, provider_name: ProviderName) -> ChatProvider:
    if provider_name == "claude-code":
        return ClaudeCodeProvider(workspace_root=workspace_root)
    if provider_name == "codex":
        return CodexProvider(workspace_root=workspace_root)
    # ``ProviderName`` is a Literal — mypy enforces; this is the runtime
    # safety net for an unexpected value (corrupt selection file, future
    # provider added to the literal but not here).
    raise ValueError(f"unsupported chat provider: {provider_name!r}")


# ``scope`` is the full wire value — a base ``ChatScope`` member or a
# parametric ``feature:<id>`` (Layer 1, D-2026-06-15-B) — so a ``str``,
# not the base literal. Keyed on the triple, two feature canvases get
# their own threads.
_SessionKey = tuple[Path, ProviderName, str]


class ChatSessionRegistry:
    """One ``ChatProvider`` instance per (resolved workspace, provider, scope).

    Keying on the triple (not just path, not just path+provider) means a user
    who switches Claude → Codex → Claude, or who hops between the Foundation
    and Actors canvases, resumes each conversation cleanly instead of
    overwriting whichever was cached. ``scope`` partitions threads per canvas
    kind plus the shared ``project`` bucket (D-2026-06-13-H). The registry's
    only responsibility is identity continuity — call ``get_or_create`` twice
    with the same triple and you get the same provider.
    """

    def __init__(self, *, factory: ProviderFactory | None = None) -> None:
        self._sessions: dict[_SessionKey, ChatProvider] = {}
        self._factory: ProviderFactory = factory or _default_provider_factory

    def get_or_create(
        self,
        workspace_root: Path,
        provider_name: ProviderName,
        scope: str = DEFAULT_CHAT_SCOPE,
    ) -> ChatProvider:
        key: _SessionKey = (workspace_root.resolve(), provider_name, scope)
        provider = self._sessions.get(key)
        if provider is None:
            provider = self._factory(key[0], provider_name)
            self._sessions[key] = provider
        return provider

    def reset(
        self,
        workspace_root: Path,
        provider_name: ProviderName | None = None,
        *,
        scope: str | None = None,
    ) -> None:
        """Drop the sessions matching the given filters for ``workspace_root``.

        ``provider_name`` / ``scope`` are independent narrowing filters — a
        ``None`` filter matches every value of that axis. The dock's Reset
        button passes ``scope=<active canvas>`` so it wipes only the current
        canvas thread (Q3); ``reset(ws)`` with both ``None`` wipes the whole
        workspace.
        """
        resolved = workspace_root.resolve()

        def drop(key: _SessionKey) -> bool:
            ws, prov, scp = key
            if ws != resolved:
                return False
            if provider_name is not None and prov != provider_name:
                return False
            if scope is not None and scp != scope:
                return False
            return True

        self._sessions = {k: v for k, v in self._sessions.items() if not drop(k)}

    def session_count(self) -> int:
        return len(self._sessions)


# ---------------------------------------------------------------------------
# Module-level singleton — the engine has one registry per process.
# ---------------------------------------------------------------------------


_REGISTRY = ChatSessionRegistry()


def chat_registry() -> ChatSessionRegistry:
    return _REGISTRY
