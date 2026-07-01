"""Server-side schema-integrity guards (Python-only).

Post-codegen (migration Phase A, D-2026-06-20-A) the cross-side regex parity
that used to live here — ``test_per_kind_field_parity``, which read the viewer
``{Kind}.ts`` inline interfaces — is retired. The viewer wire types are now
GENERATED from these same Pydantic models (``mashbill/ts_codegen.py``), and
``tests/test_ts_codegen.py`` pins the committed ``wire.gen.ts`` against fresh
generation: a strictly stronger guard (it checks types, not just names) that
survives the repo split (the old regex read both sides and died on split).

What remains here are the Python-only invariants that have no viewer half:

  - the schema-export map is the registered projection of the ``SketchNode``
    union — no kind may exist at the wire while missing from schema-export
    (the "15/17 drift" guard);
  - ``BaseNodeFields`` declares exactly the canonical base-field set.
"""

from __future__ import annotations

import typing

from mashbill.models import BaseNodeFields
from mashbill.models_union import SketchNode
from mashbill.schema_export import _ALL_KIND_CLASSES

# Canonical base-field set declared by ``BaseNodeFields`` (Pydantic). The
# viewer mirror (``BaseFieldsJson``) is generated from this same model and
# guarded by ``test_ts_codegen.py`` — no separate viewer assertion needed here.
_EXPECTED_BASE_FIELDS = {
    "id",
    "label",
    "x",
    "y",
    "width",
    "height",
    "color",
    "shape",
    "icon",
    # v0.26.0 (D-2026-05-25-A) — ``parent_id`` removed. Hierarchy moved to
    # directed edges (``SketchEdge.directed``).
    "collapsed",
    "is_root",
    "details_path",
    "owner",  # v0.16.12 (D-2026-05-12-O) — multi-user prep
    "version",  # v0.17.2 Phase 2 (D-2026-05-16-C) — per-node version
    "publish_baseline",  # v0.22.0 (D-2026-05-17-H) — publish dirty baseline
}


def _union_member_kinds() -> set[str]:
    """The ``kind`` discriminator of every member of the ``SketchNode``
    discriminated union — the SSOT of "what kinds exist at the wire."

    ``SketchNode`` is ``Annotated[A | B | ..., Field(discriminator=...)]``;
    the first ``get_args`` element is the union, whose ``get_args`` are the
    per-kind classes.
    """
    union = typing.get_args(SketchNode)[0]
    members = typing.get_args(union)
    return {m.model_fields["kind"].default for m in members}


def test_export_map_covers_union() -> None:
    """``schema_export._ALL_KIND_CLASSES`` must register EVERY member of the
    ``SketchNode`` union — no kind may exist at the wire (and on the viewer)
    while silently missing from the schema-export / codegen machinery.

    This guard exists because ``decision`` / ``group`` shipped in the union +
    viewer for months while omitted from ``_ALL_KIND_CLASSES`` (the "15/17
    drift"); the export map is a *checked projection* of the union, not a
    hand-maintained parallel list."""
    assert set(_ALL_KIND_CLASSES.keys()) == _union_member_kinds(), (
        "schema-export map drifted from the SketchNode union: "
        f"missing={_union_member_kinds() - set(_ALL_KIND_CLASSES.keys())}, "
        f"extra={set(_ALL_KIND_CLASSES.keys()) - _union_member_kinds()}"
    )


def test_all_kinds_covered() -> None:
    """Sanity: the export map size matches the union size (14 after the
    2026-06-20 churn: −`group` +`feature` +`note` −3 foundation refs −metric
    −content; +`entity` for the Entities canvas, D-2026-06-17-I)."""
    assert len(_ALL_KIND_CLASSES) == len(_union_member_kinds()) == 14


def test_base_fields_pydantic_matches_canonical_set() -> None:
    """``BaseNodeFields`` must declare exactly the canonical base set — any
    drift fails this anchor (the generated viewer mirror follows from it)."""
    actual = set(BaseNodeFields.model_fields.keys())
    assert actual == _EXPECTED_BASE_FIELDS, (
        f"BaseNodeFields fields drifted: "
        f"missing={_EXPECTED_BASE_FIELDS - actual}, "
        f"extra={actual - _EXPECTED_BASE_FIELDS}"
    )
