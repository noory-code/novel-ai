"""Read existing rule files from .claude/rules/ directories."""

from __future__ import annotations

from distill.scanner import scan_environment


def read_existing_distill_rules(project_root: str | None = None) -> str | None:
    """Read all existing distill-*.md rule files from both global and project scopes.

    Returns concatenated content, or None if no rules exist.
    """
    inventory = scan_environment(project_root)
    distill_rules = [r for r in inventory.rules if r.origin == "distill"]

    if not distill_rules:
        return None

    return "\n\n".join(f"### {r.name}\n{r.content}" for r in distill_rules)


def read_all_rules(project_root: str | None = None) -> str | None:
    """Read ALL rules (distill + user) from both global and project scopes.

    Returns content with clear section labels, or None if no rules exist.
    """
    inventory = scan_environment(project_root)

    if not inventory.rules:
        return None

    user_rules = [r for r in inventory.rules if r.origin == "user"]
    distill_rules = [r for r in inventory.rules if r.origin == "distill"]

    sections: list[str] = []

    if user_rules:
        user_section = "\n\n".join(f"#### {r.name}\n{r.content}" for r in user_rules)
        sections.append(f"### User Rules\n{user_section}")

    if distill_rules:
        distill_section = "\n\n".join(f"#### {r.name}\n{r.content}" for r in distill_rules)
        sections.append(f"### Distill Rules\n{distill_section}")

    return "\n\n".join(sections)
