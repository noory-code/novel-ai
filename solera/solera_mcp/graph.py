"""Assemble a Solera workspace into a typed :class:`Graph`.

This module is a thin facade over the split parser stack. Responsibilities
live in their own modules:

- :mod:`solera_mcp.models`    — typed Pydantic models
- :mod:`solera_mcp.parsing`   — markdown / frontmatter / table helpers
- :mod:`solera_mcp.readers`   — per-entity read_* functions
- :mod:`solera_mcp.writers`   — update_concept_frontmatter, read/write_layout
- :mod:`solera_mcp.integrity` — cross-entity validation pass

The public surface here — ``build_graph`` plus everything ``server.py`` and
the test suite previously imported from ``solera_mcp.graph`` — is
preserved via re-exports, so external imports keep working unchanged.
"""

from __future__ import annotations

from pathlib import Path

from solera_mcp.integrity import annotate_cross_ref_integrity
from solera_mcp.models import (
    STATUS_ICON_MAP,
    ActionItem,
    Concept,
    ConceptEdge,
    ConceptStatus,
    Graph,
    Identity,
    Journey,
    JourneyStep,
    Milestone,
    Narrative,
    NarrativeForm,
    Persona,
    Release,
    Role,
    Story,
    WorkStatus,
)
from solera_mcp.parsing import (
    parse_bullet_list,
    parse_frontmatter,
    parse_journey_steps_table,
    parse_sections,
)
from solera_mcp.readers import (
    read_concept_file,
    read_concept_graph,
    read_concepts,
    read_identity,
    read_journey_file,
    read_journeys,
    read_milestone_file,
    read_milestones,
    read_narrative_file,
    read_narratives,
    read_persona_file,
    read_personas,
    read_releases,
    read_role_file,
    read_roles,
    read_stories,
    read_story_file,
)
from solera_mcp.writers import read_layout, update_concept_frontmatter, write_layout

__all__ = [
    # Models
    "ActionItem",
    "Concept",
    "ConceptEdge",
    "ConceptStatus",
    "Graph",
    "Identity",
    "Journey",
    "JourneyStep",
    "Milestone",
    "Narrative",
    "NarrativeForm",
    "Persona",
    "Release",
    "Role",
    "STATUS_ICON_MAP",
    "Story",
    "WorkStatus",
    # Parsing helpers (used by skill-writers and tests)
    "parse_frontmatter",
    "parse_sections",
    "parse_bullet_list",
    "parse_journey_steps_table",
    # Readers
    "read_concept_file",
    "read_concept_graph",
    "read_concepts",
    "read_identity",
    "read_journey_file",
    "read_journeys",
    "read_milestone_file",
    "read_milestones",
    "read_narrative_file",
    "read_narratives",
    "read_persona_file",
    "read_personas",
    "read_releases",
    "read_role_file",
    "read_roles",
    "read_stories",
    "read_story_file",
    # Writers
    "read_layout",
    "update_concept_frontmatter",
    "write_layout",
    # Aggregation
    "build_graph",
]


def build_graph(workspace: Path) -> Graph:
    """Read everything under the Solera root and assemble a :class:`Graph`.

    ``workspace`` is the directory returned by ``resolve_solera_root`` —
    typically ``<project>/.solera/`` (v4+) or ``<project>/workspace/`` (v3
    fallback). The parameter name is historical; it points at whichever
    layout exists.

    A second ``integrity`` pass runs after each kind's reader so that
    cross-entity references (``Persona.role``, ``Journey.walks``,
    ``Narrative.about_roles`` / ``in_journey``) can be validated against
    the other entities' canonical id sets.
    """
    stories, action_items = read_stories(workspace)
    roles = read_roles(workspace)
    personas = read_personas(workspace)
    journeys = read_journeys(workspace)
    narratives = read_narratives(workspace)
    annotate_cross_ref_integrity(roles, personas, journeys, narratives)
    return Graph(
        identity=read_identity(workspace),
        roles=roles,
        personas=personas,
        journeys=journeys,
        narratives=narratives,
        concepts=read_concepts(workspace),
        concept_edges=read_concept_graph(workspace),
        milestones=read_milestones(workspace),
        stories=stories,
        action_items=action_items,
        releases=read_releases(workspace),
    )
