"""digest tool — Analyze patterns across accumulated knowledge."""

from __future__ import annotations

import logging

from distill.store.scope import detect_project_root, detect_workspace_root
from distill.tools.helpers import for_each_scope

logger = logging.getLogger(__name__)


def _simple_similarity(a: str, b: str) -> float:
    """Simple word-overlap similarity (Jaccard-like).

    Returns 0-1 where 1 = identical word sets.
    """
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    union = words_a | words_b
    if not union:
        return 0.0
    intersection = words_a & words_b
    return len(intersection) / len(union)


async def digest(caller_cwd: str | None = None) -> str:
    """Analyze patterns: find duplicates and stale entries."""
    project_root = detect_project_root(cwd=caller_cwd)
    workspace_root = detect_workspace_root(cwd=caller_cwd)
    if workspace_root == project_root:
        workspace_root = None
    report: list[str] = []

    def _analyze(ctx):
        try:
            all_entries = ctx.meta.search(scope=ctx.scope, limit=1000)

            # Find potential duplicates (simple text similarity)
            duplicates: list[str] = []
            for i in range(len(all_entries)):
                for j in range(i + 1, len(all_entries)):
                    if _simple_similarity(all_entries[i].content, all_entries[j].content) > 0.7:
                        duplicates.append(
                            f'  - "{all_entries[i].content[:50]}..." ≈ "{all_entries[j].content[:50]}..."'
                        )

            # Find low-confidence, never-accessed entries
            stale = [k for k in all_entries if k.confidence < 0.5 and k.access_count == 0]

            report.append(f"## {ctx.scope.upper()} scope ({len(all_entries)} entries)")

            if duplicates:
                report.append(
                    f"\nPotential duplicates ({len(duplicates)}):\n"
                    + "\n".join(duplicates[:5])
                )
            else:
                report.append("\nNo duplicates detected.")

            if stale:
                stale_lines = "\n".join(
                    f"  - [{k.type}] (confidence: {k.confidence}) {k.content[:60]}..."
                    for k in stale[:5]
                )
                report.append(
                    f"\nStale entries (low confidence, never accessed): {len(stale)}\n"
                    + stale_lines
                )
        except Exception:
            logger.debug("Suppressed error in _analyze", exc_info=True)
            report.append(f"## {ctx.scope.upper()} scope\n(no data yet)")

    await for_each_scope(None, project_root, _analyze, workspace_root=workspace_root)

    return "\n\n".join(report) or "No knowledge to analyze."
