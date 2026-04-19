"""Integrity-flag surfacing for Living-axis entities.

When a `.solera/` file is malformed (missing required frontmatter, or referring
to entities that do not exist), the parser is tolerant — it still returns the
entity — but must surface the issue via the `integrity` list so the canvas and
SidePanel can prompt the human to repair it. Silent drop is the bug these
tests guard against.
"""

from __future__ import annotations

from pathlib import Path

from solera_mcp.graph import build_graph, read_journeys, read_narratives, read_personas


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_role(tmp_path: Path, role_id: str) -> None:
    _write(
        tmp_path / "roles" / f"{role_id}.md",
        f"---\nid: {role_id}\nkind: role\nname: {role_id.title()}\nstatus: active\n"
        "created: 2026-04-01\n---\n\n# Description\nA test role.\n",
    )


def test_journey_missing_walks_sets_integrity_flag(tmp_path: Path) -> None:
    _write(
        tmp_path / "journeys" / "broken.md",
        "---\nid: broken\nkind: journey\nname: Broken\nstatus: active\n"
        "created: 2026-04-01\n---\n\n"
        "# Trigger\nSomething.\n\n# Steps\n\n# Outcome\nNothing.\n",
    )

    journeys = read_journeys(tmp_path)

    assert len(journeys) == 1
    assert journeys[0].walks == ""
    assert "missing_walks" in journeys[0].integrity


def test_narrative_empty_about_roles_sets_integrity_flag(tmp_path: Path) -> None:
    _write(
        tmp_path / "narratives" / "loose.md",
        "---\nid: loose\nkind: narrative\nform: user_story\nstatus: active\n"
        "created: 2026-04-01\nabout_roles: []\n---\n\n"
        "# Statement\nAs a buyer I want X so that Y.\n\n"
        "# Context\nSome context.\n\n"
        "# Acceptance Cues\n- observable signal\n",
    )

    narratives = read_narratives(tmp_path)

    assert len(narratives) == 1
    assert narratives[0].about_roles == []
    assert "missing_about_roles" in narratives[0].integrity


def test_narrative_absent_about_sets_integrity_flag(tmp_path: Path) -> None:
    """``about_roles`` missing from frontmatter entirely is equivalent to empty list."""
    _write(
        tmp_path / "narratives" / "loose.md",
        "---\nid: loose\nkind: narrative\nform: user_story\nstatus: active\n"
        "created: 2026-04-01\n---\n\n"
        "# Statement\nAs a buyer I want X so that Y.\n\n"
        "# Context\nSome context.\n\n"
        "# Acceptance Cues\n- observable signal\n",
    )

    narratives = read_narratives(tmp_path)

    assert len(narratives) == 1
    assert narratives[0].about_roles == []
    assert "missing_about_roles" in narratives[0].integrity


def test_narrative_legacy_about_field_coerced_with_flag(tmp_path: Path) -> None:
    """v4-style ``about:`` field is tolerantly mapped to ``about_roles`` and
    flagged so the UI can prompt the /solera-migrate-v4-to-v5 skill."""
    _write(
        tmp_path / "narratives" / "legacy.md",
        "---\nid: legacy\nkind: narrative\nform: user_story\nstatus: active\n"
        "created: 2026-04-01\nabout: [buyer]\n---\n\n"
        "# Statement\nAs a buyer I want X so that Y.\n\n"
        "# Context\nCtx.\n\n# Acceptance Cues\n- cue\n",
    )

    n = read_narratives(tmp_path)[0]
    assert n.about_roles == ["buyer"]
    assert "legacy_about_field" in n.integrity
    assert "missing_about_roles" not in n.integrity


def test_persona_missing_role_sets_integrity_flag(tmp_path: Path) -> None:
    """v5.0: every Persona must declare a Role; missing it is an integrity flag."""
    _write(
        tmp_path / "personas" / "buyer.md",
        "---\nid: buyer\nkind: persona\nname: Buyer\nstatus: active\n"
        "created: 2026-04-01\n---\n\n# Identity\nA buyer.\n\n# Goals\n- Buy.\n",
    )

    personas = read_personas(tmp_path)

    assert len(personas) == 1
    assert personas[0].role == ""
    assert "missing_role" in personas[0].integrity


