"""Per-entity Solera-root → model readers.

Every ``read_*`` here is idempotent: it rebuilds from the filesystem on each
call. Tolerant of malformed files — missing fields surface as empty defaults,
and integrity-relevant omissions are flagged so the Actors canvas can
prompt the human to repair the file.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from solera_mcp.models import (
    ActionItem,
    Concept,
    ConceptEdge,
    Identity,
    Journey,
    Milestone,
    Narrative,
    NarrativeForm,
    Persona,
    Release,
    Role,
    Story,
)
from solera_mcp.parsing import (
    coerce_id_list,
    extract_concept_id,
    normalize_identity_stem,
    parse_bullet_list,
    parse_frontmatter,
    parse_journey_steps_table,
    parse_sections,
    status_from_icon_or_text,
)

_log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Concepts
# ---------------------------------------------------------------------------


def read_concept_file(path: Path) -> Concept:
    text = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    sections = parse_sections(body)
    concept_id = fm.get("id") or path.stem
    parent = fm.get("parent")
    return Concept(
        id=concept_id,
        name=fm.get("name", concept_id.replace("-", " ").title()),
        status=fm.get("status", "active"),
        intent=sections.get("Intent", ""),
        current_design=sections.get("Current Design", ""),
        current_shape=sections.get("Current Shape", ""),
        horizon=sections.get("Horizon"),
        parent=str(parent) if parent else None,
    )


def read_concepts(workspace: Path) -> list[Concept]:
    concepts_dir = workspace / "concepts"
    if not concepts_dir.exists():
        return []
    results: list[Concept] = []
    for md in sorted(concepts_dir.glob("*.md")):
        if md.name == "_index.md":
            continue
        results.append(read_concept_file(md))
    return results


# ---------------------------------------------------------------------------
# Roles (v5.0+)
# ---------------------------------------------------------------------------


def read_role_file(path: Path) -> Role:
    text = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    sections = parse_sections(body)
    role_id = fm.get("id") or path.stem
    parent = fm.get("parent")
    return Role(
        id=str(role_id),
        name=fm.get("name", role_id.replace("-", " ").title()),
        status=fm.get("status", "active"),
        description=sections.get("Description", "").strip(),
        context=sections.get("Context", "").strip() or None,
        parent=str(parent) if parent else None,
    )


def read_roles(workspace: Path) -> list[Role]:
    roles_dir = workspace / "roles"
    if not roles_dir.exists():
        return []
    results: list[Role] = []
    for md in sorted(roles_dir.glob("*.md")):
        if md.name == "_index.md":
            continue
        results.append(read_role_file(md))
    return results


# ---------------------------------------------------------------------------
# Personas
# ---------------------------------------------------------------------------


def read_persona_file(path: Path) -> Persona:
    text = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    sections = parse_sections(body)
    persona_id = fm.get("id") or path.stem
    parent = fm.get("parent")
    role = fm.get("role")
    integrity: list[str] = []
    if not role:
        # v5.0 spec: every Persona must declare a Role. Missing `role` is
        # either a v4 legacy file (awaiting /solera-migrate-v4-to-v5) or a
        # human drafting mistake — surface as integrity so the canvas can
        # prompt a repair.
        _log.warning("Persona %s has no `role`; rendering as orphan.", path)
        integrity.append("missing_role")
    return Persona(
        id=str(persona_id),
        name=fm.get("name", persona_id.replace("-", " ").title()),
        status=fm.get("status", "active"),
        role=str(role) if role else "",
        identity=sections.get("Identity", "").strip(),
        goals=parse_bullet_list(sections.get("Goals", "")),
        pains=parse_bullet_list(sections.get("Pains", "")),
        triggers=parse_bullet_list(sections.get("Triggers", "")),
        quotes=parse_bullet_list(sections.get("Quotes", "")),
        channels=sections.get("Channels", "").strip() or None,
        parent=str(parent) if parent else None,
        integrity=integrity,
    )


def read_personas(workspace: Path) -> list[Persona]:
    personas_dir = workspace / "personas"
    if not personas_dir.exists():
        return []
    results: list[Persona] = []
    for md in sorted(personas_dir.glob("*.md")):
        if md.name == "_index.md":
            continue
        results.append(read_persona_file(md))
    return results


# ---------------------------------------------------------------------------
# Journeys
# ---------------------------------------------------------------------------


def read_journey_file(path: Path) -> Journey:
    text = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    sections = parse_sections(body)
    journey_id = fm.get("id") or path.stem
    walks = fm.get("walks")
    if not walks:
        # Tolerant read: surface the Journey with an empty `walks`. The Actors
        # canvas renders it as orphan; the human can fix the file via
        # solera-write-journey update.
        _log.warning("Journey %s has no `walks` Role id; rendering as orphan.", path)
    parent = fm.get("parent")
    integrity: list[str] = []
    if not walks:
        integrity.append("missing_walks")
    return Journey(
        id=str(journey_id),
        name=fm.get("name", journey_id.replace("-", " ").title()),
        status=fm.get("status", "active"),
        walks=str(walks) if walks else "",
        walked_by=coerce_id_list(fm.get("walked_by")),
        trigger=sections.get("Trigger", "").strip(),
        steps=parse_journey_steps_table(sections.get("Steps", "")),
        outcome=sections.get("Outcome", "").strip(),
        parent=str(parent) if parent else None,
        integrity=integrity,
    )


def read_journeys(workspace: Path) -> list[Journey]:
    journeys_dir = workspace / "journeys"
    if not journeys_dir.exists():
        return []
    results: list[Journey] = []
    for md in sorted(journeys_dir.glob("*.md")):
        if md.name == "_index.md":
            continue
        results.append(read_journey_file(md))
    return results


# ---------------------------------------------------------------------------
# Narratives
# ---------------------------------------------------------------------------


def read_narrative_file(path: Path) -> Narrative:
    text = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    sections = parse_sections(body)
    narrative_id = fm.get("id") or path.stem
    raw_form = fm.get("form", "user_story")
    form: NarrativeForm = (
        raw_form if raw_form in ("user_story", "jtbd", "scenario") else "user_story"
    )
    about_roles = coerce_id_list(fm.get("about_roles"))
    about_personas = coerce_id_list(fm.get("about_personas"))
    # v4 legacy compatibility: if only the old flat `about` key is present,
    # parse it into `about_roles` so the graph still renders something. The
    # integrity flag `legacy_about_field` cues the human to run the v4→v5
    # migration skill. Both keys present together → `about_roles` wins and
    # the legacy `about` is silently ignored (we assume the migration was
    # completed but the legacy field was left behind accidentally).
    integrity: list[str] = []
    if not about_roles and not about_personas and fm.get("about") is not None:
        about_roles = coerce_id_list(fm.get("about"))
        if about_roles:
            integrity.append("legacy_about_field")
    if not about_roles:
        # Spec requires 1+ active Role on `about_roles`. Surface as orphan so
        # the human can repair via `solera-write-narrative` update.
        _log.warning("Narrative %s has empty `about_roles` list; rendering as orphan.", path)
        integrity.append("missing_about_roles")
    return Narrative(
        id=str(narrative_id),
        form=form,
        status=fm.get("status", "active"),
        statement=sections.get("Statement", "").strip(),
        context=sections.get("Context", "").strip(),
        acceptance_cues=parse_bullet_list(sections.get("Acceptance Cues", "")),
        about_roles=about_roles,
        about_personas=about_personas,
        in_journey=str(fm["in_journey"]) if fm.get("in_journey") else None,
        proposes=coerce_id_list(fm.get("proposes")),
        integrity=integrity,
    )


def read_narratives(workspace: Path) -> list[Narrative]:
    narratives_dir = workspace / "narratives"
    if not narratives_dir.exists():
        return []
    results: list[Narrative] = []
    for md in sorted(narratives_dir.glob("*.md")):
        if md.name == "_index.md":
            continue
        results.append(read_narrative_file(md))
    return results


# ---------------------------------------------------------------------------
# Concept edges
# ---------------------------------------------------------------------------


def read_concept_graph(workspace: Path) -> list[ConceptEdge]:
    path = workspace / "concept-graph.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    edges: list[ConceptEdge] = []
    for i, e in enumerate(data.get("edges", [])):
        edges.append(
            ConceptEdge(
                id=f"{e['from']}--{e['to']}--{i}",
                **{"from": e["from"], "to": e["to"]},
                label=e.get("label", ""),
                created=e.get("created"),
            )
        )
    return edges


# ---------------------------------------------------------------------------
# Milestones
# ---------------------------------------------------------------------------


def read_milestone_file(path: Path) -> Milestone:
    text = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    sections = parse_sections(body)
    milestone_id = fm.get("id") or path.stem
    scope_lines = sections.get("Scope", "")
    scope = [
        extract_concept_id(line)
        for line in scope_lines.splitlines()
        if line.strip().startswith("-")
    ]
    return Milestone(
        id=milestone_id,
        name=fm.get("name", milestone_id),
        status=fm.get("status", "proposed"),
        scope=[s for s in scope if s],
    )


def read_milestones(workspace: Path) -> list[Milestone]:
    ms_dir = workspace / "milestones"
    if not ms_dir.exists():
        return []
    results: list[Milestone] = []
    for md in sorted(ms_dir.glob("*.md")):
        if md.name == "_index.md":
            continue
        results.append(read_milestone_file(md))
    return results


# ---------------------------------------------------------------------------
# Stories + Action Items
# ---------------------------------------------------------------------------


def read_story_file(path: Path) -> tuple[Story, list[ActionItem]]:
    text = path.read_text(encoding="utf-8")
    fm, _body = parse_frontmatter(text)
    # Solera field names evolved — tolerate both `id`/`name` and `story_id`/`story_name`.
    story_id = fm.get("id") or fm.get("story_id") or path.parent.name
    story_name = fm.get("name") or fm.get("story_name") or path.parent.name
    contributes_to_raw = fm.get("contributes_to") or []
    if isinstance(contributes_to_raw, str):
        contributes_to = [contributes_to_raw]
    else:
        contributes_to = list(contributes_to_raw)
    story = Story(
        id=str(story_id),
        name=str(story_name),
        story_type=fm.get("type", "US"),
        status=status_from_icon_or_text(fm.get("status")),
        contributes_to=contributes_to,
        belongs_to=fm.get("belongs_to"),
    )
    acts: list[ActionItem] = []
    for act_md in sorted(path.parent.glob("ACT-*.md")):
        acts.append(_read_action_item(act_md, story.id))
    return story, acts


def _read_action_item(path: Path, story_id: str) -> ActionItem:
    text = path.read_text(encoding="utf-8")
    fm, _body = parse_frontmatter(text)
    act_id = fm.get("id") or path.stem.split("-", 2)[0] + "-" + path.stem.split("-", 2)[1]
    depends_on_raw = fm.get("depends_on") or []
    if isinstance(depends_on_raw, str):
        depends_on = [depends_on_raw]
    else:
        depends_on = list(depends_on_raw)
    return ActionItem(
        story_id=story_id,
        id=act_id,
        name=fm.get("name", path.stem),
        status=status_from_icon_or_text(fm.get("status")),
        depends_on=depends_on,
    )


def read_stories(workspace: Path) -> tuple[list[Story], list[ActionItem]]:
    stories_dir = workspace / "stories"
    if not stories_dir.exists():
        return [], []
    stories: list[Story] = []
    acts: list[ActionItem] = []
    for story_dir in sorted(p for p in stories_dir.iterdir() if p.is_dir()):
        story_md = story_dir / "_story.md"
        if not story_md.exists():
            continue
        story, story_acts = read_story_file(story_md)
        stories.append(story)
        acts.extend(story_acts)
    return stories, acts


# ---------------------------------------------------------------------------
# Identity
# ---------------------------------------------------------------------------


_IDENTITY_ALIASES: dict[str, tuple[str, ...]] = {
    # canonical field → recognized filename stems (first match wins)
    "mission": ("mission",),
    "vision": ("vision",),
    "values": ("core-values", "values"),
    "goals": ("goals",),
    "tone_and_manner": ("tone-and-manner", "tone", "voice"),
}


def _read_identity_body(path: Path) -> str | None:
    if not path.exists():
        return None
    _fm, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    return body.strip() or None


def read_identity(workspace: Path) -> Identity | None:
    id_dir = workspace / "identity"
    if not id_dir.exists():
        return None

    files = list(id_dir.glob("*.md"))
    if not files:
        return None

    # Index files by normalized stem ("vision_1" → "vision") to tolerate the
    # "_N" suffixes Obsidian appends when duplicating notes.
    by_stem: dict[str, Path] = {}
    for f in files:
        by_stem.setdefault(normalize_identity_stem(f.stem), f)

    picked: dict[str, str | None] = {}
    consumed: set[str] = set()
    for field, aliases in _IDENTITY_ALIASES.items():
        for alias in aliases:
            if alias in by_stem:
                picked[field] = _read_identity_body(by_stem[alias])
                consumed.add(alias)
                break
        picked.setdefault(field, None)

    extras: dict[str, str] = {}
    for stem, path in by_stem.items():
        if stem in consumed:
            continue
        body = _read_identity_body(path)
        if body:
            extras[stem] = body

    return Identity(
        mission=picked["mission"],
        vision=picked["vision"],
        values=picked["values"],
        goals=picked["goals"],
        tone_and_manner=picked["tone_and_manner"],
        extras=extras,
    )


# ---------------------------------------------------------------------------
# Releases
# ---------------------------------------------------------------------------


def read_releases(workspace: Path) -> list[Release]:
    releases_dir = workspace / "releases"
    if not releases_dir.exists():
        return []
    results: list[Release] = []
    for tag_dir in sorted(p for p in releases_dir.iterdir() if p.is_dir()):
        marker = tag_dir / ".released"
        if not marker.exists():
            continue
        meta: dict[str, str] = {}
        for line in marker.read_text(encoding="utf-8").splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                meta[k.strip()] = v.strip()
        results.append(
            Release(
                tag=meta.get("release_tag", tag_dir.name),
                milestone_id=meta.get("milestone_id"),
                released_at=meta.get("released_at"),
            )
        )
    return results
