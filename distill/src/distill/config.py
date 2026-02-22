"""Configuration loader for Distill.

Config priority: project > workspace > global > defaults.
All fields optional (zero-config).
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field


class SourcesConfig(BaseModel):
    """Configuration for knowledge sources."""

    transcripts: bool = True
    rules: bool = True
    skills: bool = True
    agents: bool = False
    dirs: list[str] = Field(default_factory=list)


class RulesOutputConfig(BaseModel):
    """Configuration for rule file generation."""

    enabled: bool = True
    budget_max_files: int = 5
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    split_threshold_tokens: int = 500


class SkillsOutputConfig(BaseModel):
    """Configuration for skill file generation."""

    enabled: bool = True
    confidence_threshold: float = Field(default=0.6, ge=0.0, le=1.0)


class AgentsOutputConfig(BaseModel):
    """Configuration for agent file generation."""

    enabled: bool = False
    min_skills_to_merge: int = 3


class OutputsConfig(BaseModel):
    """Configuration for all output types."""

    rules: RulesOutputConfig = Field(default_factory=RulesOutputConfig)
    skills: SkillsOutputConfig = Field(default_factory=SkillsOutputConfig)
    agents: AgentsOutputConfig = Field(default_factory=AgentsOutputConfig)


class DistillConfig(BaseModel):
    """Distill configuration with sensible defaults."""

    extraction_model: str = "claude-haiku-4-5-20251001"
    crystallize_model: str = "claude-sonnet-4-5-20250929"
    max_transcript_chars: int = 100_000
    auto_crystallize_threshold: int = 0

    # Legacy flat fields (kept for backward compatibility)
    rule_budget_max_files: int = 5
    rule_confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)

    sources: SourcesConfig = Field(default_factory=SourcesConfig)
    outputs: OutputsConfig = Field(default_factory=OutputsConfig)


def _load_json_file(path: Path) -> dict:
    """Load a JSON config file, returning empty dict on any error."""
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def load_config(
    project_root: str | None = None,
    workspace_root: str | None = None,
) -> DistillConfig:
    """Load config with priority: project > workspace > global > defaults."""
    global_conf = _load_json_file(Path.home() / ".distill" / "config.json")

    workspace_conf: dict = {}
    if workspace_root:
        workspace_conf = _load_json_file(Path(workspace_root) / ".distill" / "config.json")

    project_conf: dict = {}
    if project_root:
        project_conf = _load_json_file(Path(project_root) / ".distill" / "config.json")

    merged = {**global_conf, **workspace_conf, **project_conf}
    return DistillConfig(**merged)
