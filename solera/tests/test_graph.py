"""Tests for the Solera-root → Graph parser."""

from __future__ import annotations

import json
from pathlib import Path

from solera_mcp.graph import (
    build_graph,
    parse_frontmatter,
    parse_sections,
    read_concept_graph,
    read_concepts,
    read_journeys,
    read_milestones,
    read_narratives,
    read_personas,
    read_releases,
    read_stories,
)

# ---------------------------------------------------------------------------
# Unit: markdown helpers
# ---------------------------------------------------------------------------


def test_parse_frontmatter_roundtrip() -> None:
    text = "---\nfoo: bar\nnums:\n  - 1\n  - 2\n---\nBody line\n"
    fm, body = parse_frontmatter(text)
    assert fm == {"foo": "bar", "nums": [1, 2]}
    assert body == "Body line\n"


def test_parse_frontmatter_absent() -> None:
    fm, body = parse_frontmatter("# Hello\n")
    assert fm == {}
    assert body == "# Hello\n"


def test_parse_sections_splits_on_h1() -> None:
    body = "# Intent\nthe north star\n\n# Current Design\na thing\n\n# Current Shape\nanother\n"
    sections = parse_sections(body)
    assert sections["Intent"] == "the north star"
    assert sections["Current Design"] == "a thing"
    assert sections["Current Shape"] == "another"


# ---------------------------------------------------------------------------
# Fixture helper
# ---------------------------------------------------------------------------


def _write_concept(workspace: Path, concept_id: str, status: str = "active") -> None:
    d = workspace / "concepts"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{concept_id}.md").write_text(
        f"---\n"
        f"id: {concept_id}\n"
        f"name: {concept_id.title()}\n"
        f"status: {status}\n"
        f"created: 2026-04-01\n"
        f"---\n\n"
        f"# Intent\nNorth star for {concept_id}.\n\n"
        f"# Current Design\nIdeal for {concept_id}.\n\n"
        f"# Current Shape\nBuilt so far for {concept_id}.\n\n"
        f"# Horizon\nFuture of {concept_id}.\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Concepts
# ---------------------------------------------------------------------------


def test_read_concepts_parses_sections(tmp_path: Path) -> None:
    _write_concept(tmp_path, "authentication")
    _write_concept(tmp_path, "search")

    concepts = read_concepts(tmp_path)

    assert {c.id for c in concepts} == {"authentication", "search"}
    auth = next(c for c in concepts if c.id == "authentication")
    assert auth.intent == "North star for authentication."
    assert auth.current_design == "Ideal for authentication."
    assert auth.current_shape == "Built so far for authentication."
    assert auth.horizon == "Future of authentication."
    assert auth.status == "active"
    assert auth.parent is None


def test_read_concepts_captures_parent(tmp_path: Path) -> None:
    d = tmp_path / "concepts"
    d.mkdir(parents=True)
    (d / "app.md").write_text(
        "---\nid: app\nname: App\nstatus: active\n---\n\n# Intent\nTop.\n",
        encoding="utf-8",
    )
    (d / "me-tab.md").write_text(
        "---\nid: me-tab\nname: Me Tab\nstatus: active\nparent: app\n---\n\n# Intent\nChild.\n",
        encoding="utf-8",
    )
    (d / "profile.md").write_text(
        "---\nid: profile\nname: Profile\nstatus: active\nparent: me-tab\n---\n\n"
        "# Intent\nGrandchild.\n",
        encoding="utf-8",
    )

    concepts = {c.id: c for c in read_concepts(tmp_path)}

    assert concepts["app"].parent is None
    assert concepts["me-tab"].parent == "app"
    assert concepts["profile"].parent == "me-tab"


def test_read_concepts_skips_index_file(tmp_path: Path) -> None:
    _write_concept(tmp_path, "foo")
    (tmp_path / "concepts" / "_index.md").write_text("# index\n", encoding="utf-8")

    concepts = read_concepts(tmp_path)

    assert {c.id for c in concepts} == {"foo"}


def test_read_concepts_missing_dir_returns_empty(tmp_path: Path) -> None:
    assert read_concepts(tmp_path) == []


# ---------------------------------------------------------------------------
# Concept edges
# ---------------------------------------------------------------------------


