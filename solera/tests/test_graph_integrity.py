"""Integrity-flag surfacing for Living-axis entities.

When a `.solera/` file is malformed (missing required frontmatter, or referring
to entities that do not exist), the parser is tolerant — it still returns the
entity — but must surface the issue via the `integrity` list so the canvas and
SidePanel can prompt the human to repair it. Silent drop is the bug these
tests guard against.
"""

from __future__ import annotations

from pathlib import Path

from solera_mcp.graph import build_graph, read_journeys, read_narratives


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


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


def test_narrative_empty_about_sets_integrity_flag(tmp_path: Path) -> None:
    _write(
        tmp_path / "narratives" / "loose.md",
        "---\nid: loose\nkind: narrative\nform: user_story\nstatus: active\n"
        "created: 2026-04-01\nabout: []\n---\n\n"
        "# Statement\nAs a buyer I want X so that Y.\n\n"
        "# Context\nSome context.\n\n"
        "# Acceptance Cues\n- observable signal\n",
    )

    narratives = read_narratives(tmp_path)

    assert len(narratives) == 1
    assert narratives[0].about == []
    assert "missing_about" in narratives[0].integrity


def test_narrative_absent_about_sets_integrity_flag(tmp_path: Path) -> None:
    """`about:` missing from frontmatter entirely is equivalent to empty list."""
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
    assert narratives[0].about == []
    assert "missing_about" in narratives[0].integrity


def test_narrative_broken_in_journey_ref_flagged_by_build_graph(tmp_path: Path) -> None:
    """Cross-entity ref (`in_journey` pointing at a Journey that doesn't exist)
    is only discoverable after every file is read; `build_graph` adds the flag.
    """
    # Persona the Narrative is about — needed so `missing_about` doesn't fire.
    _write(
        tmp_path / "personas" / "buyer.md",
        "---\nid: buyer\nkind: persona\nname: Buyer\nstatus: active\n"
        "created: 2026-04-01\n---\n\n"
        "# Identity\nA buyer.\n\n# Goals\n- Buy.\n",
    )
    _write(
        tmp_path / "narratives" / "has-bad-journey.md",
        "---\nid: has-bad-journey\nkind: narrative\nform: user_story\nstatus: active\n"
        "created: 2026-04-01\nabout: [buyer]\nin_journey: nonexistent-journey\n---\n\n"
        "# Statement\nAs a buyer I want X so that Y.\n\n"
        "# Context\nSome context.\n\n"
        "# Acceptance Cues\n- observable signal\n",
    )

    graph = build_graph(tmp_path)

    assert len(graph.narratives) == 1
    n = graph.narratives[0]
    assert n.in_journey == "nonexistent-journey"  # ref preserved for display
    assert "broken_in_journey_ref" in n.integrity
    assert "missing_about" not in n.integrity  # about is valid


def test_narrative_valid_in_journey_has_clean_integrity(tmp_path: Path) -> None:
    """A Narrative that points at an existing Journey gets no flag."""
    _write(
        tmp_path / "personas" / "buyer.md",
        "---\nid: buyer\nkind: persona\nname: Buyer\nstatus: active\n"
        "created: 2026-04-01\n---\n\n# Identity\nA buyer.\n\n# Goals\n- Buy.\n",
    )
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
        "created: 2026-04-01\nabout: [buyer]\nin_journey: checkout\n---\n\n"
        "# Statement\nAs a buyer I want X so that Y.\n\n"
        "# Context\nSome context.\n\n# Acceptance Cues\n- observable signal\n",
    )

    graph = build_graph(tmp_path)

    n = graph.narratives[0]
    assert n.integrity == []
