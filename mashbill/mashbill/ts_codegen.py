"""TS wire-type code generation — Pydantic schema → ``wire.gen.ts``.

Migration Phase A (D-2026-06-20-A, TECH_REVIEW step 1). The viewer used to
hand-mirror every ``XxxJson`` interface in ``viewer/src/domain/{Kind}.ts`` and
``test_schema_parity.py`` regex-compared the two sides across the repo
boundary — a guard that silently dies the moment the viewer leaves this repo.

This module makes the Pydantic models the SSOT: it emits the ``XxxJson`` wire
interfaces (``BaseFieldsJson`` + one per kind) as a single generated TS file
that each per-kind domain class re-exports and implements. Drift is impossible
because the interfaces are *generated*, not hand-written; the committed output
is pinned byte-for-byte by ``tests/test_ts_codegen.py``. The generated file
survives the repo split (the app build regenerates it from the pinned engine).

Only the **wire shape** is generated. The per-kind domain *class*
(``fromJson`` / ``toJson`` / invariant boundary, ``mashbill-entity-template``)
stays hand-written — generation here never touches behaviour.

Regenerate after a deliberate model change:

    uv run python -m mashbill.ts_codegen
"""

from __future__ import annotations

import json
import os
import types as _types
import typing
from pathlib import Path
from typing import Any, Literal

from mashbill.models_kinds import BaseNodeFields
from mashbill.schema_export import _ALL_KIND_CLASSES

# Viewer write-target. After the open-core cut (D-2026-06-20-L / -M) the viewer
# lives in the proprietary app repo, so this MIT engine no longer hardcodes the
# app's path. The dev cross-repo regen passes ``MASHBILL_VIEWER_ROOT`` pointing at
# the app's ``viewer/`` dir; unset → the viewer artifact is not this repo's
# concern and the write is a clean no-op (the engine keeps only its own
# ``wire_contract.json`` self-copy, written by ``schema_export``).
#   MASHBILL_VIEWER_ROOT=/abs/path/to/plot/viewer uv run python -m mashbill.ts_codegen
_VIEWER_REL = Path("src") / "domain" / "wire.gen.ts"


def wire_ts_path() -> Path | None:
    """Resolved ``wire.gen.ts`` target under ``MASHBILL_VIEWER_ROOT``, or ``None``."""
    root = os.environ.get("MASHBILL_VIEWER_ROOT")
    if not root:
        return None
    return Path(root).resolve() / _VIEWER_REL


# Base-field names live on ``BaseFieldsJson`` (the interface each ``XxxJson``
# extends), so they are excluded from the per-kind interface bodies.
_BASE_FIELD_NAMES = tuple(BaseNodeFields.model_fields.keys())


def _ts_literal(value: object) -> str:
    """A single ``Literal`` arg → its TS literal form. All discriminators /
    enums in the node models are string literals."""
    if isinstance(value, str):
        return json.dumps(value)  # "service" — double-quoted, JSON-escaped
    raise TypeError(f"non-string Literal arg not supported: {value!r}")


def _py_to_ts(ann: Any) -> str:
    """Map a Pydantic field annotation to a TypeScript type expression.

    Covers exactly the shapes the node models use: ``str`` / ``int`` /
    ``float`` / ``bool``, ``Literal[...]`` (string), ``X | None``,
    ``list[X]``, ``dict[K, V]``, ``Any``. Any unmapped shape raises so a
    new field type can't silently produce a wrong TS type."""
    origin = typing.get_origin(ann)

    # Union / Optional (``X | None`` or ``Optional[X]``).
    if origin in (typing.Union, _types.UnionType):
        args = typing.get_args(ann)
        non_none = [a for a in args if a is not type(None)]
        inner = " | ".join(_py_to_ts(a) for a in non_none)
        nullable = len(non_none) != len(args)
        return f"{inner} | null" if nullable else inner

    if origin is Literal:
        return " | ".join(_ts_literal(a) for a in typing.get_args(ann))

    if origin in (list, typing.List):  # noqa: UP006 — runtime origin check
        (elem,) = typing.get_args(ann)
        return f"{_py_to_ts(elem)}[]"

    if origin in (dict, typing.Dict):  # noqa: UP006 — runtime origin check
        key_t, val_t = typing.get_args(ann)
        return f"Record<{_py_to_ts(key_t)}, {_py_to_ts(val_t)}>"

    if ann is str:
        return "string"
    if ann is bool:
        return "boolean"
    if ann in (int, float):
        return "number"
    if ann is Any or ann is object:
        return "unknown"

    raise TypeError(f"ts_codegen: unmapped annotation {ann!r}")