def test_read_concept_graph(tmp_path: Path) -> None:
    (tmp_path / "concept-graph.json").write_text(
        json.dumps(
            {
                "edges": [
                    {
                        "from": "auth",
                        "to": "profile",
                        "label": "depends on",
                        "created": "2026-04-18",
                    },
                    {"from": "auth", "to": "onboarding", "label": "used by"},
                ]
            }
        ),
        encoding="utf-8",
    )

    edges = read_concept_graph(tmp_path)

    assert len(edges) == 2
    assert edges[0].from_id == "auth"
    assert edges[0].to_id == "profile"
    assert edges[0].label == "depends on"
    assert edges[0].created == "2026-04-18"
    assert edges[1].label == "used by"
    # Each edge has a unique id
    assert edges[0].id != edges[1].id


def test_read_concept_graph_missing(tmp_path: Path) -> None:
    assert read_concept_graph(tmp_path) == []


# ---------------------------------------------------------------------------
# Milestones
# ---------------------------------------------------------------------------


def test_read_milestones(tmp_path: Path) -> None:
    d = tmp_path / "milestones"
    d.mkdir()
    (d / "mvp.md").write_text(
        "---\nid: mvp\nname: MVP\nstatus: agreed\n---\n\n"
        "# Scope\n- authentication\n- onboarding\n\n"
        "# Exit Criteria\nAll concepts painted.\n",
        encoding="utf-8",
    )

    milestones = read_milestones(tmp_path)

    assert len(milestones) == 1
    assert milestones[0].id == "mvp"
    assert milestones[0].status == "agreed"
    assert milestones[0].scope == ["authentication", "onboarding"]


def test_read_milestones_with_wikilink_scope(tmp_path: Path) -> None:
    """Support Obsidian-style `[[../concepts/id]]` scope entries (banas-style)."""
    d = tmp_path / "milestones"
    d.mkdir()
    (d / "pre-v3.md").write_text(
        "---\nid: pre-v3\nname: Pre-v3\nstatus: released\n---\n\n"
        "# Scope\n"
        "- [[../concepts/authentication]] — as of v3 migration\n"
        "- [[../concepts/admin]]\n"
        "- [[../concepts/onboarding|Onboarding label]] — note\n",
        encoding="utf-8",
    )

    milestones = read_milestones(tmp_path)

    assert milestones[0].scope == ["authentication", "admin", "onboarding"]


def test_parse_frontmatter_handles_malformed_yaml() -> None:
    """Real banas workspace has unquoted titles with colons; don't hard-fail."""
    text = "---\ntitle: TS-001: 인증\nid: ts-001\n---\nBody\n"

    fm, body = parse_frontmatter(text)

    # Malformed YAML collapses to empty dict; body still usable.
    assert fm == {}
    assert body == "Body\n"


# ---------------------------------------------------------------------------
# Stories + Action Items
# ---------------------------------------------------------------------------


def test_read_stories_and_acts(tmp_path: Path) -> None:
    story_dir = tmp_path / "stories" / "US-001-google-login"
    story_dir.mkdir(parents=True)
    (story_dir / "_story.md").write_text(
        "---\n"
        "id: US-001\n"
        "name: google-login\n"
        "type: US\n"
        "status: 🔄\n"
        "contributes_to: [authentication]\n"
        "belongs_to: mvp\n"
        "---\n\n"
        "# Story\nBody.\n",
        encoding="utf-8",
    )
    (story_dir / "ACT-001-provider.md").write_text(
        "---\nid: ACT-001\nname: provider\nstatus: ✅\n---\n",
        encoding="utf-8",
    )
    (story_dir / "ACT-002-screen.md").write_text(
        "---\nid: ACT-002\nname: screen\nstatus: 🔄\ndepends_on: [ACT-001]\n---\n",
        encoding="utf-8",
    )

    stories, acts = read_stories(tmp_path)

    assert len(stories) == 1
    s = stories[0]
    assert s.id == "US-001"
    assert s.status == "in_progress"
    assert s.contributes_to == ["authentication"]
    assert s.belongs_to == "mvp"

    assert {a.id for a in acts} == {"ACT-001", "ACT-002"}
    done = next(a for a in acts if a.id == "ACT-001")
    assert done.status == "complete"
    chain = next(a for a in acts if a.id == "ACT-002")
    assert chain.depends_on == ["ACT-001"]
    assert chain.story_id == "US-001"


# ---------------------------------------------------------------------------
# Releases
# ---------------------------------------------------------------------------