def test_persona_broken_role_ref_flagged_by_build_graph(tmp_path: Path) -> None:
    """Persona declares a Role id that no file provides → broken_role_ref."""
    _write(
        tmp_path / "personas" / "buyer.md",
        "---\nid: buyer\nkind: persona\nname: Buyer\nstatus: active\n"
        "role: nonexistent-role\ncreated: 2026-04-01\n---\n\n"
        "# Identity\nA buyer.\n\n# Goals\n- Buy.\n",
    )

    graph = build_graph(tmp_path)

    p = graph.personas[0]
    assert p.role == "nonexistent-role"
    assert "broken_role_ref" in p.integrity


def test_journey_broken_walks_ref_flagged_by_build_graph(tmp_path: Path) -> None:
    """Journey.walks pointing at a non-existent Role → broken_walks_ref."""
    _write(
        tmp_path / "journeys" / "j.md",
        "---\nid: j\nkind: journey\nname: J\nstatus: active\n"
        "walks: nonexistent-role\ncreated: 2026-04-01\n---\n\n"
        "# Trigger\nT.\n\n# Steps\n\n# Outcome\nO.\n",
    )

    graph = build_graph(tmp_path)

    j = graph.journeys[0]
    assert j.walks == "nonexistent-role"
    assert "broken_walks_ref" in j.integrity
    assert "missing_walks" not in j.integrity


def test_narrative_broken_in_journey_ref_flagged_by_build_graph(tmp_path: Path) -> None:
    """Cross-entity ref (`in_journey` pointing at a Journey that doesn't exist)
    is only discoverable after every file is read; `build_graph` adds the flag.
    """
    _seed_role(tmp_path, "buyer")
    _write(
        tmp_path / "narratives" / "has-bad-journey.md",
        "---\nid: has-bad-journey\nkind: narrative\nform: user_story\nstatus: active\n"
        "created: 2026-04-01\nabout_roles: [buyer]\nin_journey: nonexistent-journey\n---\n\n"
        "# Statement\nAs a buyer I want X so that Y.\n\n"
        "# Context\nSome context.\n\n"
        "# Acceptance Cues\n- observable signal\n",
    )

    graph = build_graph(tmp_path)

    assert len(graph.narratives) == 1
    n = graph.narratives[0]
    assert n.in_journey == "nonexistent-journey"  # ref preserved for display
    assert "broken_in_journey_ref" in n.integrity
    assert "missing_about_roles" not in n.integrity


def test_narrative_broken_about_role_ref_flagged_by_build_graph(tmp_path: Path) -> None:
    """about_roles containing an unknown Role id → broken_about_role_ref."""
    _seed_role(tmp_path, "buyer")
    _write(
        tmp_path / "narratives" / "mixed.md",
        "---\nid: mixed\nkind: narrative\nform: user_story\nstatus: active\n"
        "created: 2026-04-01\nabout_roles: [buyer, nonexistent-role]\n---\n\n"
        "# Statement\nS.\n\n# Context\nC.\n\n# Acceptance Cues\n- cue\n",
    )

    graph = build_graph(tmp_path)

    n = graph.narratives[0]
    assert "broken_about_role_ref" in n.integrity


def test_narrative_valid_refs_has_clean_integrity(tmp_path: Path) -> None:
    """A Narrative that points at existing Role + existing Journey gets no flag."""
    _seed_role(tmp_path, "buyer")
    _write(
        tmp_path / "journeys" / "checkout.md",
        "---\nid: checkout\nkind: journey\nname: Checkout\nstatus: active\n"
        "created: 2026-04-01\nwalks: buyer\n---\n\n"
        "# Trigger\nThey want to buy.\n\n"
        "# Steps\n\n| # | Stage | Step | Touchpoint | Emotion | Pain |\n"
        "|---|-------|------|------------|---------|------|\n"
        "| 01 | Pick | Pick item | Mobile | 😀 | — |\n\n"
        "# Outcome\nItem bought.\n",
    )
    _write(
        tmp_path / "narratives" / "anchored.md",
        "---\nid: anchored\nkind: narrative\nform: user_story\nstatus: active\n"
        "created: 2026-04-01\nabout_roles: [buyer]\nin_journey: checkout\n---\n\n"
        "# Statement\nAs a buyer I want X so that Y.\n\n"
        "# Context\nSome context.\n\n# Acceptance Cues\n- observable signal\n",
    )

    graph = build_graph(tmp_path)

    assert graph.narratives[0].integrity == []
    assert graph.journeys[0].integrity == []