def _field_line(name: str, ann: Any) -> str:
    """One ``  name: type;`` interface line, with the two base-field special
    cases the hand-written interfaces carried.

    - ``shape`` → the canonical ``Shape`` alias (imported), not an inlined
      7-arm union, to match the existing idiom + keep one Shape SSOT.
    - ``publish_baseline`` → ``publish_baseline?: unknown`` (server-managed,
      aliased ``_publish_baseline`` on the wire, never round-tripped by the
      client, so optional + opaque)."""
    if name == "shape":
        return "  shape: Shape;"
    if name == "publish_baseline":
        return "  publish_baseline?: unknown;"
    return f"  {name}: {_py_to_ts(ann)};"


def _base_interface() -> str:
    lines = ["export interface BaseFieldsJson {"]
    for name in _BASE_FIELD_NAMES:
        ann = BaseNodeFields.model_fields[name].annotation
        lines.append(_field_line(name, ann))
    lines.append("}")
    return "\n".join(lines)


def _kind_interface(kind: str) -> str:
    cls = _ALL_KIND_CLASSES[kind]
    iface = "".join(part.capitalize() for part in kind.split("_")) + "Json"
    lines = [f"export interface {iface} extends BaseFieldsJson {{"]
    for name, field in cls.model_fields.items():
        if name in _BASE_FIELD_NAMES:
            continue  # inherited via BaseFieldsJson
        lines.append(_field_line(name, field.annotation))
    lines.append("}")
    return "\n".join(lines)


def generate_wire_ts() -> str:
    """The full content of ``viewer/src/domain/wire.gen.ts``.

    ``BaseFieldsJson`` + one ``XxxJson`` per registered kind (in
    ``_ALL_KIND_CLASSES`` order — the grouped schema-export order)."""
    blocks: list[str] = [
        "// AUTO-GENERATED by mashbill/ts_codegen.py (noory-ai engine) — DO NOT EDIT.",
        "// Regenerate (cross-repo, from noory-ai/mashbill):",
        "//   MASHBILL_VIEWER_ROOT=<this app>/viewer uv run python -m mashbill.ts_codegen",
        "// SSOT: mashbill Pydantic models (BaseNodeFields + the SketchNode union).",
        "// Wire shape only — the per-kind domain *class* (fromJson/toJson) is hand-written.",
        "",
        'import type { Shape } from "../types";',
        "",
        _base_interface(),
    ]
    for kind in _ALL_KIND_CLASSES:
        blocks.append("")
        blocks.append(_kind_interface(kind))
    return "\n".join(blocks) + "\n"


def write_wire_ts() -> Path | None:
    """Write ``wire.gen.ts`` under ``MASHBILL_VIEWER_ROOT``; return its path.

    Returns ``None`` (a no-op) when the env var is unset — an engine-alone
    checkout has no viewer to write to."""
    target = wire_ts_path()
    if target is None:
        return None
    content = generate_wire_ts()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


if __name__ == "__main__":
    path = write_wire_ts()
    if path is None:
        print("MASHBILL_VIEWER_ROOT unset — skipped wire.gen.ts (engine-alone checkout)")
    else:
        print(f"wrote {path}")
