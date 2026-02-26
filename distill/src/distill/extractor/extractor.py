"""Knowledge extraction from conversation transcripts via MCP Sampling."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from distill.config import load_config
from distill.extractor.parser import ConversationTurn, format_transcript, parse_transcript
from distill.extractor.llm_client import call_llm as _call_llm
from distill.extractor.prompts import EXTRACTION_SYSTEM_PROMPT, build_extraction_prompt
from distill.extractor.rules_reader import read_all_rules
from distill.store.types import ExtractionTrigger, KnowledgeInput, KnowledgeScope, KnowledgeSource

VALID_TYPES = {"pattern", "preference", "decision", "mistake", "workaround", "conflict"}
VALID_SCOPES = {"global", "project", "workspace"}


async def extract_knowledge(
    *,
    ctx: Any,
    transcript_path: str,
    session_id: str,
    trigger: ExtractionTrigger,
    project_name: str | None = None,
    scope_override: KnowledgeScope | None = None,
    project_root: str | None = None,
) -> list[KnowledgeInput]:
    """Extract knowledge from a .jsonl transcript file.

    Uses MCP sampling to request LLM completion from the client (Claude Code).
    """
    config = load_config(project_root)

    # 1. Parse transcript
    turns = parse_transcript(transcript_path)
    if len(turns) < 2:
        return []  # need at least 1 exchange

    # 2. Format and truncate
    formatted = format_transcript(turns)
    if len(formatted) > config.max_transcript_chars:
        # max_transcript_chars\ub294 \ubb38\uc790 \uc218\uc774\uc9c0 \ud1a0\ud070 \uc218\uac00 \uc544\ub2d9\ub2c8\ub2e4.
        # \ub2e4\uad6d\uc5b4 \ucf58\ud150\uce20(\ud55c\uad6d\uc5b4/\uc911\uad6d\uc5b4/\uc77c\ubcf8\uc5b4)\uc758 \uacbd\uc6b0 \uc2e4\uc81c \ud1a0\ud070 \uc18c\ube44\ub7c9\uc774
        # 2-3\ubc30 \ub354 \ub192\uc744 \uc218 \uc788\uc2b5\ub2c8\ub2e4. \ucee8\ud14d\uc2a4\ud2b8 \uc708\ub3c4\uc6b0 \uc624\ub958\uac00 \ubc1c\uc0dd\ud558\uba74
        # max_transcript_chars\ub97c \uc904\uc774\uc138\uc694.
        formatted = formatted[:config.max_transcript_chars]
        last_newline = formatted.rfind("\n")
        if last_newline > 0:
            formatted = formatted[:last_newline]

    # 3. Read all rules (user + distill) for conflict detection
    existing_rules = read_all_rules(project_root)

    # 4. Call LLM via MCP sampling
    raw = await call_llm(ctx, formatted, config.extraction_model, project_name, existing_rules)
    if not raw:
        return []

    # 5. Convert to KnowledgeInput
    now = datetime.now(timezone.utc).isoformat()
    return [
        KnowledgeInput(
            content=r["content"],
            type=r["type"],
            scope=scope_override or r["scope"],
            project=project_name,
            tags=r["tags"],
            source=KnowledgeSource(
                session_id=session_id,
                timestamp=now,
                trigger=trigger,
            ),
            confidence=r["confidence"],
        )
        for r in raw
    ]


async def call_llm(
    ctx: Any,
    formatted_transcript: str,
    model: str,
    project_name: str | None = None,
    existing_rules: str | None = None,
) -> list[dict]:
    """LLM call via MCP Sampling."""
    text = await _call_llm(
        messages=[
            {
                "role": "user",
                "content": build_extraction_prompt(formatted_transcript, project_name, existing_rules),
            },
        ],
        system_prompt=EXTRACTION_SYSTEM_PROMPT,
        model=model,
        model_preferences={
            "hints": [{"name": model}],
            "costPriority": 0.8,
            "speedPriority": 0.8,
        },
        ctx=ctx,
    )
    return parse_extraction_response(text)


def parse_extraction_response(text: str) -> list[dict]:
    """Parse and validate JSON extraction response from LLM."""
    json_match = re.search(r"\[[\s\S]*\]", text)
    if not json_match:
        return []

    try:
        parsed = json.loads(json_match.group(0))
        if not isinstance(parsed, list):
            return []

        return [
            item
            for item in parsed
            if (
                isinstance(item, dict)
                and isinstance(item.get("content"), str)
                and item.get("type") in VALID_TYPES
                and item.get("scope") in VALID_SCOPES
                and isinstance(item.get("tags"), list)
                and isinstance(item.get("confidence"), (int, float))
                and 0 <= item["confidence"] <= 1
            )
        ]
    except (json.JSONDecodeError, ValueError):
        return []


def _truncate_to_recent(turns: list[ConversationTurn], max_chars: int) -> str:
    """Truncate transcript to fit within char limit, keeping recent turns."""
    result: list[ConversationTurn] = []
    total = 0

    for turn in reversed(turns):
        entry = f"[{turn.role.upper()}]\n{turn.text}\n\n---\n\n"
        if total + len(entry) > max_chars:
            break
        total += len(entry)
        result.insert(0, turn)

    return format_transcript(result)
