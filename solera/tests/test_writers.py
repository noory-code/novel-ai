"""Round-trip tests for the v5.1 entity writers.

Each test writes a fresh entity file via ``create_*``, re-reads it via the
matching reader, asserts the values round-trip, then applies a ``update_*``
patch and re-reads to assert the patch took effect without corrupting other
sections.
"""

from __future__ import annotations

from pathlib import Path

from solera_mcp.readers import (
    read_concept_file,
    read_journey_file,
    read_narrative_file,
    read_persona_file,
    read_role_file,
)
from solera_mcp.writers import (
    create_concept,
    create_journey,
    create_narrative,
    create_persona,
    create_role,
    update_concept,
    update_journey,
    update_narrative,
    update_persona,
    update_role,
)

# ---------------------------------------------------------------------------
# Role
# ---------------------------------------------------------------------------


def test_role_create_and_update_round_trip(tmp_path: Path) -> None:
    path = create_role(
        tmp_path,
        {
            "id": "admin",
            "name": "Admin",
            "description": "Operates the platform.",
            "context": "Runtime team.",
        },
    )
    r = read_role_file(path)
    assert r.id == "admin"
    assert r.description == "Operates the platform."
    assert r.context == "Runtime team."
    assert r.parent is None

    update_role(path, {"name": "Platform Admin", "description": "Updated."})
    r2 = read_role_file(path)
    assert r2.name == "Platform Admin"
    assert r2.description == "Updated."
    # Context must not have been disturbed.
    assert r2.context == "Runtime team."


def test_role_update_can_remove_context(tmp_path: Path) -> None:
    path = create_role(
        tmp_path,
        {"id": "admin", "description": "Desc.", "context": "Ctx."},
    )
    update_role(path, {"context": None})
    r = read_role_file(path)
    assert r.context is None


def test_role_update_parent_to_null_removes_field(tmp_path: Path) -> None:
    path = create_role(tmp_path, {"id": "child", "parent": "parent-role", "description": "D"})
    assert read_role_file(path).parent == "parent-role"
    update_role(path, {"parent": None})
    assert read_role_file(path).parent is None


# ---------------------------------------------------------------------------
# Persona — bullet lists + textual body
# ---------------------------------------------------------------------------


def test_persona_create_round_trip(tmp_path: Path) -> None:
    path = create_persona(
        tmp_path,
        {
            "id": "alice",
            "role": "fan",
            "identity": "A designer.",
            "goals": ["Buy more", "Stay connected"],
            "pains": ["Slow checkout"],
            "triggers": [],
            "quotes": ['"Coffee" — interview'],
            "channels": "Mobile",
        },
    )
    p = read_persona_file(path)
    assert p.role == "fan"
    assert p.identity == "A designer."
    assert p.goals == ["Buy more", "Stay connected"]
    assert p.pains == ["Slow checkout"]
    assert p.triggers == []
    assert len(p.quotes) == 1
    assert p.channels == "Mobile"


def test_persona_update_bullet_list_replaces_whole_section(tmp_path: Path) -> None:
    path = create_persona(
        tmp_path,
        {
            "id": "alice",
            "role": "fan",
            "identity": "A designer.",
            "goals": ["old-goal-1", "old-goal-2"],
        },
    )
    update_persona(path, {"goals": ["new-goal-a"]})
    p = read_persona_file(path)
    assert p.goals == ["new-goal-a"]


def test_persona_update_role_field_updates_frontmatter(tmp_path: Path) -> None:
    path = create_persona(tmp_path, {"id": "alice", "role": "fan", "identity": "A."})
    update_persona(path, {"role": "hero"})
    assert read_persona_file(path).role == "hero"


# ---------------------------------------------------------------------------
# Journey — steps table + walked_by list
# ---------------------------------------------------------------------------


def test_journey_create_round_trip(tmp_path: Path) -> None:
    path = create_journey(
        tmp_path,
        {
            "id": "first-purchase",
            "walks": "fan",
            "walked_by": ["alice"],
            "trigger": "They want to buy.",
            "outcome": "They did.",
            "steps": [
                {
                    "n": 1,
                    "stage": "Browse",
                    "step": "Open app",
                    "touchpoint": "Mobile",
                    "emotion": "😀",
                    "pain": "—",
                },
                {
                    "n": 2,
                    "stage": "Pay",
                    "step": "Confirm",
                    "touchpoint": "Mobile",
                    "emotion": "😐",
                    "pain": "Slow",
                },
            ],
        },
    )
    j = read_journey_file(path)
    assert j.walks == "fan"
    assert j.walked_by == ["alice"]
    assert j.trigger == "They want to buy."
    assert j.outcome == "They did."
    assert len(j.steps) == 2
    assert j.steps[0].stage == "Browse"
    assert j.steps[1].pain == "Slow"


