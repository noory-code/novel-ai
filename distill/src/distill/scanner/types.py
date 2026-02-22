"""Types for .claude/ environment scanning."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

EnvironmentItemOrigin = Literal["distill", "user"]
EnvironmentItemType = Literal["rule", "skill", "agent"]


class EnvironmentItem(BaseModel):
    """A single item discovered in the .claude/ environment."""

    type: EnvironmentItemType
    origin: EnvironmentItemOrigin
    name: str
    path: str
    content: str


class EnvironmentSummary(BaseModel):
    """Aggregated counts from scanning."""

    total_rules: int = 0
    distill_rules: int = 0
    user_rules: int = 0
    total_skills: int = 0
    distill_skills: int = 0
    user_skills: int = 0
    total_agents: int = 0
    estimated_tokens: int = 0


class EnvironmentInventory(BaseModel):
    """Full inventory from scanning .claude/ directories."""

    rules: list[EnvironmentItem] = []
    skills: list[EnvironmentItem] = []
    agents: list[EnvironmentItem] = []
    summary: EnvironmentSummary = EnvironmentSummary()
