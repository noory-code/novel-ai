"""Core type definitions for Distill knowledge store."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

KnowledgeType = Literal[
    "pattern", "preference", "decision", "mistake", "workaround", "conflict"
]

KnowledgeScope = Literal["global", "project", "workspace"]

# Semantic visibility: where this chunk applies, independent of storage location.
# - "global": applies everywhere
# - "workspace": applies within the monorepo workspace
# - "project": applies only within this project
# - "private": personal only, excluded from team sharing
KnowledgeVisibility = Literal["global", "workspace", "project", "private"]

ExtractionTrigger = Literal["pre_compact", "session_end", "manual", "ingest"]

# Lifecycle event types for tracking chunk state transitions.
LifecycleEventType = Literal["created", "promoted", "demoted", "crystallized", "deleted"]

# Relationship types between knowledge chunks.
RelationType = Literal["refines", "contradicts", "depends_on", "supersedes"]


class KnowledgeSource(BaseModel):
    session_id: str
    timestamp: str
    trigger: ExtractionTrigger


class LifecycleEvent(BaseModel):
    """A single state transition event in a chunk's lifecycle."""

    chunk_id: str
    event_type: LifecycleEventType
    from_scope: KnowledgeScope | None = None
    to_scope: KnowledgeScope | None = None
    timestamp: str
    note: str | None = None


class ChunkRelation(BaseModel):
    """A directional relationship between two knowledge chunks."""

    from_id: str
    to_id: str
    relation_type: RelationType
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    created_at: str


class KnowledgeChunk(BaseModel):
    """A single knowledge chunk extracted from conversation."""

    id: str
    content: str
    type: KnowledgeType
    scope: KnowledgeScope
    visibility: KnowledgeVisibility | None = None  # defaults to scope value if None
    project: str | None = None
    tags: list[str]
    source: KnowledgeSource
    confidence: float = Field(ge=0.0, le=1.0)
    access_count: int = 0
    created_at: str
    updated_at: str
    last_accessed_at: str | None = None


class KnowledgeInput(BaseModel):
    """Input for creating a new knowledge chunk (before ID/timestamps)."""

    content: str
    type: KnowledgeType
    scope: KnowledgeScope
    visibility: KnowledgeVisibility | None = None  # defaults to scope value if None
    project: str | None = None
    tags: list[str]
    source: KnowledgeSource
    confidence: float = Field(ge=0.0, le=1.0)