def test_read_releases(tmp_path: Path) -> None:
    tag_dir = tmp_path / "releases" / "v0.1-mvp"
    tag_dir.mkdir(parents=True)
    (tag_dir / ".released").write_text(
        "release_tag: v0.1-mvp\n"
        "milestone_id: mvp\n"
        "released_at: 2026-04-18 10:00\n"
        "by: solera-release v1.0.1\n",
        encoding="utf-8",
    )

    releases = read_releases(tmp_path)

    assert len(releases) == 1
    assert releases[0].tag == "v0.1-mvp"
    assert releases[0].milestone_id == "mvp"


def test_read_releases_skips_dirs_without_marker(tmp_path: Path) -> None:
    incomplete = tmp_path / "releases" / "v0.2-wip"
    incomplete.mkdir(parents=True)
    # no .released marker

    assert read_releases(tmp_path) == []


# ---------------------------------------------------------------------------
# build_graph aggregate
# ---------------------------------------------------------------------------


def test_build_graph_end_to_end(tmp_path: Path) -> None:
    _write_concept(tmp_path, "authentication")
    _write_concept(tmp_path, "search")
    (tmp_path / "concept-graph.json").write_text(
        json.dumps({"edges": [{"from": "authentication", "to": "search", "label": "uses"}]}),
        encoding="utf-8",
    )

    graph = build_graph(tmp_path)

    assert {c.id for c in graph.concepts} == {"authentication", "search"}
    assert len(graph.concept_edges) == 1
    assert graph.concept_edges[0].label == "uses"
    assert graph.milestones == []
    assert graph.stories == []
    assert graph.releases == []
    # New v4 Living-axis arrays default to empty when their dirs are absent.
    assert graph.personas == []
    assert graph.journeys == []
    assert graph.narratives == []


# ---------------------------------------------------------------------------
# Personas (v4 Living axis)
# ---------------------------------------------------------------------------


def _write_role(
    workspace: Path,
    role_id: str,
    *,
    parent: str | None = None,
) -> None:
    """v5.0+ Role fixture helper."""
    d = workspace / "roles"
    d.mkdir(parents=True, exist_ok=True)
    parent_line = f"parent: {parent}\n" if parent else ""
    (d / f"{role_id}.md").write_text(
        f"---\n"
        f"id: {role_id}\n"
        f"kind: role\n"
        f"name: {role_id.replace('-', ' ').title()}\n"
        f"status: active\n"
        f"created: 2026-04-01\n"
        f"{parent_line}"
        f"---\n\n"
        f"# Description\nThe {role_id} Role used in tests.\n",
        encoding="utf-8",
    )


def _write_persona(
    workspace: Path,
    persona_id: str,
    *,
    role: str = "customer",
    parent: str | None = None,
) -> None:
    d = workspace / "personas"
    d.mkdir(parents=True, exist_ok=True)
    parent_line = f"parent: {parent}\n" if parent else ""
    (d / f"{persona_id}.md").write_text(
        f"---\n"
        f"id: {persona_id}\n"
        f"kind: persona\n"
        f"name: {persona_id.replace('-', ' ').title()}\n"
        f"status: active\n"
        f"created: 2026-04-01\n"
        f"role: {role}\n"
        f"{parent_line}"
        f"---\n\n"
        f"# Identity\nA shopkeeper running a small independent cafe in a dense urban area.\n\n"
        f"# Goals\n"
        f"- Sell more coffee per morning\n"
        f"- Build a regular crowd\n\n"
        f"# Pains\n"
        f"- Mornings are chaotic; orders get lost\n"
        f"- Cash drawer reconciliation is manual\n\n"
        f"# Triggers\n"
        f"- Drops one too many drink orders during peak\n"
        f"- A regular asks if there's a loyalty system\n\n"
        f"# Quotes\n"
        f'- "I just need it to work during the morning rush." — *real interview*\n\n'
        f"# Channels\nMobile (in-store), occasionally desktop after hours.\n",
        encoding="utf-8",
    )


def test_read_personas_parses_sections_and_lists(tmp_path: Path) -> None:
    _write_persona(tmp_path, "small-cafe-owner")

    personas = read_personas(tmp_path)

    assert len(personas) == 1
    p = personas[0]
    assert p.id == "small-cafe-owner"
    assert p.status == "active"
    assert "shopkeeper" in p.identity
    assert p.goals == ["Sell more coffee per morning", "Build a regular crowd"]
    assert len(p.pains) == 2
    assert p.triggers == [
        "Drops one too many drink orders during peak",
        "A regular asks if there's a loyalty system",
    ]
    assert len(p.quotes) == 1 and "morning rush" in p.quotes[0]
    assert p.channels and "Mobile" in p.channels
    assert p.parent is None


