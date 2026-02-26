"""Test data factories."""

from __future__ import annotations

from datetime import UTC, datetime

from distill.store.types import KnowledgeChunk, KnowledgeInput, KnowledgeSource


def make_knowledge_input(**overrides) -> KnowledgeInput:
    defaults = {
        "content": "Default test content",
        "type": "pattern",
        "scope": "project",
        "project": "test-project",
        "tags": ["test"],
        "source": KnowledgeSource(
            session_id="test-session-001",
            timestamp=datetime.now(UTC).isoformat(),
            trigger="manual",
        ),
        "confidence": 0.8,
    }
    defaults.update(overrides)
    return KnowledgeInput(**defaults)


def make_knowledge_chunk(**overrides) -> KnowledgeChunk:
    now = datetime.now(UTC).isoformat()
    defaults = {
        "id": "test-id-001",
        "access_count": 0,
        "created_at": now,
        "updated_at": now,
        **make_knowledge_input().model_dump(),
    }
    defaults.update(overrides)
    return KnowledgeChunk(**defaults)
