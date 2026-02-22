"""profile tool — View accumulated knowledge profile and statistics."""

from __future__ import annotations

from distill.config import load_config
from distill.scanner.scanner import scan_environment
from distill.store.scope import detect_project_root, detect_workspace_root
from distill.store.types import KnowledgeScope
from distill.tools.helpers import for_each_scope


async def profile(scope: KnowledgeScope | None = None, caller_cwd: str | None = None) -> str:
    """View accumulated user knowledge profile and statistics."""
    project_root = detect_project_root(cwd=caller_cwd)
    workspace_root = detect_workspace_root(cwd=caller_cwd)
    if workspace_root == project_root:
        workspace_root = None
    sections: list[str] = []

    def _collect(ctx):
        try:
            stats = ctx.meta.stats()

            type_breakdown = "\n".join(
                f"  {k}: {v}" for k, v in stats["byType"].items()
            )

            sections.append(
                f"## {ctx.scope.upper()} scope\n"
                f"Total: {stats['total']}\n\n"
                f"By type:\n{type_breakdown or '  (empty)'}"
            )

            # Show top accessed knowledge
            top_accessed = ctx.meta.search(scope=ctx.scope, limit=5)
            if top_accessed:
                top = sorted(top_accessed, key=lambda k: k.access_count, reverse=True)[:3]
                top_lines = "\n".join(
                    f"  - [{k.type}] (accessed {k.access_count}x) {k.content[:60]}..."
                    for k in top
                )
                sections.append(f"\nMost accessed:\n{top_lines}")
        except Exception:
            sections.append(f"## {ctx.scope.upper()} scope\n(no data yet)")

    await for_each_scope(scope, project_root, _collect, workspace_root=workspace_root)

    # Environment summary
    inventory = scan_environment(project_root)
    config = load_config(project_root)
    summary = inventory.summary
    budget_used = summary.distill_rules
    budget_max = config.rule_budget_max_files
    budget_pct = round((budget_used / budget_max) * 100) if budget_max > 0 else 0

    env_lines = [
        f"Rules: {summary.total_rules} files "
        f"({summary.distill_rules} distill, {summary.user_rules} user) "
        f"— ~{summary.estimated_tokens} tokens",
    ]
    if summary.total_skills > 0:
        env_lines.append(
            f"Skills: {summary.total_skills} "
            f"({summary.distill_skills} distill, {summary.user_skills} user)"
        )
    else:
        env_lines.append("Skills: 0")
    env_lines.append(f"Agents: {summary.total_agents}")
    env_lines.append(f"Budget: {budget_used}/{budget_max} rule files used ({budget_pct}%)")

    sections.append(f"## ENVIRONMENT\n" + "\n".join(env_lines))

    return "\n\n".join(sections) or "No knowledge accumulated yet."