def test_journey_update_steps_replaces_whole_table(tmp_path: Path) -> None:
    path = create_journey(
        tmp_path,
        {
            "id": "first-purchase",
            "walks": "fan",
            "trigger": "T",
            "outcome": "O",
            "steps": [
                {"n": 1, "stage": "a", "step": "x", "touchpoint": "y", "emotion": "😀", "pain": "—"}
            ],
        },
    )
    update_journey(
        path,
        {
            "steps": [
                {
                    "n": 1,
                    "stage": "z",
                    "step": "replaced",
                    "touchpoint": "web",
                    "emotion": "😐",
                    "pain": "pain!",
                },
            ]
        },
    )
    j = read_journey_file(path)
    assert len(j.steps) == 1
    assert j.steps[0].step == "replaced"
    assert j.steps[0].pain == "pain!"


def test_journey_update_walks_updates_frontmatter(tmp_path: Path) -> None:
    path = create_journey(
        tmp_path, {"id": "j", "walks": "fan", "trigger": "T", "outcome": "O", "steps": []}
    )
    update_journey(path, {"walks": "hero"})
    assert read_journey_file(path).walks == "hero"


# ---------------------------------------------------------------------------
# Narrative — about_roles/about_personas split + acceptance cues bullets
# ---------------------------------------------------------------------------


def test_narrative_create_round_trip(tmp_path: Path) -> None:
    path = create_narrative(
        tmp_path,
        {
            "id": "queue-fair",
            "form": "user_story",
            "about_roles": ["fan"],
            "about_personas": ["alice"],
            "in_journey": "first-purchase",
            "statement": "As a fan I want X so that Y.",
            "context": "Context.",
            "acceptance_cues": ["Cue 1", "Cue 2"],
        },
    )
    n = read_narrative_file(path)
    assert n.about_roles == ["fan"]
    assert n.about_personas == ["alice"]
    assert n.in_journey == "first-purchase"
    assert n.statement.startswith("As a fan")
    assert n.acceptance_cues == ["Cue 1", "Cue 2"]


def test_narrative_update_about_roles_splits_from_about_personas(tmp_path: Path) -> None:
    path = create_narrative(
        tmp_path,
        {
            "id": "n",
            "about_roles": ["fan"],
            "statement": "S",
            "context": "C",
            "acceptance_cues": ["c"],
        },
    )
    update_narrative(path, {"about_roles": ["fan", "hero"], "about_personas": ["alice"]})
    n = read_narrative_file(path)
    assert n.about_roles == ["fan", "hero"]
    assert n.about_personas == ["alice"]


def test_narrative_update_statement_preserves_context(tmp_path: Path) -> None:
    path = create_narrative(
        tmp_path,
        {
            "id": "n",
            "about_roles": ["fan"],
            "statement": "old statement",
            "context": "load-bearing context",
            "acceptance_cues": ["c"],
        },
    )
    update_narrative(path, {"statement": "new statement"})
    n = read_narrative_file(path)
    assert n.statement == "new statement"
    assert n.context == "load-bearing context"


# ---------------------------------------------------------------------------
# Concept — extends the existing frontmatter-only writer
# ---------------------------------------------------------------------------


def test_concept_create_and_update_round_trip(tmp_path: Path) -> None:
    path = create_concept(
        tmp_path,
        {
            "id": "auth",
            "name": "Auth",
            "intent": "User proves identity.",
            "current_design": "Passwordless.",
            "current_shape": "(no Stories)",
        },
    )
    c = read_concept_file(path)
    assert c.id == "auth"
    assert c.intent == "User proves identity."
    assert c.current_design == "Passwordless."

    update_concept(path, {"current_design": "OAuth", "horizon": "Passkeys by 2027"})
    c2 = read_concept_file(path)
    assert c2.current_design == "OAuth"
    assert c2.horizon == "Passkeys by 2027"
    # Intent must not have been disturbed.
    assert c2.intent == "User proves identity."
