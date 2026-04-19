"""Parse a Solera workspace into a typed graph.

The graph is the source of truth the HTTP layer and the MCP tools hand out.
Reads are idempotent — every call rebuilds from the filesystem. A future phase
adds an SQLite cache layer and a file watcher; for now, correctness first.

Data origin (paths relative to the Solera root, which is `.solera/` in v4 and
`workspace/` in the deprecated v3 fallback):

- `identity/*.md`                       → Identity
- `concepts/*.md`                       → Concept (Living axis)
- `concept-graph.json`                  → Concept ↔ Concept edges (solera-map only)
- `milestones/*.md`                     → Milestone (Time-bound)
- `stories/{id}/_story.md`              → Story (Time-bound)
- `stories/{id}/ACT-*.md`               → ActionItem
- `releases/{tag}/.released`            → Release (Immutable)
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

_log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

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
    the graph). Set during :func:`build_graph`'s integrity pass.
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


# ---------------------------------------------------------------------------
# Markdown helpers
# ---------------------------------------------------------------------------

_FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n?", re.DOTALL)
_SECTION_RE = re.compile(r"^# (.+?)\n(.*?)(?=\n# |\Z)", re.MULTILINE | re.DOTALL)
_WIKILINK_RE = re.compile(r"\[\[[^\]]*?/?([\w.-]+?)(?:\|[^\]]*)?\]\]")


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Split a markdown file into (frontmatter dict, body).

    Malformed YAML frontmatter yields an empty dict and a warning log — real
    Solera workspaces contain hand-edited files where quoting slipped, and we
    prefer to surface them as under-populated nodes over hard-failing the read.
    """
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    try:
        fm = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as exc:
        _log.warning("malformed frontmatter: %s", exc)
        return {}, text[match.end() :]
    if not isinstance(fm, dict):
        return {}, text[match.end() :]
    return fm, text[match.end() :]


def parse_sections(body: str) -> dict[str, str]:
    """Split body by top-level `# Heading` blocks. Returns {heading: content}."""
    out: dict[str, str] = {}
    for m in _SECTION_RE.finditer(body):
        out[m.group(1).strip()] = m.group(2).strip()
    return out


def _status_from_icon_or_text(raw: str | None) -> WorkStatus:
    if not raw:
        return "pending"
    raw = raw.strip()
    for icon, status in STATUS_ICON_MAP.items():
        if icon in raw:
            return status
    lowered = raw.lower().replace("-", "_").replace(" ", "_")
    if lowered in ("pending", "in_progress", "complete", "on_hold", "cancelled"):
        return lowered  # type: ignore[return-value]
    return "pending"


# ---------------------------------------------------------------------------
# Readers
# ---------------------------------------------------------------------------


def update_concept_frontmatter(path: Path, updates: dict[str, Any]) -> None:
    """Merge `updates` into the Concept file's frontmatter and rewrite.

    - Keys with value `None` are **removed** from frontmatter.
    - Keys with any other value **overwrite**.
    - Frontmatter ordering is preserved for keys that already existed; new
      keys append to the end.
    - The body (everything after the second `---`) is left untouched.
    - If the file has no frontmatter, a new block is inserted at the top.
    """
    text = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    for key, value in updates.items():
        if value is None:
            fm.pop(key, None)
        else:
            fm[key] = value
    dumped = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False).strip()
    new_text = f"---\n{dumped}\n---\n{body}" if dumped else body
    path.write_text(new_text, encoding="utf-8")


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
# Living-axis helpers (Personas, Journeys, Narratives)
# ---------------------------------------------------------------------------


def _parse_bullet_list(section_text: str) -> list[str]:
    """Extract leading-`-` bullet items from a section body.

    Strips the leading `- ` and any trailing whitespace. Skips blank lines and
    HTML comment lines. Multi-line continuations of a bullet are not joined —
    a hand-edited Persona is unlikely to have them, and merging them would
    change the user's text without consent.
    """
    out: list[str] = []
    for raw in section_text.splitlines():
        line = raw.rstrip()
        if not line.lstrip().startswith("-"):
            continue
        text = line.lstrip()[1:].strip()
        if not text or text.startswith("<!--"):
            continue
        out.append(text)
    return out


