"""store tool — Save pre-extracted knowledge chunks directly (no LLM required).

Used by `claude -p` subprocess in hooks and by external agents that extract
knowledge themselves and call this tool to persist it.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path

from distill.extractor.extractor import parse_extraction_response
from distill.store.metadata import MetadataStore
from distill.store.scope import detect_project_root, detect_workspace_root
from distill.store.types import ExtractionTrigger, KnowledgeInput, KnowledgeScope, KnowledgeSource
from distill.store.vector import VectorStore

logger = logging.getLogger(__name__)

_VALID_TRIGGERS = {"pre_compact", "session_end", "manual", "ingest"}


async def store(
    chunks: list[dict],
    session_id: str,
    trigger: str = "manual",
    scope: KnowledgeScope | None = None,
    caller_cwd: str | None = None,
    _project_root: str | None = None,
) -> str:
    """Save pre-extracted knowledge chunks to the knowledge store.

    Used by the distill-learn agent to persist knowledge extracted by Claude
    without requiring an API key.

    Args:
        chunks: List of knowledge dicts with keys: content, type, scope, tags, confidence.
        session_id: Session identifier for provenance tracking.
        trigger: Source trigger — "manual", "pre_compact", "session_end", or "ingest".
        scope: Override storage scope. Defaults to each chunk's own scope.
        caller_cwd: Caller's working directory for project root detection.
        _project_root: Override project root (for testing).
    """
    project_root = _project_root or detect_project_root(cwd=caller_cwd)
    workspace_root = detect_workspace_root(cwd=caller_cwd)
    if workspace_root == project_root:
        workspace_root = None

    # Validate trigger
    effective_trigger: ExtractionTrigger = (
        trigger if trigger in _VALID_TRIGGERS else "manual"
    )  # type: ignore[assignment]

    # Validate chunks using existing parser
    valid_items = parse_extraction_response(
        "[" + ", ".join(
            __import__("json").dumps(c) for c in chunks if isinstance(c, dict)
        ) + "]"
    )

    if not valid_items:
        return (
            "No valid knowledge chunks to store. Expected: "
            "[{content, type, scope, tags, confidence}, ...]"
        )

    now = datetime.now(UTC).isoformat()
    source = KnowledgeSource(
        session_id=session_id,
        timestamp=now,
        trigger=effective_trigger,
    )

    saved = 0
    conflict_warnings: list[str] = []

    for item in valid_items:
        effective_scope: KnowledgeScope = scope or item.get(
            "scope", "project"
        )  # type: ignore[assignment]
        ws_root = workspace_root if effective_scope == "workspace" else None

        chunk_input = KnowledgeInput(
            content=item["content"],
            type=item["type"],
            scope=effective_scope,
            tags=item.get("tags", []),
            source=source,
            confidence=float(item.get("confidence", 0.7)),
            project=Path(project_root).name if project_root else None,
        )

        try:
            with (
                MetadataStore(effective_scope, project_root, ws_root) as meta,
                VectorStore(effective_scope, project_root, ws_root) as vector,
            ):
                inserted = meta.insert(chunk_input)
                vector.index(inserted.id, inserted.content, inserted.tags)

                if chunk_input.type == "conflict":
                    conflict_warnings.append(
                        f"  ⚠ CONFLICT: {chunk_input.content[:100]}"
                    )

                saved += 1
        except Exception:
            pass

    summary = "\n".join(
        f"- [{item['type']}] {item['content'][:80]}"
        f"{'...' if len(item['content']) > 80 else ''}"
        for item in valid_items
    )

    lines = [f"Stored {saved}/{len(valid_items)} knowledge chunks."]

    if conflict_warnings:
        lines.append("")
        lines.append("Rule conflicts detected:")
        lines.extend(conflict_warnings)

    lines.append("")
    lines.append(summary)

    return "\n".join(lines)