def test_read_personas_captures_parent(tmp_path: Path) -> None:
    _write_persona(tmp_path, "buyer")
    _write_persona(tmp_path, "vip-buyer", parent="buyer")

    personas = {p.id: p for p in read_personas(tmp_path)}

    assert personas["buyer"].parent is None
    assert personas["vip-buyer"].parent == "buyer"


def test_read_personas_skips_index_file(tmp_path: Path) -> None:
    _write_persona(tmp_path, "buyer")
    (tmp_path / "personas" / "_index.md").write_text("# index\n", encoding="utf-8")

    assert {p.id for p in read_personas(tmp_path)} == {"buyer"}


def test_read_personas_missing_dir_returns_empty(tmp_path: Path) -> None:
    assert read_personas(tmp_path) == []


# ---------------------------------------------------------------------------
# Journeys (v4 Living axis)
# ---------------------------------------------------------------------------


def _write_journey(
    workspace: Path,
    journey_id: str,
    *,
    walks: str = "buyer",
    parent: str | None = None,
) -> None:
    d = workspace / "journeys"
    d.mkdir(parents=True, exist_ok=True)
    parent_line = f"parent: {parent}\n" if parent else ""
    (d / f"{journey_id}.md").write_text(
        f"---\n"
        f"id: {journey_id}\n"
        f"kind: journey\n"
        f"name: {journey_id.replace('-', ' ').title()}\n"
        f"status: active\n"
        f"created: 2026-04-01\n"
        f"walks: {walks}\n"
        f"{parent_line}"
        f"---\n\n"
        f"# Trigger\nThe buyer hears about the service from a friend.\n\n"
        f"# Steps\n\n"
        f"| # | Stage | Step | Touchpoint | Emotion | Pain |\n"
        f"|---|-------|------|------------|---------|------|\n"
        f"| 01 | Discovery | Search for a cafe app | Web | 😀 | — |\n"
        f"| 02 | Signup | Create an account | Mobile | 😐 | Email confirmation slow |\n"
        f"| 03 | First order | Browse menu | Mobile | 😀 | — |\n\n"
        f"# Outcome\nThe buyer places their first order in under two minutes.\n",
        encoding="utf-8",
    )


def test_read_journeys_parses_steps_table(tmp_path: Path) -> None:
    _write_journey(tmp_path, "first-time-checkout", walks="small-cafe-owner")

    journeys = read_journeys(tmp_path)

    assert len(journeys) == 1
    j = journeys[0]
    assert j.id == "first-time-checkout"
    assert j.walks == "small-cafe-owner"
    assert "hears about the service" in j.trigger
    assert "first order" in j.outcome
    assert len(j.steps) == 3
    assert j.steps[0].n == 1
    assert j.steps[0].stage == "Discovery"
    assert j.steps[0].emotion == "😀"
    assert j.steps[1].pain == "Email confirmation slow"
    assert j.steps[2].step == "Browse menu"


def test_read_journeys_missing_walks_renders_orphan(tmp_path: Path) -> None:
    """A Journey lacking `walks` is surfaced (canvas marks it orphan)."""
    d = tmp_path / "journeys"
    d.mkdir(parents=True)
    (d / "broken.md").write_text(
        "---\nid: broken\nkind: journey\nname: Broken\nstatus: active\ncreated: 2026-04-01\n---\n\n"
        "# Trigger\nSomething.\n\n# Steps\n\n# Outcome\nNothing.\n",
        encoding="utf-8",
    )

    journeys = read_journeys(tmp_path)

    assert len(journeys) == 1
    assert journeys[0].walks == ""  # rendered as orphan by the canvas


def test_read_journeys_missing_dir_returns_empty(tmp_path: Path) -> None:
    assert read_journeys(tmp_path) == []


# ---------------------------------------------------------------------------
# Narratives (v4 Living axis)
# ---------------------------------------------------------------------------


