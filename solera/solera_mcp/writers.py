"""Filesystem writers for the Solera workspace.

Keeps file-mutating code isolated from the pure readers so tests can run
read-only paths without touching the writer surface.

v5.1 expands this module from "Concept frontmatter only" to a unified
CRUD surface across every Living-axis entity. Each kind (Role, Persona,
Journey, Narrative, Concept) has:

- ``update_{kind}(path, patch)`` — merges a patch dict into the file,
  classifying each key as either frontmatter or body-section and
  applying both in one atomic rewrite.
- ``create_{kind}(workspace, payload)`` — writes a brand-new file with
  the required frontmatter + section scaffolding derived from ``payload``.

Cross-reference validation (e.g., "Persona.role must exist") lives in the
HTTP endpoint layer, not here — the writers trust their inputs.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import yaml

from solera_mcp.parsing import parse_frontmatter

_log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Core primitives: frontmatter + body-section manipulation
# ---------------------------------------------------------------------------


def _serialise(fm: dict[str, Any], body: str) -> str:
    """Render frontmatter + body back to a full markdown file string."""
    # Normalise the body to always end with exactly one newline.
    body = body.rstrip("\n") + "\n"
    if not fm:
        return body
    dumped = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False).strip()
    return f"---\n{dumped}\n---\n\n{body}"


def _update_sections(body: str, section_patch: dict[str, str | None]) -> str:
    """Rewrite named H1 sections in ``body``.

    For each ``(heading, content)`` in ``section_patch``:

    - If ``content is None`` → remove the whole section (heading + its
      body until the next top-level heading).
    - If the heading exists → replace its body (keep the heading line).
    - If the heading is new → append a new section at the end of the body.

    Other sections and free-form prose outside any heading are preserved.
    """
    if not section_patch:
        return body

    # Partition the body into a sequence of (heading | None, block_text).
    # The text before any H1 heading has heading=None; each H1 starts a
    # new block. Preserves the original spacing between blocks.
    blocks: list[tuple[str | None, str]] = []
    current_heading: str | None = None
    current_lines: list[str] = []
    for line in body.splitlines(keepends=True):
        m = re.match(r"^# (.+?)\s*$", line.rstrip("\n"))
        if m:
            # Flush the previous block.
            blocks.append((current_heading, "".join(current_lines)))
            current_heading = m.group(1).strip()
            current_lines = []
        else:
            current_lines.append(line)
    blocks.append((current_heading, "".join(current_lines)))

    # Apply the patch.
    updated: list[tuple[str | None, str]] = []
    applied: set[str] = set()
    for heading, block_text in blocks:
        if heading is not None and heading in section_patch:
            new_content = section_patch[heading]
            if new_content is None:
                # Delete this section.
                applied.add(heading)
                continue
            applied.add(heading)
            # Normalise trailing newlines on the new content so blocks are
            # separated by a blank line.
            new_content = new_content.rstrip("\n") + "\n\n"
            updated.append((heading, new_content))
        else:
            updated.append((heading, block_text))

    # Append any new sections that weren't in the original body.
    for heading, content in section_patch.items():
        if content is None:
            continue
        if heading in applied:
            continue
        content_norm = content.rstrip("\n") + "\n\n"
        updated.append((heading, content_norm))

    # Reassemble.
    parts: list[str] = []
    for heading, block_text in updated:
        if heading is None:
            parts.append(block_text)
        else:
            parts.append(f"# {heading}\n{block_text}")
    return "".join(parts)


def _patch_file(
    path: Path,
    frontmatter_patch: dict[str, Any],
    section_patch: dict[str, str | None],
) -> None:
    """Apply the frontmatter + section patches to an existing entity file."""
    text = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    for key, value in frontmatter_patch.items():
        if value is None:
            fm.pop(key, None)
        else:
            fm[key] = value
    new_body = _update_sections(body, section_patch)
    path.write_text(_serialise(fm, new_body), encoding="utf-8")


# ---------------------------------------------------------------------------
# Bullet list and Journey Steps table rendering
# ---------------------------------------------------------------------------


def _render_bullet_list(items: list[str] | None) -> str:
    """``['a', 'b']`` → ``"- a\\n- b\\n"``. Empty list → placeholder comment."""
    if not items:
        return "<!-- empty — fill via solera-write-* or by editing this file -->\n"
    return "".join(f"- {item}\n" for item in items)


def _render_steps_table(
    steps: list[dict[str, Any]] | None,
) -> str:
    """Render a Journey Steps list-of-dicts as a markdown table."""
    header = (
        "| # | Stage | Step | Touchpoint | Emotion | Pain |\n"
        "|---|-------|------|------------|---------|------|\n"
    )
    if not steps:
        return header
    rows = []
    for s in steps:
        n = s.get("n", 0)
        stage = s.get("stage", "")
        step = s.get("step", "")
        touchpoint = s.get("touchpoint", "")
        emotion = s.get("emotion", "")
        pain = s.get("pain", "—")
        rows.append(f"| {int(n):02d} | {stage} | {step} | {touchpoint} | {emotion} | {pain} |\n")
    return header + "".join(rows)


# ---------------------------------------------------------------------------
# Concept — existing (kept for back-compat) + updated to support body sections
# ---------------------------------------------------------------------------


def update_concept_frontmatter(path: Path, updates: dict[str, Any]) -> None:
    """Merge ``updates`` into the Concept file's frontmatter.

    Preserved from v4.x for tests and callers that only need to flip
    frontmatter keys (e.g. ``parent``). Use :func:`update_concept` for
    combined frontmatter + body edits.
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