_JOURNEY_STEP_ROW_RE = re.compile(
    r"^\|\s*(?P<n>\d+)\s*\|"
    r"\s*(?P<stage>[^|]*?)\s*\|"
    r"\s*(?P<step>[^|]*?)\s*\|"
    r"\s*(?P<touchpoint>[^|]*?)\s*\|"
    r"\s*(?P<emotion>[^|]*?)\s*\|"
    r"\s*(?P<pain>[^|]*?)\s*\|\s*$"
)


def _parse_journey_steps_table(section_text: str) -> list[JourneyStep]:
    """Parse the Steps markdown table in a Journey file.

    Skips the header row (`| # | Stage | ...`) and the separator (`|---|---|...`).
    Tolerates malformed rows by skipping them; never raises.
    """
    steps: list[JourneyStep] = []
    for line in section_text.splitlines():
        # Filter out header / separator / non-data rows.
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if "---" in stripped:
            continue
        # Skip the header row (first cell is non-numeric like "#").
        match = _JOURNEY_STEP_ROW_RE.match(stripped)
        if not match:
            continue
        try:
            n = int(match.group("n"))
        except ValueError:
            continue
        steps.append(
            JourneyStep(
                n=n,
                stage=match.group("stage"),
                step=match.group("step"),
                touchpoint=match.group("touchpoint"),
                emotion=match.group("emotion"),
                pain=match.group("pain"),
            )
        )
    return steps


def _coerce_id_list(raw: Any) -> list[str]:
    """Frontmatter list fields may be a YAML list, a single string, or absent."""
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, list):
        return [str(item) for item in raw if item is not None]
    return []


