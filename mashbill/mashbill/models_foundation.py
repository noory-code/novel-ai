"""Foundation-canvas node classes + Foundation sub-union (D-2026-06-11-B).

Extracted from the models.py god module. Contains the 4 Foundation node
kinds (project / mission / core_value / identity) and the dispatch maps
that drive the legacy MD template parser.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, model_validator

from mashbill.models_kinds import BaseNodeFields


class ProjectNode(BaseNodeFields):
    """v0.13 Phase 1: ``project`` kind anchor.

    In v0.13 the project anchor's data lives in ``ProjectDoc.anchors`` and
    is rendered as a synthetic node by the viewer (not stored in
    canvas.json). This class is kept for symmetry with the other kinds and
    for the rare fully-derived case; canvas.json should not normally
    contain a ProjectNode.
    """

    kind: Literal["project"] = "project"


class MissionNode(BaseNodeFields):
    """v0.43.0 (D-2026-06-06-C): mission = ``label`` (the declaration) +
    ``body`` (free Markdown). The former typed fields ``what_we_do`` /
    ``why`` / ``direction`` were removed — a mission is one indivisible
    declaration, not a bag of sliced angles. Legacy values fold into
    ``body`` on read (data-loss guard); see ``_fold_legacy_typed_fields``."""

    kind: Literal["mission"] = "mission"
    statement: str = ""
    body: str = ""

    @model_validator(mode="before")
    @classmethod
    def _migrate_legacy_typed_fields(cls, data: object) -> object:
        """Pre-v0.43 mission nodes carry what_we_do/why/direction. Migrate:
        what_we_do -> ``statement``; fold why/direction into ``body`` as
        ``## {label}`` paragraphs. Drop the legacy keys (no content lost)."""
        legacy = ("what_we_do", "why", "direction")
        if not isinstance(data, dict) or not any(k in data for k in legacy):
            return data
        out = dict(data)
        what = out.pop("what_we_do", None)
        if isinstance(what, str) and what.strip() and not str(out.get("statement") or "").strip():
            out["statement"] = what.strip()
        fold_labels = {"why": "Why", "direction": "Direction"}
        blocks = [
            f"## {label}\n{str(out[key]).strip()}"
            for key, label in fold_labels.items()
            if isinstance(out.get(key), str) and str(out[key]).strip()
        ]
        for key in fold_labels:
            out.pop(key, None)
        if blocks:
            body = str(out.get("body") or "").rstrip()
            folded = "\n\n".join(blocks)
            out["body"] = f"{body}\n\n{folded}" if body else folded
        return out


class CoreValueNode(BaseNodeFields):
    """v0.45 (D-2026-07-02-A): core_value = ``label`` (the value's name) +
    ``body`` (its meaning + tradeoff). The former typed ``definition`` field
    is removed — it *was* the value's meaning, which now leads ``body`` — and
    the earlier ``do`` / ``dont`` fields stay removed. Legacy values fold into
    ``body`` on read (data-loss guard): ``definition`` leads, then the prior
    body, then do/dont as ``## Do`` / ``## Don't`` sections. Root canon:
    docs/concepts/kinds.md (name + body)."""

    kind: Literal["core_value"] = "core_value"
    body: str = ""

    @model_validator(mode="before")
    @classmethod
    def _fold_legacy_fields(cls, data: object) -> object:
        legacy_keys = ("definition", "do", "dont")
        if not isinstance(data, dict) or not any(k in data for k in legacy_keys):
            return data
        out = dict(data)
        definition = str(out.pop("definition", "") or "").strip()
        body = str(out.get("body") or "").strip()
        sections = {"do": "Do", "dont": "Don't"}
        blocks = [
            f"## {label}\n{str(out[key]).strip()}"
            for key, label in sections.items()
            if isinstance(out.get(key), str) and str(out[key]).strip()
        ]
        for key in sections:
            out.pop(key, None)
        parts = [p for p in (definition, body, *blocks) if p]
        out["body"] = "\n\n".join(parts)
        return out