CONCEPT_FM_KEYS = {"name", "status", "parent"}
CONCEPT_BODY_SECTIONS = {
    "intent": "Intent",
    "current_design": "Current Design",
    "current_shape": "Current Shape",
    "horizon": "Horizon",
}


def update_concept(path: Path, patch: dict[str, Any]) -> None:
    """Apply a Concept PATCH mixing frontmatter + body-section keys."""
    fm_patch, sec_patch = _split_patch(patch, CONCEPT_FM_KEYS, CONCEPT_BODY_SECTIONS)
    _patch_file(path, fm_patch, sec_patch)


def create_concept(workspace: Path, payload: dict[str, Any]) -> Path:
    """Write a new Concept file. Returns the written path."""
    concept_id = payload["id"]
    target = workspace / "concepts" / f"{concept_id}.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    fm = {
        "id": concept_id,
        "name": payload.get("name", concept_id.replace("-", " ").title()),
        "status": payload.get("status", "active"),
        "created": payload.get("created"),
    }
    if payload.get("parent"):
        fm["parent"] = payload["parent"]
    fm = {k: v for k, v in fm.items() if v is not None}
    body_sections = {
        "Intent": payload.get("intent", ""),
        "Current Design": payload.get("current_design", ""),
        "Current Shape": payload.get("current_shape", ""),
    }
    if payload.get("horizon"):
        body_sections["Horizon"] = payload["horizon"]
    body = "".join(f"# {h}\n{content}\n\n" for h, content in body_sections.items())
    target.write_text(_serialise(fm, body), encoding="utf-8")
    return target


# ---------------------------------------------------------------------------
# Role
# ---------------------------------------------------------------------------

ROLE_FM_KEYS = {"name", "status", "parent"}
ROLE_BODY_SECTIONS = {"description": "Description", "context": "Context"}


def update_role(path: Path, patch: dict[str, Any]) -> None:
    fm_patch, sec_patch = _split_patch(patch, ROLE_FM_KEYS, ROLE_BODY_SECTIONS)
    _patch_file(path, fm_patch, sec_patch)


