"""Typed models for the Solera workspace graph.

Every field parsed out of `.solera/` markdown files lands in one of the
`Living`, `Time-bound`, or `Immutable` axis models here. The `Graph`
aggregate is what HTTP endpoints and MCP tools return to clients.

Models live in their own module (separate from :mod:`solera_mcp.readers`)
so that downstream callers (tests, the HTTP layer, the MCP tools) can
import types without pulling in the file-system I/O transitively.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ConceptStatus = Literal["active", "deprecated", "archived"]
"""Status grammar shared by every Living-axis item: Concept, Persona, Journey, Narrative."""

MilestoneStatus = Literal["proposed", "agreed", "in-progress", "released"]
WorkStatus = Literal["pending", "in_progress", "complete", "on_hold", "cancelled"]
NarrativeForm = Literal["user_story", "jtbd", "scenario"]

STATUS_ICON_MAP: dict[str, WorkStatus] = {
    "⏳": "pending",
    "🔄": "in_progress",
    "✅": "complete",
    "⏸️": "on_hold",
    "❌": "cancelled",
}


class Concept(BaseModel):
    id: str
    name: str
    status: ConceptStatus
    intent: str
    current_design: str
    current_shape: str
    horizon: str | None = None
    parent: str | None = None  # Concept ID of the containing Concept; None = top-level surface


class Persona(BaseModel):
    """Living-axis service composer. Upstream of Concepts."""

    id: str
    name: str
    status: ConceptStatus
    identity: str  # the opening paragraph
    goals: list[str] = Field(default_factory=list)
    pains: list[str] = Field(default_factory=list)
    triggers: list[str] = Field(default_factory=list)
    quotes: list[str] = Field(default_factory=list)
    channels: str | None = None
    parent: str | None = None  # Persona ID of the containing Persona; None = top-level


class JourneyStep(BaseModel):
    """One row of a Journey's Steps table.

    Steps live in the table inside `# Steps`, not as separate files — they are
    read-mostly artifacts surfaced as swimlane cells in the Service canvas.
    """

    n: int
    stage: str
    step: str
    touchpoint: str
    emotion: str
    pain: str


class Journey(BaseModel):
    """Living-axis sequence of steps a Persona walks. Walked by exactly one Persona."""

    id: str
    name: str
    status: ConceptStatus
    walks: str  # Persona ID, required
    trigger: str
    steps: list[JourneyStep] = Field(default_factory=list)
    outcome: str
    parent: str | None = None  # Journey ID; None = top-level
    integrity: list[str] = Field(default_factory=list)
    """Data-integrity flags surfaced to the canvas so the human can repair the file.

    Canonical values: ``missing_walks`` (no ``walks`` Persona id in frontmatter).
    Future passes may add ``broken_walks_ref`` / ``inactive_walks_ref``.
    """


class Narrative(BaseModel):
    """Living-axis "As a / I want / so that" statement (or JTBD / scenario).

    Distinct from Solera's Time-bound `Story` work item — a Narrative is upstream
    of Concepts and may `proposes:` Concepts via the Service canvas action (which
    creates a stub Concept whose Intent is flagged "needs human review").
    """

    id: str
    form: NarrativeForm
    status: ConceptStatus
    statement: str
    context: str
    acceptance_cues: list[str] = Field(default_factory=list)
    about: list[str] = Field(default_factory=list)  # Persona IDs, 1+
    in_journey: str | None = None  # Journey ID, optional
    proposes: list[str] = Field(default_factory=list)  # Concept IDs, populated by canvas action
    integrity: list[str] = Field(default_factory=list)
    """Data-integrity flags surfaced to the canvas so the human can repair the file.

    Canonical values: ``missing_about`` (``about`` list empty — spec requires 1+),
    ``broken_in_journey_ref`` (``in_journey`` references a Journey not present in
    the graph). Set during :func:`solera_mcp.graph.build_graph`'s integrity pass.
    """


class ConceptEdge(BaseModel):
    """Concept ↔ Concept relation. Free-text label by design (per plan)."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    from_id: str = Field(alias="from")
    to_id: str = Field(alias="to")
    label: str
    created: str | None = None


class Story(BaseModel):
    id: str
    name: str
    story_type: str  # US / TS
    status: WorkStatus
    contributes_to: list[str] = Field(default_factory=list)
    belongs_to: str | None = None


class ActionItem(BaseModel):
    story_id: str
    id: str
    name: str
    status: WorkStatus
    depends_on: list[str] = Field(default_factory=list)


class Milestone(BaseModel):
    id: str
    name: str
    status: MilestoneStatus
    scope: list[str] = Field(default_factory=list)


class Identity(BaseModel):
    mission: str | None = None
    vision: str | None = None
    values: str | None = None
    goals: str | None = None
    tone_and_manner: str | None = None
    # Any other `identity/*.md` files we don't recognize above are
    # surfaced here keyed by filename stem (e.g., "brand-voice").
    extras: dict[str, str] = Field(default_factory=dict)


class Release(BaseModel):
    tag: str
    milestone_id: str | None = None
    released_at: str | None = None


class Graph(BaseModel):
    identity: Identity | None = None
    personas: list[Persona] = Field(default_factory=list)
    journeys: list[Journey] = Field(default_factory=list)
    narratives: list[Narrative] = Field(default_factory=list)
    concepts: list[Concept] = Field(default_factory=list)
    concept_edges: list[ConceptEdge] = Field(default_factory=list)
    milestones: list[Milestone] = Field(default_factory=list)
    stories: list[Story] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)
    releases: list[Release] = Field(default_factory=list)