def read_persona_file(path: Path) -> Persona:
    text = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    sections = parse_sections(body)
    persona_id = fm.get("id") or path.stem
    parent = fm.get("parent")
    return Persona(
        id=str(persona_id),
        name=fm.get("name", persona_id.replace("-", " ").title()),
        status=fm.get("status", "active"),
        identity=sections.get("Identity", "").strip(),
        goals=_parse_bullet_list(sections.get("Goals", "")),
        pains=_parse_bullet_list(sections.get("Pains", "")),
        triggers=_parse_bullet_list(sections.get("Triggers", "")),
        quotes=_parse_bullet_list(sections.get("Quotes", "")),
        channels=sections.get("Channels", "").strip() or None,
        parent=str(parent) if parent else None,
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


def read_journey_file(path: Path) -> Journey:
    text = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    sections = parse_sections(body)
    journey_id = fm.get("id") or path.stem
    walks = fm.get("walks")
    if not walks:
        # Tolerant read: surface the Journey with an empty `walks`. The Service
        # canvas renders it as orphan; the human can fix the file via
        # solera-write-journey update.
        _log.warning("Journey %s has no `walks` Persona id; rendering as orphan.", path)
    parent = fm.get("parent")
    integrity: list[str] = []
    if not walks:
        integrity.append("missing_walks")
    return Journey(
        id=str(journey_id),
        name=fm.get("name", journey_id.replace("-", " ").title()),
        status=fm.get("status", "active"),
        walks=str(walks) if walks else "",
        trigger=sections.get("Trigger", "").strip(),
        steps=_parse_journey_steps_table(sections.get("Steps", "")),
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


def read_narrative_file(path: Path) -> Narrative:
    text = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    sections = parse_sections(body)
    narrative_id = fm.get("id") or path.stem
    raw_form = fm.get("form", "user_story")
    form: NarrativeForm = (
        raw_form if raw_form in ("user_story", "jtbd", "scenario") else "user_story"
    )
    about = _coerce_id_list(fm.get("about"))
    integrity: list[str] = []
    if not about:
        # Spec requires 1+ active Personas on `about`. Surface as orphan so the
        # human can repair via `solera-write-narrative` update.
        _log.warning("Narrative %s has empty `about` list; rendering as orphan.", path)
        integrity.append("missing_about")
    return Narrative(
        id=str(narrative_id),
        form=form,
        status=fm.get("status", "active"),
        statement=sections.get("Statement", "").strip(),
        context=sections.get("Context", "").strip(),
        acceptance_cues=_parse_bullet_list(sections.get("Acceptance Cues", "")),
        about=about,
        in_journey=str(fm["in_journey"]) if fm.get("in_journey") else None,
        proposes=_coerce_id_list(fm.get("proposes")),
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


def read_layout(workspace: Path) -> dict[str, Any]:
    """Read `_views/map-layout.json` or return an empty layout."""
    path = workspace / "_views" / "map-layout.json"
    if not path.exists():
        return {"nodes": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        _log.warning("malformed map-layout.json at %s; ignoring", path)
        return {"nodes": {}}
    if not isinstance(data, dict):
        return {"nodes": {}}
    nodes = data.get("nodes") or {}
    return {"nodes": nodes if isinstance(nodes, dict) else {}}


def write_layout(workspace: Path, layout: dict[str, Any]) -> None:
    """Persist a layout dict to `_views/map-layout.json` (pretty JSON).

    The schema is `{"nodes": {"<node_id>": {"x": float, "y": float}, ...}}`.
    Arbitrary extra keys are allowed and preserved.
    """
    views_dir = workspace / "_views"
    views_dir.mkdir(parents=True, exist_ok=True)
    path = views_dir / "map-layout.json"
    path.write_text(
        json.dumps(layout, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _extract_concept_id(bullet_line: str) -> str:
    """Pull a Concept id out of a Scope bullet.

    Accepted shapes:
        - authentication
        - [[../concepts/authentication]]
        - [[../concepts/authentication]] — annotation
        - [[../concepts/authentication|label]] — annotation
    """
    stripped = bullet_line.lstrip("- ").strip()
    wikilink = _WIKILINK_RE.search(stripped)
    if wikilink:
        return wikilink.group(1)
    # Bare id, optionally followed by em-dash annotation.
    return stripped.split("—")[0].split(" ")[0].strip()


def read_milestone_file(path: Path) -> Milestone:
    text = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    sections = parse_sections(body)
    milestone_id = fm.get("id") or path.stem
    scope_lines = sections.get("Scope", "")
    scope = [
        _extract_concept_id(line)
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
        status=_status_from_icon_or_text(fm.get("status")),
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
        status=_status_from_icon_or_text(fm.get("status")),
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
    def _norm(stem: str) -> str:
        return re.sub(r"_\d+$", "", stem).lower()

    by_stem: dict[str, Path] = {}
    for f in files:
        by_stem.setdefault(_norm(f.stem), f)

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


# ---------------------------------------------------------------------------
# Aggregate
# ---------------------------------------------------------------------------


def build_graph(workspace: Path) -> Graph:
    """Read everything under the Solera root and assemble a `Graph`.

    `workspace` is the directory returned by `resolve_solera_root` —
    typically `<project>/.solera/` (v4) or `<project>/workspace/` (v3 fallback).
    The parameter name is historical; it points at whichever layout exists.
    """
    stories, action_items = read_stories(workspace)
    journeys = read_journeys(workspace)
    narratives = read_narratives(workspace)
    _annotate_cross_ref_integrity(journeys, narratives)
    return Graph(
        identity=read_identity(workspace),
        personas=read_personas(workspace),
        journeys=journeys,
        narratives=narratives,
        concepts=read_concepts(workspace),
        concept_edges=read_concept_graph(workspace),
        milestones=read_milestones(workspace),
        stories=stories,
        action_items=action_items,
        releases=read_releases(workspace),
    )


def _annotate_cross_ref_integrity(
    journeys: list[Journey], narratives: list[Narrative]
) -> None:
    """Second pass: flag cross-entity reference breaks.

    Per-file :func:`read_*_file` only sees one file at a time, so refs like
    ``Narrative.in_journey`` can only be validated once every file has been
    read. This pass appends ``broken_in_journey_ref`` where applicable; other
    cross-ref flags can be added here without touching the single-file readers.
    """
    journey_ids = {j.id for j in journeys}
    for n in narratives:
        if n.in_journey and n.in_journey not in journey_ids:
            if "broken_in_journey_ref" not in n.integrity:
                n.integrity.append("broken_in_journey_ref")
