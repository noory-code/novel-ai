"""Crystallize: consolidate knowledge into rules, skills, agents, or store-only entries."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from distill.config import load_config
from distill.extractor.llm_client import call_llm
from distill.extractor.prompts import CRYSTALLIZE_SYSTEM_PROMPT, build_crystallize_prompt
from distill.scanner import scan_environment
from distill.store.metadata import MetadataStore
from distill.store.scope import detect_workspace_root
from distill.store.types import KnowledgeChunk, RelationType


class SkillMetadata(BaseModel):
    """Skill metadata for procedural knowledge."""

    description: str
    when_to_use: str
    procedure: list[str]
    examples: list[str] | None = None


class AgentMetadata(BaseModel):
    """Agent metadata for workflow orchestration."""

    description: str
    skills: list[str]
    tools: list[str] = ["Bash", "Read", "Write"]


class UserConflict(BaseModel):
    """A conflict between knowledge and a user-authored rule."""

    user_rule_file: str
    conflicting_content: str
    suggestion: str


class CrystallizeResult(BaseModel):
    """A single crystallize rule group from LLM."""

    topic: str
    action: str  # "create" | "update" | "remove" | "downgrade"
    delivery: str  # "rule" | "skill" | "store" | "agent"
    rules: list[str]
    source_ids: list[str]
    existing_file: str | None = None
    skill_metadata: SkillMetadata | None = None
    agent_metadata: AgentMetadata | None = None
    user_conflicts: list[UserConflict] | None = None


class ChunkRelationResult(BaseModel):
    """A relation between two chunks extracted by the LLM during crystallize."""

    from_id: str
    to_id: str
    relation_type: str
    confidence: float = 0.8


class CrystallizeReport(BaseModel):
    """Report of what crystallize did."""

    created: list[str] = []
    updated: list[str] = []
    removed: list[str] = []
    downgraded: list[str] = []
    skills_created: list[str] = []
    agents_created: list[str] = []
    user_conflicts: list[UserConflict] = []
    relations_added: int = 0
    total_rules: int = 0


def _empty_report() -> CrystallizeReport:
    return CrystallizeReport()


_VALID_RELATION_TYPES: set[str] = {"refines", "contradicts", "depends_on", "supersedes"}


async def crystallize(
    *,
    ctx: Any,
    chunks: list[KnowledgeChunk],
    model: str,
    project_root: str | None = None,
) -> CrystallizeReport:
    """Run the crystallize pipeline: analyze chunks -> generate/update rules/skills/agents."""
    if not chunks:
        return _empty_report()

    config = load_config(project_root)

    # 1. Scan full environment based on sources config
    inventory = scan_environment(project_root)

    sections: list[str] = []
    user_rules = [r for r in inventory.rules if r.origin == "user"]
    distill_rules = [r for r in inventory.rules if r.origin == "distill"]

    if user_rules and config.sources.rules:
        user_section = "\n\n".join(f"#### {r.name}\n{r.content}" for r in user_rules)
        sections.append(f"### User Rules\n{user_section}")
    if distill_rules:
        distill_section = "\n\n".join(f"#### {r.name}\n{r.content}" for r in distill_rules)
        sections.append(f"### Distill Rules\n{distill_section}")

    # Optionally include skills context
    if config.sources.skills and inventory.skills:
        skill_names = "\n".join(f"- {s.name}" for s in inventory.skills)
        sections.append(f"### Existing Skills\n{skill_names}")

    # Optionally include agents context
    if config.sources.agents and inventory.agents:
        agent_names = "\n".join(f"- {a.name}" for a in inventory.agents)
        sections.append(f"### Existing Agents\n{agent_names}")

    existing_rules_text = "\n\n".join(sections) if sections else None

    # 2. Prepare entries for LLM
    entries = [
        {
            "id": c.id,
            "content": c.content,
            "type": c.type,
            "tags": c.tags,
            "confidence": c.confidence,
        }
        for c in chunks
    ]

    # 3. Call LLM via MCP Sampling (with Anthropic API fallback)
    outputs = config.outputs
    text = await call_llm(
        messages=[
            {
                "role": "user",
                "content": build_crystallize_prompt(
                    entries,
                    existing_rules_text,
                    confidence_threshold=outputs.rules.confidence_threshold,
                    current_rule_count=len(distill_rules),
                    rule_budget_max=outputs.rules.budget_max_files,
                    split_threshold_tokens=outputs.rules.split_threshold_tokens,
                    skills_enabled=outputs.skills.enabled,
                    agents_enabled=outputs.agents.enabled,
                    min_skills_to_merge=outputs.agents.min_skills_to_merge,
                ),
            },
        ],
        system_prompt=CRYSTALLIZE_SYSTEM_PROMPT,
        model=model,
        model_preferences={
            "hints": [{"name": model}],
            "intelligencePriority": 0.9,
        },
        ctx=ctx,
    )

    # 4. Parse results and relations
    results, relations = parse_crystallize_response(text)
    if not results:
        return _empty_report()

    # 5. Resolve output directories
    target_rules_dir = _resolve_rules_dir("project", project_root) or _resolve_rules_dir("global")
    if not target_rules_dir:
        raise RuntimeError("No rules directory available")

    target_skills_dir = _resolve_skills_dir("project", project_root) or _resolve_skills_dir("global")
    if not target_skills_dir:
        raise RuntimeError("No skills directory available")

    target_agents_dir = _resolve_agents_dir("project", project_root) or _resolve_agents_dir("global")
    if not target_agents_dir:
        raise RuntimeError("No agents directory available")

    report = _apply_delivery_actions(
        results,
        target_rules_dir,
        target_skills_dir,
        target_agents_dir,
        outputs_config=outputs,
    )

    # 6. Persist chunk relations
    if relations:
        chunk_ids = {c.id for c in chunks}
        workspace_root = detect_workspace_root(cwd=project_root)
        if workspace_root == project_root:
            workspace_root = None
        relations_added = 0
        for rel in relations:
            if rel.from_id not in chunk_ids or rel.to_id not in chunk_ids:
                continue
            if rel.relation_type not in _VALID_RELATION_TYPES:
                continue
            # Store relation in the project or global metadata store
            for scope in ("project", "workspace", "global"):
                if scope == "workspace" and not workspace_root:
                    continue
                if scope == "project" and not project_root:
                    continue
                ws_root = workspace_root if scope == "workspace" else None
                try:
                    with MetadataStore(scope, project_root, ws_root) as meta:  # type: ignore[arg-type]
                        meta.add_relation(
                            rel.from_id,
                            rel.to_id,
                            rel.relation_type,  # type: ignore[arg-type]
                            rel.confidence,
                        )
                        relations_added += 1
                        break
                except Exception:
                    continue
        report.relations_added = relations_added

    return report


def parse_crystallize_response(
    text: str,
) -> tuple[list[CrystallizeResult], list[ChunkRelationResult]]:
    """Parse and validate JSON crystallize response from LLM.

    Returns (results, relations) tuple.
    """
    json_match = re.search(r"\{[\s\S]*\}|\[[\s\S]*\]", text)
    if not json_match:
        return [], []

    try:
        parsed_raw = json.loads(json_match.group(0))

        # Support both {"results": [...], "relations": [...]} and plain [...] format
        relations_raw: list = []
        if isinstance(parsed_raw, dict):
            parsed = parsed_raw.get("results", [])
            relations_raw = parsed_raw.get("relations", [])
        else:
            parsed = parsed_raw

        if not isinstance(parsed, list):
            return [], []

        # Parse relations
        relations: list[ChunkRelationResult] = []
        for r in relations_raw:
            if not isinstance(r, dict):
                continue
            if not isinstance(r.get("from_id"), str) or not isinstance(r.get("to_id"), str):
                continue
            if r.get("relation_type") not in _VALID_RELATION_TYPES:
                continue
            relations.append(
                ChunkRelationResult(
                    from_id=r["from_id"],
                    to_id=r["to_id"],
                    relation_type=r["relation_type"],
                    confidence=float(r.get("confidence", 0.8)),
                )
            )

        results: list[CrystallizeResult] = []
        for item in parsed:
            if not isinstance(item, dict):
                continue
            if not isinstance(item.get("topic"), str):
                continue
            if item.get("action") not in ("create", "update", "remove", "downgrade"):
                continue
            if item.get("delivery") not in ("rule", "skill", "store", "agent"):
                continue
            if not isinstance(item.get("rules"), list):
                continue
            if not isinstance(item.get("source_ids"), list):
                continue

            # Validate skill_metadata when delivery === "skill"
            skill_meta = None
            if item["delivery"] == "skill":
                sm = item.get("skill_metadata")
                if (
                    not isinstance(sm, dict)
                    or not isinstance(sm.get("description"), str)
                    or not isinstance(sm.get("when_to_use"), str)
                    or not isinstance(sm.get("procedure"), list)
                ):
                    continue
                skill_meta = SkillMetadata(
                    description=sm["description"],
                    when_to_use=sm["when_to_use"],
                    procedure=sm["procedure"],
                    examples=sm.get("examples"),
                )

            # Validate agent_metadata when delivery === "agent"
            agent_meta = None
            if item["delivery"] == "agent":
                am = item.get("agent_metadata")
                if (
                    not isinstance(am, dict)
                    or not isinstance(am.get("description"), str)
                    or not isinstance(am.get("skills"), list)
                ):
                    continue
                agent_meta = AgentMetadata(
                    description=am["description"],
                    skills=am["skills"],
                    tools=am.get("tools", ["Bash", "Read", "Write"]),
                )

            # Validate and sanitize user_conflicts
            raw_conflicts = item.get("user_conflicts")
            conflicts = None
            if isinstance(raw_conflicts, list):
                valid_conflicts = []
                for c in raw_conflicts:
                    if (
                        isinstance(c, dict)
                        and isinstance(c.get("user_rule_file"), str)
                        and isinstance(c.get("conflicting_content"), str)
                        and isinstance(c.get("suggestion"), str)
                    ):
                        valid_conflicts.append(
                            UserConflict(
                                user_rule_file=c["user_rule_file"],
                                conflicting_content=c["conflicting_content"],
                                suggestion=c["suggestion"],
                            )
                        )
                if valid_conflicts:
                    conflicts = valid_conflicts

            results.append(
                CrystallizeResult(
                    topic=item["topic"],
                    action=item["action"],
                    delivery=item["delivery"],
                    rules=item["rules"],
                    source_ids=item["source_ids"],
                    existing_file=item.get("existing_file"),
                    skill_metadata=skill_meta,
                    agent_metadata=agent_meta,
                    user_conflicts=conflicts,
                )
            )

        return results, relations
    except (json.JSONDecodeError, ValueError):
        return [], []


def _resolve_rules_dir(scope: str, project_root: str | None = None) -> str | None:
    if scope == "global":
        return str(Path.home() / ".claude" / "rules")
    if project_root:
        return str(Path(project_root) / ".claude" / "rules")
    return None


def _resolve_skills_dir(scope: str, project_root: str | None = None) -> str | None:
    if scope == "global":
        return str(Path.home() / ".claude" / "skills")
    if project_root:
        return str(Path(project_root) / ".claude" / "skills")
    return None


def _resolve_agents_dir(scope: str, project_root: str | None = None) -> str | None:
    if scope == "global":
        return str(Path.home() / ".claude" / "agents")
    if project_root:
        return str(Path(project_root) / ".claude" / "agents")
    return None


def _write_rule_file(
    rules_dir: str,
    topic: str,
    rules: list[str],
    source_ids: list[str],
) -> str:
    """Write a rule file in the standard Distill format."""
    os.makedirs(rules_dir, exist_ok=True)
    filename = f"distill-{topic}.md"
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    content = (
        f"# {topic}\n"
        f"> Auto-generated by Distill from {len(source_ids)} decisions (last updated: {date})\n\n"
        + "\n".join(f"- {r}" for r in rules)
        + "\n\n## Sources\n"
        + "\n".join(f"- {sid}" for sid in source_ids)
        + "\n"
    )

    with open(os.path.join(rules_dir, filename), "w", encoding="utf-8") as f:
        f.write(content)
    return filename


def _write_skill_file(
    skills_dir: str,
    topic: str,
    metadata: SkillMetadata,
    rules: list[str],
    source_ids: list[str],
) -> str:
    """Write a skill file in Claude Code SKILL.md format."""
    skill_dir_name = f"distill-{topic}"
    skill_dir = os.path.join(skills_dir, skill_dir_name)
    os.makedirs(skill_dir, exist_ok=True)

    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    examples_section = ""
    if metadata.examples:
        examples_section = "\n\n## Examples\n\n" + "\n".join(
            f'- "{ex}"' for ex in metadata.examples
        )

    procedure_text = "\n".join(
        f"{i + 1}. {step}" for i, step in enumerate(metadata.procedure)
    )

    content = (
        f"---\ndisable-model-invocation: true\n---\n\n"
        f"# {topic}\n\n"
        f"> Auto-generated by Distill from {len(source_ids)} decisions (last updated: {date})\n\n"
        f"## Description\n\n{metadata.description}\n\n"
        f"## When to Use\n\n{metadata.when_to_use}\n\n"
        f"## Procedure\n\n{procedure_text}{examples_section}\n\n"
        f"## Context\n\n"
        + "\n".join(f"- {r}" for r in rules)
        + "\n\n## Sources\n\n"
        + "\n".join(f"- {sid}" for sid in source_ids)
        + "\n"
    )

    with open(os.path.join(skill_dir, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write(content)
    return skill_dir_name


def _write_agent_file(
    agents_dir: str,
    topic: str,
    metadata: AgentMetadata,
) -> str:
    """Write an agent file in Claude Code agents format."""
    os.makedirs(agents_dir, exist_ok=True)
    filename = f"distill-{topic}.md"
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    tools_str = ", ".join(metadata.tools)
    skills_list = "\n".join(f"- {s}" for s in metadata.skills)

    content = (
        f"---\n"
        f"name: distill-{topic}\n"
        f"description: {metadata.description}\n"
        f"tools: [{tools_str}]\n"
        f"---\n\n"
        f"# {topic} (Auto-generated by Distill, {date})\n\n"
        f"{metadata.description}\n\n"
        f"## Skills Used\n\n"
        f"{skills_list}\n"
    )

    with open(os.path.join(agents_dir, filename), "w", encoding="utf-8") as f:
        f.write(content)
    return filename


def _apply_delivery_actions(
    results: list[CrystallizeResult],
    rules_dir: str,
    skills_dir: str,
    agents_dir: str,
    outputs_config: Any = None,
) -> CrystallizeReport:
    """Apply delivery actions — write files based on delivery mechanism."""
    from distill.config import OutputsConfig
    if outputs_config is None:
        outputs_config = OutputsConfig()

    report = CrystallizeReport()

    for result in results:
        # Collect user conflicts
        if result.user_conflicts:
            report.user_conflicts.extend(result.user_conflicts)

        # Handle remove and downgrade actions
        if result.action in ("remove", "downgrade"):
            file_name = result.existing_file or f"distill-{result.topic}.md"
            file_path = os.path.join(rules_dir, file_name)
            if os.path.exists(file_path):
                os.unlink(file_path)
                if result.action == "remove":
                    report.removed.append(os.path.basename(file_path))
                else:
                    report.downgraded.append(os.path.basename(file_path))
            continue

        # Route by delivery mechanism
        if result.delivery == "skill" and outputs_config.skills.enabled:
            if not result.skill_metadata:
                continue
            skill_dir_name = _write_skill_file(
                skills_dir,
                result.topic,
                result.skill_metadata,
                result.rules,
                result.source_ids,
            )
            report.skills_created.append(skill_dir_name)
            report.total_rules += len(result.rules)

        elif result.delivery == "agent" and outputs_config.agents.enabled:
            if not result.agent_metadata:
                continue
            agent_filename = _write_agent_file(
                agents_dir,
                result.topic,
                result.agent_metadata,
            )
            report.agents_created.append(agent_filename)

        elif result.delivery == "rule" and outputs_config.rules.enabled:
            filename = _write_rule_file(
                rules_dir,
                result.topic,
                result.rules,
                result.source_ids,
            )
            if result.action == "create":
                report.created.append(filename)
            else:
                report.updated.append(filename)
            report.total_rules += len(result.rules)
        # delivery === "store" or disabled: no file output

    return report
