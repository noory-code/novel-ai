"""Recover concrete coach proposals that were not recorded during the turn."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import get_args

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from mashbill.canvas_io import read_canvas
from mashbill.chat_providers.base import ChatProvider
from mashbill.draft_store import list_drafts, record_extracted_draft
from mashbill.models_canvas import CanvasKind
from mashbill.models_kinds import NodeKind

DRAFT_EXTRACTION_KNOWN_CAP = 30
DRAFT_EXTRACTION_TIMEOUT_SECONDS = 60.0
_NODE_KINDS: frozenset[str] = frozenset(get_args(NodeKind))
_NODE_KIND_OPTIONS = ", ".join(get_args(NodeKind))

DRAFT_EXTRACTION_PROMPT = f"""You extract unrecorded design drafts from one coach reply.

A draft is concrete text ready to place in a canvas node, or a concrete new node proposal that
includes its name. Include it even when it is phrased as a question. Do not include a question
that only asks for direction and contains no concrete proposed text.

Return only a JSON array. Each item must have:
- proposed_text: the exact concrete proposal, preserving its language
- rationale: one short reason it qualifies as a draft
It may also have:
- proposed_kind: only when proposing a new node, and only one of: {_NODE_KIND_OPTIONS}
- target_node_ids: ids chosen only from the supplied canvas nodes

Exclude proposals represented by any existing draft, including rejected drafts. A coach repeating
an earlier proposal or referring to a rejected proposal is not a new proposal. Do not use tools,
do not add commentary, and return [] when there is nothing new.
"""

_log = logging.getLogger(__name__)


class ExtractedProposal(BaseModel):
    """One validated item returned by the isolated extraction call."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    proposed_text: str = Field(min_length=1)
    proposed_kind: str | None = None
    target_node_ids: list[str] = Field(default_factory=list)
    rationale: str = Field(min_length=1)


def build_draft_extraction_prompt(
    coach_reply: str,
    existing_drafts: list[dict[str, str]],
    canvas_nodes: list[dict[str, str]],
) -> str:
    """Attach the turn facts as JSON so either provider sees the same input."""
    payload = {
        "coach_reply": coach_reply,
        "existing_drafts": existing_drafts,
        "canvas_nodes": canvas_nodes,
    }
    return f"{DRAFT_EXTRACTION_PROMPT}\nInput:\n{json.dumps(payload, ensure_ascii=False)}"


async def extract_turn_drafts(
    provider: ChatProvider,
    plot_root: Path,
    project_id: str,
    scope: str,
    coach_reply: str,
    turn_started_at: str,
    *,
    model: str | None = None,
) -> int:
    """Run isolated proposal extraction and persist valid, non-duplicate results.

    Every failure stays inside this background boundary. The completed chat turn has
    already been streamed and persisted before this coroutine is scheduled.
    """
    target = _target_for_scope(scope)
    if target is None:
        return 0
    canvas_kind, service_id = target
    try:
        scope_drafts = [
            draft
            for draft in list_drafts(plot_root, project_id)
            if draft.chat_scope == scope
        ]
        known_drafts = scope_drafts[:DRAFT_EXTRACTION_KNOWN_CAP]
        known_ids = {draft.id for draft in known_drafts}
        known_drafts.extend(
            draft
            for draft in scope_drafts
            if draft.created >= turn_started_at and draft.id not in known_ids
        )
        nodes = _canvas_nodes(plot_root, project_id, canvas_kind, service_id)
        prompt = build_draft_extraction_prompt(
            coach_reply,
            [
                {"text": draft.proposed_text, "status": draft.status}
                for draft in known_drafts
            ],
            nodes,
        )
        raw = await asyncio.wait_for(
            provider.complete_once(prompt, model=model),
            timeout=DRAFT_EXTRACTION_TIMEOUT_SECONDS,
        )
        proposals = _parse_proposals(raw)
        if proposals is None:
            _log.warning("chat draft extraction returned invalid JSON for %s", plot_root)
            return 0

        known_node_ids = {node["id"] for node in nodes}
        seen = {draft.proposed_text.strip().casefold() for draft in known_drafts}
        persisted_count = 0
        for proposal in proposals:
            normalized = proposal.proposed_text.strip().casefold()
            if normalized in seen:
                continue
            seen.add(normalized)
            record_extracted_draft(
                plot_root,
                project_id,
                canvas_kind,
                proposal.proposed_text,
                proposal.rationale,
                scope,
                [node_id for node_id in proposal.target_node_ids if node_id in known_node_ids],
                proposal.proposed_kind if proposal.proposed_kind in _NODE_KINDS else None,
                service_id,
            )
            persisted_count += 1
        return persisted_count
    except TimeoutError:
        _log.warning("chat draft extraction timed out for %s", plot_root)
        return 0
    except Exception:  # noqa: BLE001 — extraction must never affect the chat turn
        _log.exception("chat draft extraction failed for %s", plot_root)
        return 0


def _parse_proposals(raw: str) -> list[ExtractedProposal] | None:
    try:
        payload = json.loads(raw)
        if not isinstance(payload, list):
            return None
        return [ExtractedProposal.model_validate(item) for item in payload]
    except (json.JSONDecodeError, TypeError, ValidationError):
        return None


def _target_for_scope(scope: str) -> tuple[CanvasKind, str | None] | None:
    base, _, instance_id = scope.partition(":")
    if base == "service":
        return ("services", None)
    if base == "feature" and instance_id:
        return ("feature", instance_id)
    if base in {"foundation", "actors", "services", "entities"} and not instance_id:
        return (base, None)  # type: ignore[return-value]
    return None


def _canvas_nodes(
    plot_root: Path,
    project_id: str,
    canvas_kind: CanvasKind,
    service_id: str | None,
) -> list[dict[str, str]]:
    canvas = read_canvas(plot_root, project_id, canvas_kind, service_id)
    return [{"id": node.id, "name": node.label} for node in canvas.nodes]