def create_role(workspace: Path, payload: dict[str, Any]) -> Path:
    role_id = payload["id"]
    target = workspace / "roles" / f"{role_id}.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    fm: dict[str, Any] = {
        "id": role_id,
        "kind": "role",
        "name": payload.get("name", role_id.replace("-", " ").title()),
        "status": payload.get("status", "active"),
        "created": payload.get("created"),
    }
    if payload.get("parent"):
        fm["parent"] = payload["parent"]
    fm = {k: v for k, v in fm.items() if v is not None}
    body = f"# Description\n{payload.get('description', '')}\n\n"
    if payload.get("context"):
        body += f"# Context\n{payload['context']}\n\n"
    target.write_text(_serialise(fm, body), encoding="utf-8")
    return target


# ---------------------------------------------------------------------------
# Persona — identity + four bullet-list body sections + Channels prose
# ---------------------------------------------------------------------------

PERSONA_FM_KEYS = {"name", "status", "role", "parent"}
# Persona body fields: identity is prose, goals/pains/triggers/quotes are
# bullet lists, channels is prose again. Keys here are patch-facing;
# section headings match the template.
PERSONA_SIMPLE_BODY_SECTIONS = {"identity": "Identity", "channels": "Channels"}
PERSONA_BULLET_BODY_SECTIONS = {
    "goals": "Goals",
    "pains": "Pains",
    "triggers": "Triggers",
    "quotes": "Quotes",
}


def update_persona(path: Path, patch: dict[str, Any]) -> None:
    fm_patch, sec_patch = _split_patch(patch, PERSONA_FM_KEYS, PERSONA_SIMPLE_BODY_SECTIONS)
    # Additional bullet-list sections: render lists to markdown.
    for patch_key, heading in PERSONA_BULLET_BODY_SECTIONS.items():
        if patch_key in patch:
            value = patch[patch_key]
            sec_patch[heading] = None if value is None else _render_bullet_list(value)
    _patch_file(path, fm_patch, sec_patch)


def create_persona(workspace: Path, payload: dict[str, Any]) -> Path:
    persona_id = payload["id"]
    target = workspace / "personas" / f"{persona_id}.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    fm: dict[str, Any] = {
        "id": persona_id,
        "kind": "persona",
        "name": payload.get("name", persona_id.replace("-", " ").title()),
        "status": payload.get("status", "active"),
        "created": payload.get("created"),
        "role": payload["role"],
    }
    if payload.get("parent"):
        fm["parent"] = payload["parent"]
    fm = {k: v for k, v in fm.items() if v is not None}
    body = f"# Identity\n{payload.get('identity', '')}\n\n"
    for patch_key, heading in PERSONA_BULLET_BODY_SECTIONS.items():
        body += f"# {heading}\n{_render_bullet_list(payload.get(patch_key, []))}\n"
    if payload.get("channels"):
        body += f"# Channels\n{payload['channels']}\n\n"
    target.write_text(_serialise(fm, body), encoding="utf-8")
    return target


# ---------------------------------------------------------------------------
# Journey — Trigger / Outcome prose + Steps markdown table
# ---------------------------------------------------------------------------

JOURNEY_FM_KEYS = {"name", "status", "walks", "walked_by", "parent"}
JOURNEY_SIMPLE_BODY_SECTIONS = {"trigger": "Trigger", "outcome": "Outcome"}


def update_journey(path: Path, patch: dict[str, Any]) -> None:
    fm_patch, sec_patch = _split_patch(patch, JOURNEY_FM_KEYS, JOURNEY_SIMPLE_BODY_SECTIONS)
    if "steps" in patch:
        steps = patch["steps"]
        sec_patch["Steps"] = None if steps is None else _render_steps_table(steps)
    _patch_file(path, fm_patch, sec_patch)


def create_journey(workspace: Path, payload: dict[str, Any]) -> Path:
    journey_id = payload["id"]
    target = workspace / "journeys" / f"{journey_id}.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    fm: dict[str, Any] = {
        "id": journey_id,
        "kind": "journey",
        "name": payload.get("name", journey_id.replace("-", " ").title()),
        "status": payload.get("status", "active"),
        "created": payload.get("created"),
        "walks": payload["walks"],
    }
    if payload.get("walked_by"):
        fm["walked_by"] = payload["walked_by"]
    if payload.get("parent"):
        fm["parent"] = payload["parent"]
    fm = {k: v for k, v in fm.items() if v is not None}
    body = (
        f"# Trigger\n{payload.get('trigger', '')}\n\n"
        f"# Steps\n{_render_steps_table(payload.get('steps', []))}\n"
        f"# Outcome\n{payload.get('outcome', '')}\n\n"
    )
    target.write_text(_serialise(fm, body), encoding="utf-8")
    return target


