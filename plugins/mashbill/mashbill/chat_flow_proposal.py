"""Show the person the flow draft the engine holds, under the coach's reply.

The in-app coach records a flow draft with ``propose_flow`` from its own MCP
process. When a feature-scope turn completes, :func:`append_flow_proposal` adds
the rendering of a proposal recorded during that turn to the reply, as a final
delta and in ``turn_complete.text``, so the draft the person confirms is the one
``draw_proposed_flow`` draws (D-2026-10-11-B).
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from datetime import datetime
from pathlib import Path

from mashbill.chat_providers.base import ChatStreamEvent
from mashbill.flow_proposal import rendering_proposed_since

_log = logging.getLogger(__name__)


def _proposal_block(plot_root: Path, project_id: str, scope: str, since: datetime) -> str:
    base, separator, feature_id = scope.partition(":")
    if base != "feature" or not separator or not feature_id:
        return ""
    try:
        rendered = rendering_proposed_since(plot_root, project_id, feature_id, since)
    except Exception:  # noqa: BLE001 — showing the draft must not break the reply
        _log.exception("flow proposal rendering failed for %s", scope)
        return ""
    return f"\n\n```\n{rendered}\n```" if rendered else ""


async def append_flow_proposal(
    events: AsyncIterator[ChatStreamEvent],
    plot_root: Path,
    project_id: str | None,
    scope: str,
    since: datetime,
) -> AsyncIterator[ChatStreamEvent]:
    """Pass events through; on completion append a flow proposal recorded since ``since``."""
    async for event in events:
        if event.type == "turn_complete" and project_id:
            block = _proposal_block(plot_root, project_id, scope, since)
            if block:
                yield ChatStreamEvent(type="delta", turn_id=event.turn_id, text=block)
                event = event.model_copy(update={"text": event.text + block})
        yield event
