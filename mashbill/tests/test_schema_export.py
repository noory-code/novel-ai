"""Tests for ``mashbill.schema_export`` — JSON Schema + MD template export.

v0.15.3 — extended from Foundation-only to all 15 kinds. The test surface
covers:

  - All 15 ``{kind}.json`` files are emitted.
  - Only 3 ``{kind}.md.template`` files (Foundation typed-text kinds)
    are emitted.
  - Foundation JSON schemas exclude typed-text fields (they live in MD).
  - Non-Foundation JSON schemas include their typed fields.
  - ``_meta.json`` lists every kind.
  - Idempotent: a second call with no model change rewrites no bytes.
"""

from __future__ import annotations

import json
from pathlib import Path

from mashbill.models import FOUNDATION_TYPED_TEXT_FIELDS
from mashbill.schema_export import (
    _ALL_KIND_CLASSES,
    MASHBILL_VERSION,
    SCHEMA_VERSION,
    export_all_schemas,
)

# Kinds whose typed text moves to per-node MD template (so the canvas.json
# schema must NOT expose those fields). Mirrors ``FOUNDATION_TYPED_TEXT_FIELDS``
# minus the empty-text ``project`` kind.
_TYPED_TEXT_MD_KINDS = {k for k, v in FOUNDATION_TYPED_TEXT_FIELDS.items() if v}


def test_export_writes_all_15_kind_schemas(tmp_path: Path) -> None:
    export_all_schemas(tmp_path, "proj-1")
    schema_dir = tmp_path / "schema"
    for kind in _ALL_KIND_CLASSES:
        assert (schema_dir / f"{kind}.json").is_file(), f"missing {kind}.json"


def test_export_writes_md_template_only_for_foundation_typed_text_kinds(
    tmp_path: Path,
) -> None:
    """Only 3 Foundation kinds split typed text into MD (mission /
    core_value / identity). The other 12 kinds get no MD template."""
    export_all_schemas(tmp_path, "proj-1")
    schema_dir = tmp_path / "schema"
    md_files = sorted(p.name for p in schema_dir.glob("*.md.template"))
    expected = sorted(f"{k}.md.template" for k in _TYPED_TEXT_MD_KINDS)
    assert md_files == expected


def test_foundation_json_schema_strips_typed_text_fields(tmp_path: Path) -> None:
    """A foundation kind's canvas.json schema must NOT expose typed-text
    fields — they live in the MD template, not in JSON."""
    export_all_schemas(tmp_path, "proj-1")
    schema_dir = tmp_path / "schema"
    mission_schema = json.loads((schema_dir / "mission.json").read_text(encoding="utf-8"))
    props = mission_schema.get("properties", {})
    for typed in FOUNDATION_TYPED_TEXT_FIELDS["mission"]:
        assert typed not in props, f"mission.json must not expose typed text {typed!r}"


def test_non_foundation_json_schema_includes_typed_fields(tmp_path: Path) -> None:
    """A non-Foundation kind's typed fields live in JSON, so its schema
    must expose them (e.g. ActorNode.body). (side removed US-303)"""
    export_all_schemas(tmp_path, "proj-1")
    schema_dir = tmp_path / "schema"

    # D-2026-06-15-J + US-303: actor is identity-only (body); motivation/pain
    # moved to actor_ref. side removed.
    actor_schema = json.loads((schema_dir / "actor.json").read_text(encoding="utf-8"))
    actor_props = actor_schema.get("properties", {})
    for field in ("body",):
        assert field in actor_props, f"actor.json must expose {field!r}"
    for field in ("motivation", "pain"):
        assert field not in actor_props, f"actor.json must NOT expose {field!r} (now actor_ref)"

    # D-2026-06-19-I: actor_ref is a read-only anchor — ref_actor_id only
    # only; the per-service stake (gives/receives/motivation/pain) is retired.
    actor_ref_schema = json.loads((schema_dir / "actor_ref.json").read_text(encoding="utf-8"))
    actor_ref_props = actor_ref_schema.get("properties", {})
    for field in ("ref_actor_id",):
        assert field in actor_ref_props, f"actor_ref.json must expose {field!r}"
    for gone in ("gives", "receives", "motivation", "pain"):
        assert gone not in actor_ref_props, f"actor_ref.json must NOT expose retired {gone!r}"

    # D-2026-06-20-F — service is the 5-field model: problem + value_created
    # (typed) + 3 ref-id arrays. The old 9 free-text fields are gone.
    service_schema = json.loads((schema_dir / "service.json").read_text(encoding="utf-8"))
    service_props = service_schema.get("properties", {})
    for field in ("problem", "value_created", "ref_actor_ids", "ref_value_ids", "ref_identity_ids"):
        assert field in service_props, f"service.json must expose {field!r}"
    for gone in ("target_side", "what", "scope", "do", "dont"):
        assert gone not in service_props, f"service.json must NOT expose retired {gone!r}"

    # metric / content retired 2026-06-20 (D-2026-06-20-H) — no schema files.
    assert not (schema_dir / "metric.json").exists()
    assert not (schema_dir / "content.json").exists()

    # rule (kept) exposes its typed fields.
    rule_schema = json.loads((schema_dir / "rule.json").read_text(encoding="utf-8"))
    rule_props = rule_schema.get("properties", {})
    for field in ("policy", "enforcement", "actor_permissions"):
        assert field in rule_props, f"rule.json must expose {field!r}"


def test_meta_json_lists_every_kind(tmp_path: Path) -> None:
    export_all_schemas(tmp_path, "proj-1")
    meta = json.loads((tmp_path / "schema" / "_meta.json").read_text(encoding="utf-8"))
    assert meta["schema_version"] == SCHEMA_VERSION
    assert meta["plot_version"] == MASHBILL_VERSION
    assert sorted(meta["kinds"]) == sorted(_ALL_KIND_CLASSES.keys())


def test_export_is_idempotent_no_byte_rewrite(tmp_path: Path) -> None:
    """A second call with no model change must keep mtimes intact —
    git diffs / fs watchers don't churn on rerun."""
    export_all_schemas(tmp_path, "proj-1")
    schema_dir = tmp_path / "schema"
    actor_schema_path = schema_dir / "actor.json"
    mtime_before = actor_schema_path.stat().st_mtime_ns
    export_all_schemas(tmp_path, "proj-1")
    mtime_after = actor_schema_path.stat().st_mtime_ns
    assert mtime_after == mtime_before


def test_each_kind_schema_round_trips_through_pydantic(tmp_path: Path) -> None:
    """Sanity: every exported schema parses as a JSON Schema object with
    the kind in its description / title path (catches accidental
    truncation / merge errors during the v0.15.3 expansion)."""
    export_all_schemas(tmp_path, "proj-1")
    schema_dir = tmp_path / "schema"
    for kind in _ALL_KIND_CLASSES:
        raw = json.loads((schema_dir / f"{kind}.json").read_text(encoding="utf-8"))
        assert isinstance(raw, dict)
        assert "properties" in raw
        # ``id`` is required on every node kind (BaseNodeFields)
        assert "id" in raw["properties"]
