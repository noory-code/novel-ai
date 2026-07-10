"""recall tool — Search accumulated knowledge by hybrid semantic + keyword search."""

from __future__ import annotations

from distill.store.scope import detect_project_root, detect_workspace_root
from distill.store.types import (
    KnowledgeChunk,
    KnowledgeScope,
    KnowledgeType,
    KnowledgeVisibility,
)
from distill.tools.helpers import for_each_scope

# Ranking weights
_W_SEARCH = 0.50
_W_CONFIDENCE = 0.35
_W_ACCESS = 0.15
_ACCESS_CAP = 10  # access_count beyond this gets no additional boost


def _relevance_score(
    search_score: float, confidence: float, access_count: int
) -> float:
    """Compute combined relevance from search score, confidence, and usage."""
    access_bonus = min(access_count / _ACCESS_CAP, 1.0)
    return (
        _W_SEARCH * search_score
        + _W_CONFIDENCE * confidence
        + _W_ACCESS * access_bonus
    )


async def recall(
    query: str,
    scope: KnowledgeScope | None = None,
    knowledge_type: KnowledgeType | None = None,
    limit: int = 5,
    min_confidence: float = 0.0,
    visibility: KnowledgeVisibility | None = None,
    caller_cwd: str | None = None,
) -> str:
    """Search accumulated knowledge by hybrid semantic + keyword search."""
    max_results = min(limit, 20)
    project_root = detect_project_root(cwd=caller_cwd)
    workspace_root = detect_workspace_root(cwd=caller_cwd)
    if workspace_root == project_root:
        workspace_root = None
    results: list[tuple[KnowledgeChunk, float]] = []  # (chunk, relevance)

    async def _search(ctx):
        if not ctx.vector:
            return
        hits = ctx.vector.hybrid_search(query, max_results)
        for hit in hits:
            chunk = ctx.meta.get_by_id(hit.id)
            if not chunk:
                continue
            if knowledge_type and chunk.type != knowledge_type:
                continue
            if chunk.confidence < min_confidence:
                continue
            if visibility:
                effective_visibility = chunk.visibility or chunk.scope
                if effective_visibility != visibility:
                    continue
            ctx.meta.touch(hit.id)
            relevance = _relevance_score(
                hit.score, chunk.confidence, chunk.access_count
            )
            results.append((chunk, relevance))

    await for_each_scope(
        scope,
        project_root,
        _search,
        include_vector=True,
        workspace_root=workspace_root,
    )

    # Sort by combined relevance descending
    results.sort(key=lambda pair: pair[1], reverse=True)
    limited = results[:max_results]

    if not limited:
        return "No matching knowledge found."

    def _format_chunk(i: int, chunk: KnowledgeChunk, relevance: float) -> str:
        project_tag = f" [{chunk.project}]" if chunk.project else ""
        return (
            f"{i + 1}. [{chunk.type}]{project_tag} "
            f"({chunk.scope}, relevance: {relevance:.2f})\n"
            f"   {chunk.content}\n"
            f"   tags: {', '.join(chunk.tags)}"
        )

    formatted = "\n\n".join(
        _format_chunk(i, chunk, rel) for i, (chunk, rel) in enumerate(limited)
    )
    return formatted
