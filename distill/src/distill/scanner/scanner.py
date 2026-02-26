"""Scan .claude/ directories for rules, skills, and agents."""

from __future__ import annotations

import logging
import math
from pathlib import Path

logger = logging.getLogger(__name__)

from distill.scanner.types import (
    EnvironmentInventory,
    EnvironmentItem,
    EnvironmentItemOrigin,
    EnvironmentSummary,
)


def scan_environment(project_root: str | None = None) -> EnvironmentInventory:
    """Scan .claude/ directories (global + project) and return a full environment inventory.

    Reads rules, skills, and agents. No caching — always fresh scan.
    """
    rules: list[EnvironmentItem] = []
    skills: list[EnvironmentItem] = []
    agents: list[EnvironmentItem] = []

    # Scan global scope
    global_base = Path.home() / ".claude"
    rules.extend(_scan_rules_dir(global_base / "rules"))
    skills.extend(_scan_skills_dir(global_base / "skills"))
    agents.extend(_scan_agents_dir(global_base / "agents"))

    # Scan project scope
    if project_root:
        project_base = Path(project_root) / ".claude"
        rules.extend(_scan_rules_dir(project_base / "rules"))
        skills.extend(_scan_skills_dir(project_base / "skills"))
        agents.extend(_scan_agents_dir(project_base / "agents"))

    # Compute summary
    total_chars = (
        sum(r.content.__len__() for r in rules)
        + sum(s.content.__len__() for s in skills)
        + sum(a.content.__len__() for a in agents)
    )

    distill_rules = sum(1 for r in rules if r.origin == "distill")
    user_rules = sum(1 for r in rules if r.origin == "user")
    distill_skills = sum(1 for s in skills if s.origin == "distill")
    user_skills = sum(1 for s in skills if s.origin == "user")

    return EnvironmentInventory(
        rules=rules,
        skills=skills,
        agents=agents,
        summary=EnvironmentSummary(
            total_rules=len(rules),
            distill_rules=distill_rules,
            user_rules=user_rules,
            total_skills=len(skills),
            distill_skills=distill_skills,
            user_skills=user_skills,
            total_agents=len(agents),
            estimated_tokens=math.ceil(total_chars / 4),
        ),
    )


def _scan_rules_dir(dir_path: Path) -> list[EnvironmentItem]:
    """Scan .claude/rules/ for *.md files."""
    if not dir_path.is_dir():
        return []

    items: list[EnvironmentItem] = []
    try:
        for f in sorted(dir_path.iterdir()):
            if not f.suffix == ".md":
                continue
            try:
                content = f.read_text(encoding="utf-8")
                origin: EnvironmentItemOrigin = (
                    "distill" if f.name.startswith("distill-") else "user"
                )
                items.append(
                    EnvironmentItem(
                        type="rule",
                        origin=origin,
                        name=f.name,
                        path=str(f),
                        content=content,
                    )
                )
            except OSError as exc:
                logger.debug("건너뜀 %s: %s", f, exc)
    except OSError as exc:
        logger.debug("건너뜀 %s: %s", dir_path, exc)

    return items


def _scan_skills_dir(dir_path: Path) -> list[EnvironmentItem]:
    """Scan .claude/skills/ subdirectories for SKILL.md files."""
    if not dir_path.is_dir():
        return []

    items: list[EnvironmentItem] = []
    try:
        for entry in sorted(dir_path.iterdir()):
            if not entry.is_dir():
                continue
            skill_file = entry / "SKILL.md"
            if not skill_file.exists():
                continue
            try:
                content = skill_file.read_text(encoding="utf-8")
                origin: EnvironmentItemOrigin = (
                    "distill" if entry.name.startswith("distill-") else "user"
                )
                items.append(
                    EnvironmentItem(
                        type="skill",
                        origin=origin,
                        name=entry.name,
                        path=str(skill_file),
                        content=content,
                    )
                )
            except OSError as exc:
                logger.debug("건너뜀 %s: %s", skill_file, exc)
    except OSError as exc:
        logger.debug("건너뜀 %s: %s", dir_path, exc)

    return items


def _scan_agents_dir(dir_path: Path) -> list[EnvironmentItem]:
    """Scan .claude/agents/*.yaml or *.yml files."""
    if not dir_path.is_dir():
        return []

    items: list[EnvironmentItem] = []
    try:
        for f in sorted(dir_path.iterdir()):
            if f.suffix not in (".yaml", ".yml"):
                continue
            try:
                content = f.read_text(encoding="utf-8")
                items.append(
                    EnvironmentItem(
                        type="agent",
                        origin="user",
                        name=f.name,
                        path=str(f),
                        content=content,
                    )
                )
            except OSError as exc:
                logger.debug("건너뜀 %s: %s", f, exc)
    except OSError as exc:
        logger.debug("건너뜀 %s: %s", dir_path, exc)

    return items