class IdentityNode(BaseNodeFields):
    """v0.44.0 (D-2026-06-07-A): identity = ``description`` + ``body`` plus the
    **output-model** structural fields ``status`` + ``provenance``. identity is
    an output kind (AI-derived from mission + core_value), so it tracks its
    derivation lineage and a derive→confirm lifecycle the input kinds lack:

    - ``status`` — ``manual`` (hand-authored; graceful-degradation default) /
      ``derived`` (AI draft, unconfirmed) / ``confirmed`` (AI-derived + user-locked).
    - ``provenance`` — ids of the source nodes this identity was derived from.

    Both are **structural** (not MD prose) → ``canvas.json`` only, NOT in the
    MD typed-text split, so absent from FOUNDATION_TYPED_TEXT_FIELDS /
    FOUNDATION_MD_FIELDS. ``evolution`` (revision history) is deferred — overlaps
    git + ``version``, no writer yet. v0.43.2 (D-2026-06-06-B) removed the legacy
    ``do`` / ``dont`` (folded into ``body`` on read). See
    docs/node-format/foundation/identity.md."""

    kind: Literal["identity"] = "identity"
    description: str = ""
    body: str = ""
    status: Literal["manual", "derived", "confirmed"] = "manual"
    provenance: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _fold_body_into_description(cls, data: object) -> object:
        # B-15 (D-2026-07-03-S): description is the single prose field —
        # the inspector no longer shows body, so a non-empty body folds into
        # description on read (data-loss guard, like core_value's definition).
        if not isinstance(data, dict):
            return data
        body = str(data.get("body") or "").strip()
        if not body:
            return data
        out = dict(data)
        desc = str(out.get("description") or "").strip()
        out["description"] = f"{desc}\n\n{body}" if desc else body
        out["body"] = ""
        return out

    @model_validator(mode="before")
    @classmethod
    def _fold_legacy_do_dont(cls, data: object) -> object:
        legacy = {"do": "Do", "dont": "Don't"}
        if not isinstance(data, dict) or not any(k in data for k in legacy):
            return data
        out = dict(data)
        blocks = [
            f"## {label}\n{str(out[key]).strip()}"
            for key, label in legacy.items()
            if isinstance(out.get(key), str) and str(out[key]).strip()
        ]
        for key in legacy:
            out.pop(key, None)
        if blocks:
            body = str(out.get("body") or "").rstrip()
            folded = "\n\n".join(blocks)
            out["body"] = f"{body}\n\n{folded}" if body else folded
        return out


# Discriminated union — the runtime + IDE narrows on ``kind`` automatically.
# Used by Phase 3's MD template I/O to instantiate the correct subclass per
# node (Pydantic dispatches via the ``kind`` literal).
FoundationNode = Annotated[
    ProjectNode | MissionNode | CoreValueNode | IdentityNode,
    Field(discriminator="kind"),
]

# Per-kind H2-section field map for the *legacy* MD template parser.
# Each entry lists the typed fields that ``parse_md_template`` extracts
# from ``## Heading`` sections of pre-v0.17 ``foundation/{kind}-{slug}.md``
# files. Phase 1's ``_absorb_md_typed_text_into_json`` uses this to know
# which JSON keys to absorb from H2 content; the ``body`` field is
# separately sourced from the post-``---`` free prose, so it is NOT in
# this map. Keep in sync with the subclass definitions above.
FOUNDATION_TYPED_TEXT_FIELDS: dict[str, list[str]] = {
    "project": [],
    "mission": ["statement"],  # v0.43.0 (D-2026-06-06-C): 3 fields → statement
    "core_value": [],  # v0.45 (D-2026-07-02-A): definition removed → name (label) + body
    "identity": ["description"],  # v0.43.2 (D-2026-06-06-B): do/dont removed
}

# Per-kind *all-MD-syntax-fields-per-kind* map. JSON SSOT consumers
# (viewer MD-aware inspectors, Phase 3 publish output) iterate this
# list to know every field whose value is an MD-formatted string.
# Equals ``FOUNDATION_TYPED_TEXT_FIELDS[kind] + ["body"]`` for the 3
# typed-text kinds, empty otherwise.
FOUNDATION_MD_FIELDS: dict[str, list[str]] = {
    "project": [],
    "mission": ["statement", "body"],  # v0.43.0 (D-2026-06-06-C)
    "core_value": ["body"],  # v0.45 (D-2026-07-02-A): definition removed
    "identity": ["description", "body"],  # v0.43.2 (D-2026-06-06-B)
}

# v0.13 Phase 0 — the project anchor lives in ``ProjectDoc.anchors``,
# not in ``canvas.nodes``. The viewer injects a synthetic node with
# this id so user-drawn edges can legitimately reference it
# (D-2026-05-04-B: *"User may draw edges from / to the anchor like
# any other node"*). Mirrors ``viewer/src/canvases/sketch/constants.ts``
# ``PROJECT_ANCHOR_ID``. See D-2026-05-13-M.
PROJECT_ANCHOR_ID = "__project_anchor__"
