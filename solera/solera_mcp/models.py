"""Typed models for the Solera workspace graph.

Every field parsed out of the Solera workspace markdown files (under
`.noory/solera/` after R9, or a legacy `.solera/`) lands in one of the
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
"""Status grammar shared by every Living-axis item: Role, Concept, Persona, Journey, Narrative."""

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


class Role(BaseModel):
    """Living-axis structural user class (e.g. ``admin``, ``fan``, ``hero``).

    Introduced in v5.0 to separate *structural* audience description from the
    individual archetype description that :class:`Persona` already covered.
    Whereas a Persona is a named, concrete caricature with goals/pains/quotes,
    a Role is the Role itself — the position someone occupies when they use
    the service. Roles form the **primary tree** around a project's Identity
    on the Actors canvas; Personas (if any) hang off a specific Role as
    optional archetype examples.
    """

    id: str
    name: str
    status: ConceptStatus
    description: str  # one-paragraph "who this Role is"
    context: str | None = None  # when/where this Role shows up (optional)
    parent: str | None = None  # Role ID (sub-role chain); None = top-level
    integrity: list[str] = Field(default_factory=list)
    """Data-integrity flags: ``broken_parent_ref``, ``inactive_parent_ref``."""


class Persona(BaseModel):
    """Living-axis individual archetype of a :class:`Role`.

    As of v5.0 every Persona must belong to a Role (``role`` required). The
    Persona captures the concrete texture — "30대 성덕 Alice who streams every
    live" — that a Role alone can't express. A Role can exist with no
    Personas (most early-stage projects); adding Personas is what deepening a
    vertical looks like.
    """

    id: str
    name: str
    status: ConceptStatus
    role: str  # Role ID this Persona is an archetype of (required in v5.0+)
    identity: str  # the opening paragraph
    goals: list[str] = Field(default_factory=list)
    pains: list[str] = Field(default_factory=list)
    triggers: list[str] = Field(default_factory=list)
    quotes: list[str] = Field(default_factory=list)
    channels: str | None = None
    parent: str | None = None  # Persona ID of the containing Persona; None = top-level
    integrity: list[str] = Field(default_factory=list)
    """Data-integrity flags: ``missing_role``, ``broken_role_ref``, ``inactive_role_ref``."""


class JourneyStep(BaseModel):
    """One row of a Journey's Steps table.

    Steps live in the table inside `# Steps`, not as separate files — they are
    read-mostly artifacts surfaced as swimlane cells in the Actors canvas.
    """

    n: int
    stage: str
    step: str
    touchpoint: str
    emotion: str
    pain: str


class Journey(BaseModel):
    """Living-axis sequence of steps a Role walks.

    As of v5.0 ``walks`` references a :class:`Role` (structural user class),
    not a :class:`Persona` directly. The optional ``walked_by`` list can
    supply specific Persona archetypes that concretise this Journey; an empty
    list means the Journey is described abstractly at the Role level, which
    is the common case early in a project.
    """

    id: str
    name: str
    status: ConceptStatus
    walks: str  # Role ID (in v4.x this was a Persona ID)
    walked_by: list[str] = Field(default_factory=list)
    """Persona IDs for concrete cases (optional)."""

    trigger: str
    steps: list[JourneyStep] = Field(default_factory=list)
    outcome: str
    parent: str | None = None  # Journey ID; None = top-level
    integrity: list[str] = Field(default_factory=list)
    """Data-integrity flags: ``missing_walks``, ``broken_walks_ref``, ``inactive_walks_ref``."""


class Narrative(BaseModel):
    """Living-axis "As a / I want / so that" statement (or JTBD / scenario).

    Distinct from Solera's Time-bound :class:`Story` work item — a Narrative
    is upstream of Concepts and may ``proposes:`` Concepts via the Actors
    canvas action (which creates a stub Concept whose Intent is flagged
    "needs human review").

    As of v5.0 ``about`` is split into ``about_roles`` (required, 1+) and
    ``about_personas`` (optional). The structural anchor is the Role set;
    Persona anchors add concreteness when available.
    """

    id: str
    form: NarrativeForm
    status: ConceptStatus
    statement: str
    context: str
    acceptance_cues: list[str] = Field(default_factory=list)
    about_roles: list[str] = Field(default_factory=list)
    """Role IDs this Narrative concerns; spec requires 1+."""

    about_personas: list[str] = Field(default_factory=list)
    """Optional Persona IDs for concrete archetype anchoring."""

    in_journey: str | None = None  # Journey ID, optional
    proposes: list[str] = Field(default_factory=list)  # Concept IDs, populated by canvas action
    integrity: list[str] = Field(default_factory=list)
    """Data-integrity flags: ``missing_about_roles``, ``broken_about_role_ref``,
    ``broken_about_persona_ref``, ``broken_in_journey_ref``."""


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
    roles: list[Role] = Field(default_factory=list)
    personas: list[Persona] = Field(default_factory=list)
    journeys: list[Journey] = Field(default_factory=list)
    narratives: list[Narrative] = Field(default_factory=list)
    concepts: list[Concept] = Field(default_factory=list)
    concept_edges: list[ConceptEdge] = Field(default_factory=list)
    milestones: list[Milestone] = Field(default_factory=list)
    stories: list[Story] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)
    releases: list[Release] = Field(default_factory=list)
