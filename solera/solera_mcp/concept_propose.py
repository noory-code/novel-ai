"""POST /api/concept/propose-from-narrative — stub-Concept creation from a Narrative.

Surfaces the Service canvas's "Propose as Concept" action ergonomically
WITHOUT bypassing the Moment 1 collaboration rule (`solera/skills/
solera-write-concept/SKILL.md` — "AI must not invent the Intent"). Behavior:

1. Validate the named Narrative exists.
2. Validate the proposed concept_id does NOT already exist (this endpoint
   creates a stub; updates go through ``PATCH /api/concept/{id}`` or a
   direct ``solera-write-concept update`` invocation).
3. Write a stub Concept whose ``# Intent`` is explicitly flagged
   "needs human review per solera-write-concept Moment 1 rule" — the human
   must run ``solera-write-concept`` in ``update`` mode to fill the real
   Intent.
4. Append the new concept_id to the Narrative's ``proposes:`` frontmatter.
5. Return the path of the new Concept file.

What the endpoint does NOT do: finalize the Concept; copy the full Workflow
section from concept-template.md (solera-map does not vendor solera plugin
assets — the Workflow is added by ``solera-write-concept update``);
validate axes-and-status invariants beyond the create-vs-update distinction.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import yaml
from starlette.requests import Request
from starlette.responses import JSONResponse

from solera_mcp.parsing import parse_frontmatter
from solera_mcp.workspace import resolve_solera_root

_VALID_KEBAB_RE = re.compile(r"^[a-z][a-z0-9-]{0,62}[a-z0-9]$")


def stub_concept_body(narrative_id: str, today: str) -> str:
    """Body of a stub Concept created from a Narrative proposal.

    Intentionally MINIMAL. The ``# Intent`` is the Moment 1 guardrail —
    flagged "needs human review" so a casual reader cannot mistake it for
    a real Intent. The ``## Workflow`` section is INTENTIONALLY OMITTED
    here; running ``solera-write-concept`` in ``update`` mode will inject
    the canonical Workflow from solera's ``concept-template.md``.
    """
    return (
        f"# Intent\n"
        f"(proposed from narrative `{narrative_id}` on {today} — "
        f"needs human review per solera-write-concept Moment 1 rule)\n"
        f"\n"
        f"# Current Design\n"
        f"\n"
        f"# Current Shape\n"
        f"(no Stories have contributed yet)\n"
        f"\n"
        f"# Horizon\n"
        f"(not set yet)\n"
        f"\n"
        f"# Health\n"
        f"(no signals yet)\n"
        f"\n"
        f"# Contributions\n"
        f"| Story | What it left behind | Date |\n"
        f"|-------|---------------------|------|\n"
        f"\n"
        f"# Related Artifacts\n"
        f"\n"
        f"# Proposed From Narratives\n"
        f"- [[narrative/{narrative_id}]]\n"
        f"\n"
        f"<!-- Stub created by solera-map propose-from-narrative on {today}.\n"
        f"     Run `solera-write-concept` in `update` mode to fill Intent and\n"
        f"     install the canonical ## Workflow section. -->\n"
    )


def append_to_narrative_proposes(narrative_path: Path, concept_id: str) -> None:
    """Add ``concept_id`` to a Narrative's frontmatter ``proposes:`` list (idempotent).

    Reads the existing list (if any), appends if absent, rewrites the
    frontmatter while preserving body and key order. If the file lacks
    frontmatter, this is treated as an integrity violation — narrative
    files always have frontmatter — so we skip silently rather than corrupt.
    """
    text = narrative_path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    if not fm:
        # Defensive: do not invent frontmatter for a malformed Narrative.
        return
    existing = fm.get("proposes") or []
    if isinstance(existing, str):
        existing = [existing]
    elif not isinstance(existing, list):
        existing = []
    if concept_id in existing:
        return
    existing.append(concept_id)
    fm["proposes"] = existing
    dumped = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False).strip()
    narrative_path.write_text(f"---\n{dumped}\n---\n{body}", encoding="utf-8")


async def concept_propose_from_narrative_endpoint(request: Request) -> JSONResponse:
    project_path = request.query_params.get("project_path")
    if not project_path:
        return JSONResponse({"error": "project_path query param is required"}, status_code=400)
    try:
        workspace = resolve_solera_root(project_path)
    except FileNotFoundError as exc:
        return JSONResponse({"error": str(exc)}, status_code=404)

    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"error": "invalid JSON body"}, status_code=400)
    if not isinstance(payload, dict):
        return JSONResponse({"error": "body must be an object"}, status_code=400)

    narrative_id = payload.get("narrative_id")
    concept_id = payload.get("concept_id")
    concept_name = payload.get("concept_name")

    for field, value in (
        ("narrative_id", narrative_id),
        ("concept_id", concept_id),
        ("concept_name", concept_name),
    ):
        if not isinstance(value, str) or not value.strip():
            return JSONResponse(
                {"error": f"{field} is required and must be a non-empty string"},
                status_code=400,
            )

    assert isinstance(concept_id, str)  # narrowed for mypy
    assert isinstance(narrative_id, str)
    assert isinstance(concept_name, str)

    if not _VALID_KEBAB_RE.match(concept_id):
        return JSONResponse(
            {
                "error": (
                    "concept_id must be kebab-case: lowercase letters/digits/hyphens, "
                    "starting with a letter, ending with letter/digit, length 2-64"
                )
            },
            status_code=400,
        )

    narrative_path = workspace / "narratives" / f"{narrative_id}.md"
    if not narrative_path.exists():
        return JSONResponse({"error": f"Narrative '{narrative_id}' not found"}, status_code=404)

    concept_path = workspace / "concepts" / f"{concept_id}.md"
    if concept_path.exists():
        return JSONResponse(
            {
                "error": (
                    f"Concept '{concept_id}' already exists. Use a different id, or "
                    f"run `solera-write-concept` in update mode against the existing one."
                )
            },
            status_code=409,
        )

    today = date.today().isoformat()

    concept_path.parent.mkdir(parents=True, exist_ok=True)
    frontmatter = (
        f"---\nid: {concept_id}\nname: {concept_name}\nstatus: active\ncreated: {today}\n---\n\n"
    )
    concept_path.write_text(frontmatter + stub_concept_body(narrative_id, today), encoding="utf-8")

    append_to_narrative_proposes(narrative_path, concept_id)

    return JSONResponse(
        {
            "ok": True,
            "concept_path": str(concept_path.relative_to(workspace.parent)),
            "concept_id": concept_id,
            "needs_intent_review": True,
        }
    )
