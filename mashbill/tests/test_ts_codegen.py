"""Engine-side codegen guard — ``generate_wire_ts`` covers every kind.

Migration Phase A (D-2026-06-20-A). ``mashbill/ts_codegen.py`` generates the
viewer's ``XxxJson`` wire interfaces from the Pydantic models. After the
open-core cut (D-2026-06-20-L / -M) the *committed* ``wire.gen.ts`` lives in
the proprietary app repo, so the byte-for-byte freshness check is re-homed in
the app's vitest (``wire-validate`` / ``wire-contract``). What stays here is
the engine-side invariant: the generator runs, is deterministic, and emits one
interface per registered kind — so a Pydantic model change is always reflected
and a kind added without codegen support fails loudly on this side too.
"""

from __future__ import annotations

from mashbill.schema_export import _ALL_KIND_CLASSES
from mashbill.ts_codegen import generate_wire_ts


def _to_interface_name(kind: str) -> str:
    """``core_value`` → ``CoreValueJson`` — the generated interface name
    (mirror of ``ts_codegen._kind_interface``)."""
    return "".join(part.capitalize() for part in kind.split("_")) + "Json"


def test_generator_is_deterministic() -> None:
    assert generate_wire_ts() == generate_wire_ts()


def test_generator_emits_base_and_every_kind_interface() -> None:
    out = generate_wire_ts()
    assert "interface BaseFieldsJson" in out
    for kind in _ALL_KIND_CLASSES:
        name = _to_interface_name(kind)
        assert f"interface {name}" in out, (
            f"{name} missing from wire.gen.ts — a kind without codegen support. "
            "Run: MASHBILL_VIEWER_ROOT=<app>/viewer uv run python -m mashbill.ts_codegen"
        )
