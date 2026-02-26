"""recall tool — Search accumulated knowledge by semantic similarity."""

from __future__ import annotations

from distill.store.scope import detect_project_root, detect_workspace_root
from distill.store.types import KnowledgeChunk, KnowledgeScope, KnowledgeType, KnowledgeVisibility
from distill.tools.helpers import for_each_scope


async def recall(
    query: str,
    scope: KnowledgeScope | None = None,
    knowledge_type: KnowledgeType | None = None,
    limit: int = 5,
    min_confidence: float = 0.0,
    visibility: KnowledgeVisibility | None = None,
    caller_cwd: str | None = None,
) -> str:
    """Search accumulated knowledge by semantic similarity."""
    max_results = min(limit, 20)
    project_root = detect_project_root(cwd=caller_cwd)
    workspace_root = detect_workspace_root(cwd=caller_cwd)
    if workspace_root == project_root:
        workspace_root = None
    results: list[KnowledgeChunk] = []

    async def _search(ctx):
        if not ctx.vector:
            return
        hits = ctx.vector.search(query, max_results)
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
            results.append(chunk)

    await for_each_scope(
        scope,
        project_root,
        _search,
        include_vector=True,
        workspace_root=workspace_root,
    )

    # Sort by confidence descending
    results.sort(key=lambda k: k.confidence, reverse=True)
    limited = results[:max_results]

    if not limited:
        return "No matching knowledge found."

    def _format_chunk(i: int, k: KnowledgeChunk) -> str:
        project_tag = f" [{k.project}]" if k.project else ""
        return (
            f"{i + 1}. [{k.type}]{project_tag} "
            f"({k.scope}, confidence: {k.confidence})\n"
            f"   {k.content}\n"
            f"   tags: {', '.join(k.tags)}"
        )

    formatted = "\n\n".join(_format_chunk(i, k) for i, k in enumerate(limited))
    return formatted
