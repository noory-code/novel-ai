"""Workspace-scoped chat provider selection (D-2026-06-11-E, Phase B step B3).

When more than one external CLI is installed and Novel-registered, the user
picks which one drives the R7 chat panel. That pick lives at
``<workspace>/.noory/plot/chat-provider`` (JSON,
``{"provider": "claude-code" | "codex" | "gemini" | null}``) so it survives
across reloads and moved machines (the file rides the workspace).

This module is the file-IO + validation seam; HTTP wiring lives in
``endpoints_mcp.chat_provider_get_endpoint`` / ``chat_provider_put_endpoint``.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from mashbill.mcp_registration import ProviderName

_SELECTION_FILENAME = "chat-provider"


class ChatProviderSelection(BaseModel):
    """Persisted chat-CLI choice for one workspace.

    ``provider`` is ``None`` when no choice has been made yet (or the user
    cleared it). The literal union mirrors ``ProviderName`` from
    ``mcp_registration``; pydantic rejects any other string at the boundary
    so malformed disk state can't leak past this module.

    ``model`` (D-2026-06-16-C) is the optional CLI model override for the
    chosen provider — ``None`` / empty means "let the CLI use its own
    configured default". Passed to the provider as ``--model <model>`` (all
    three CLIs accept it). Reset to ``None`` when the provider changes (a
    model valid for one CLI is meaningless for another).
    """

    provider: ProviderName | None = None
    model: str | None = None


def selection_path(plot_root: Path) -> Path:
    """``<workspace>/.noory/plot/chat-provider`` — the file backing the choice."""
    return plot_root / _SELECTION_FILENAME


def read_selection(plot_root: Path) -> ChatProviderSelection:
    """Read the persisted choice. Missing file or unreadable JSON → null choice.

    We don't surface read errors to the caller — a corrupt file shouldn't
    block the panel from showing a "no selection" state; the next PUT
    overwrites it cleanly.
    """
    path = selection_path(plot_root)
    if not path.is_file():
        return ChatProviderSelection(provider=None)
    try:
        raw = path.read_text(encoding="utf-8")
        return ChatProviderSelection.model_validate_json(raw)
    except (OSError, ValueError):
        return ChatProviderSelection(provider=None)


def write_selection(plot_root: Path, selection: ChatProviderSelection) -> None:
    """Persist the choice atomically-ish (write_text is one syscall on POSIX)."""
    path = selection_path(plot_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(selection.model_dump_json(), encoding="utf-8")