def _write_narrative(
    workspace: Path,
    narrative_id: str,
    *,
    form: str = "user_story",
    about_roles: list[str] | None = None,
    about_personas: list[str] | None = None,
    in_journey: str | None = None,
    proposes: list[str] | None = None,
) -> None:
    d = workspace / "narratives"
    d.mkdir(parents=True, exist_ok=True)
    about_roles = about_roles if about_roles is not None else ["customer"]
    about_personas_line = (
        f"about_personas: {json.dumps(about_personas)}\n"
        if about_personas is not None
        else ""
    )
    in_journey_line = f"in_journey: {in_journey}\n" if in_journey else ""
    proposes_line = (
        f"proposes: {json.dumps(proposes)}\n"
        if proposes is not None
        else ""
    )
    (d / f"{narrative_id}.md").write_text(
        f"---\n"
        f"id: {narrative_id}\n"
        f"kind: narrative\n"
        f"form: {form}\n"
        f"status: active\n"
        f"created: 2026-04-01\n"
        f"about_roles: {json.dumps(about_roles)}\n"
        f"{about_personas_line}"
        f"{in_journey_line}"
        f"{proposes_line}"
        f"---\n\n"
        f"# Statement\n"
        f"> As a small cafe owner, I want to track morning rush orders so that nothing slips.\n\n"
        f"# Context\n"
        f"During the morning rush the cafe loses orders silently until reconciliation.\n\n"
        f"# Acceptance Cues\n"
        f"- Orders that arrive after 7am show up in the active queue immediately.\n"
        f"- A miss-fire is impossible without an audible alert.\n",
        encoding="utf-8",
    )


def test_read_narratives_parses_user_story(tmp_path: Path) -> None:
    _write_narrative(tmp_path, "rush-orders-not-lost")

    narratives = read_narratives(tmp_path)

    assert len(narratives) == 1
    n = narratives[0]
    assert n.id == "rush-orders-not-lost"
    assert n.form == "user_story"
    assert "small cafe owner" in n.statement
    assert "morning rush" in n.context
    assert len(n.acceptance_cues) == 2
    assert n.about_roles == ["customer"]
    assert n.about_personas == []
    assert n.in_journey is None
    assert n.proposes == []


def test_read_narratives_captures_in_journey_and_proposes(tmp_path: Path) -> None:
    _write_narrative(
        tmp_path,
        "first-purchase",
        in_journey="first-time-checkout",
        proposes=["order-tracking", "alert-bell"],
    )

    n = read_narratives(tmp_path)[0]

    assert n.in_journey == "first-time-checkout"
    assert n.proposes == ["order-tracking", "alert-bell"]


def test_read_narratives_form_fallback_to_user_story(tmp_path: Path) -> None:
    """Unknown `form:` values silently fall back to `user_story` rather than crash."""
    d = tmp_path / "narratives"
    d.mkdir(parents=True)
    (d / "weird.md").write_text(
        "---\n"
        "id: weird\nkind: narrative\nform: poem\nstatus: active\ncreated: 2026-04-01\n"
        'about_roles: ["buyer"]\n---\n\n'
        "# Statement\nA verse.\n\n# Context\nCtx.\n\n# Acceptance Cues\n- one\n",
        encoding="utf-8",
    )

    n = read_narratives(tmp_path)[0]

    assert n.form == "user_story"


def test_read_narratives_missing_dir_returns_empty(tmp_path: Path) -> None:
    assert read_narratives(tmp_path) == []


# ---------------------------------------------------------------------------
# build_graph end-to-end with v5 Living-axis entities
# ---------------------------------------------------------------------------


def test_build_graph_includes_v5_living_axis(tmp_path: Path) -> None:
    _write_role(tmp_path, "customer")
    _write_concept(tmp_path, "order-tracking")
    _write_persona(tmp_path, "small-cafe-owner", role="customer")
    _write_journey(tmp_path, "first-time-checkout", walks="customer")
    _write_narrative(
        tmp_path,
        "rush-orders-not-lost",
        about_roles=["customer"],
        in_journey="first-time-checkout",
        proposes=["order-tracking"],
    )

    graph = build_graph(tmp_path)

    assert {r.id for r in graph.roles} == {"customer"}
    assert {p.id for p in graph.personas} == {"small-cafe-owner"}
    assert {j.id for j in graph.journeys} == {"first-time-checkout"}
    assert {n.id for n in graph.narratives} == {"rush-orders-not-lost"}
    assert graph.narratives[0].proposes == ["order-tracking"]
    # All cross-refs resolve — no integrity flags.
    assert graph.personas[0].integrity == []
    assert graph.journeys[0].integrity == []
    assert graph.narratives[0].integrity == []