# ---------------------------------------------------------------------------
# Narrative — Statement / Context prose + Acceptance Cues bullets
# ---------------------------------------------------------------------------

NARRATIVE_FM_KEYS = {
    "name",
    "status",
    "form",
    "about_roles",
    "about_personas",
    "in_journey",
    "proposes",
}
NARRATIVE_SIMPLE_BODY_SECTIONS = {"statement": "Statement", "context": "Context"}


def update_narrative(path: Path, patch: dict[str, Any]) -> None:
    fm_patch, sec_patch = _split_patch(patch, NARRATIVE_FM_KEYS, NARRATIVE_SIMPLE_BODY_SECTIONS)
    if "acceptance_cues" in patch:
        cues = patch["acceptance_cues"]
        sec_patch["Acceptance Cues"] = None if cues is None else _render_bullet_list(cues)
    _patch_file(path, fm_patch, sec_patch)


def create_narrative(workspace: Path, payload: dict[str, Any]) -> Path:
    narrative_id = payload["id"]
    target = workspace / "narratives" / f"{narrative_id}.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    fm: dict[str, Any] = {
        "id": narrative_id,
        "kind": "narrative",
        "form": payload.get("form", "user_story"),
        "status": payload.get("status", "active"),
        "created": payload.get("created"),
        "about_roles": payload["about_roles"],
    }
    if payload.get("about_personas"):
        fm["about_personas"] = payload["about_personas"]
    if payload.get("in_journey"):
        fm["in_journey"] = payload["in_journey"]
    if payload.get("proposes"):
        fm["proposes"] = payload["proposes"]
    fm = {k: v for k, v in fm.items() if v is not None}
    body = (
        f"# Statement\n{payload.get('statement', '')}\n\n"
        f"# Context\n{payload.get('context', '')}\n\n"
        f"# Acceptance Cues\n"
        f"{_render_bullet_list(payload.get('acceptance_cues', []))}\n"
    )
    target.write_text(_serialise(fm, body), encoding="utf-8")
    return target


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _split_patch(
    patch: dict[str, Any],
    fm_keys: set[str],
    body_sections: dict[str, str],
) -> tuple[dict[str, Any], dict[str, str | None]]:
    """Partition a patch dict into frontmatter updates and body-section rewrites.

    ``body_sections`` maps a patch-facing key (``description``) to the
    H1 heading it writes to (``Description``). Keys not present in either
    set are silently ignored — the HTTP layer has already filtered them
    against an allowlist.
    """
    fm_patch: dict[str, Any] = {}
    sec_patch: dict[str, str | None] = {}
    for key, value in patch.items():
        if key in fm_keys:
            fm_patch[key] = value
        elif key in body_sections:
            sec_patch[body_sections[key]] = value
    return fm_patch, sec_patch


# ---------------------------------------------------------------------------
# Layout JSON (unchanged from v4.x)
# ---------------------------------------------------------------------------


def read_layout(workspace: Path) -> dict[str, Any]:
    """Read ``_views/map-layout.json`` or return an empty layout.

    Kept alongside :func:`write_layout` rather than in :mod:`readers` because
    layout I/O is an opaque blob of canvas state, not a typed model like the
    other readers produce.
    """
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
    """Persist a layout dict to ``_views/map-layout.json`` (pretty JSON).

    The schema is ``{"nodes": {"<node_id>": {"x": float, "y": float}, ...}}``.
    Arbitrary extra keys are allowed and preserved.
    """
    views_dir = workspace / "_views"
    views_dir.mkdir(parents=True, exist_ok=True)
    path = views_dir / "map-layout.json"
    path.write_text(
        json.dumps(layout, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
