"""Show the person the proposal the engine holds, under the coach's reply.

The in-app coach records proposals from its own MCP process: a feature flow draft
(``propose_flow``) or the Services canvas service set (``propose_services``). When a turn
completes, :func:`append_proposal` adds the rendering of a proposal that turn recorded for its
scope, as a final delta and in ``turn_complete.text``, so what the person confirms is what the
engine writes (D-2026-10-11-B, D-2026-10-12-A).
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from datetime import datetime
from pathlib import Path

from mashbill.chat_providers.base import ChatStreamEvent
from mashbill.flow_proposal import reader_names as flow_reader_names
from mashbill.flow_proposal import rendering_proposed_since as flow_rendering
from mashbill.service_proposal import rendering_proposed_since as services_rendering

_log = logging.getLogger(__name__)


def _rendering(plot_root: Path, project_id: str, scope: str, since: datetime) -> str | None:
    base, separator, scope_id = scope.partition(":")
    if base == "feature" and separator and scope_id:
        return flow_rendering(plot_root, project_id, scope_id, since)
    if base in ("services", "service"):
        return services_rendering(plot_root, project_id, since)
    return None


def _proposal_block(plot_root: Path, project_id: str, scope: str, since: datetime) -> str:
    try:
        rendered = _rendering(plot_root, project_id, scope, since)
    except Exception:  # noqa: BLE001 — showing the proposal must not break the reply
        _log.exception("proposal rendering failed for %s", scope)
        return ""
    return f"\n\n```\n{rendered}\n```" if rendered else ""


def _reader_names(plot_root: Path, project_id: str, scope: str) -> dict[str, str]:
    base, separator, scope_id = scope.partition(":")
    if base != "feature" or not separator or not scope_id:
        return {}
    try:
        return flow_reader_names(plot_root, project_id, scope_id)
    except Exception:  # noqa: BLE001 — renaming draft keys must not break the reply
        _log.exception("draft key names failed for %s", scope)
        return {}


def _renamed(text: str, names: dict[str, str]) -> str:
    for key, shown in names.items():
        text = text.replace(key, shown)
    return text


async def append_proposal(
    events: AsyncIterator[ChatStreamEvent],
    plot_root: Path,
    project_id: str | None,
    scope: str,
    since: datetime,
) -> AsyncIterator[ChatStreamEvent]:
    """Pass events through; on completion append a proposal recorded since ``since``.

    A draft key the coach writes into its reply reads as what the person sees
    (O-00000137), in the streamed text and in ``turn_complete.text`` alike.
    """
    async for event in events:
        if event.type in ("delta", "turn_complete") and project_id and "[" in event.text:
            names = _reader_names(plot_root, project_id, scope)
            if names:
                event = event.model_copy(update={"text": _renamed(event.text, names)})
        if event.type == "turn_complete" and project_id:
            block = _proposal_block(plot_root, project_id, scope, since)
            if block:
                yield ChatStreamEvent(type="delta", turn_id=event.turn_id, text=block)
                event = event.model_copy(update={"text": event.text + block})
        yield event
