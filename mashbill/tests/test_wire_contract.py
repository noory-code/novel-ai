"""Wire-contract snapshot — split-survivable schema parity (D-2026-06-10-E).

`test_schema_parity.py` reads BOTH sides (Pydantic + viewer TS) from disk, so
it silently dies the moment viewer/ leaves this repo (TECH_REVIEW step 1).
The replacement contract is a generated JSON snapshot committed TWICE:

    mashbill/wire_contract.json            (engine copy — this side)
    <app repo>/viewer/src/schema/wire-contract.json  (viewer copy — vitest)

Each side verifies its own sources against its own committed copy, so both
guards survive the repo split. **The split happened (D-2026-06-20-L / -M):**
the viewer copy now lives in the proprietary app repo and is guarded there;
this engine test only owns the engine copy. The former monorepo byte-identity
sync test is retired — the two copies are kept consistent by the dev
cross-repo regen writing both from one payload.

Regenerate after a deliberate schema change (engine copy only; add
``MASHBILL_VIEWER_ROOT=/abs/path/to/plot/viewer`` to also refresh the app copy):

    uv run python -m mashbill.schema_export --wire
"""

from __future__ import annotations

import json
from pathlib import Path

from mashbill.schema_export import wire_contract

_MASHBILL_ROOT = Path(__file__).resolve().parent.parent
_ENGINE_COPY = _MASHBILL_ROOT / "mashbill" / "wire_contract.json"


def test_engine_snapshot_matches_generated_contract() -> None:
    """The committed engine copy must equal what the models generate NOW.
    Drift = someone changed a Pydantic model without regenerating."""
    assert _ENGINE_COPY.is_file(), (
        f"missing {_ENGINE_COPY} — run: uv run python -m mashbill.schema_export --wire"
    )
    committed = json.loads(_ENGINE_COPY.read_text(encoding="utf-8"))
    assert committed == wire_contract(), (
        "wire_contract.json is stale — a model changed without regenerating. "
        "Run: uv run python -m mashbill.schema_export --wire"
    )


def test_contract_shape() -> None:
    c = wire_contract()
    assert c["schema_version"] >= 1
    assert "base_fields" in c and "id" in c["base_fields"]
    assert len(c["kinds"]) == 14
    for kind, fields in c["kinds"].items():
        assert "kind" in fields, f"{kind} must carry its discriminator"
        assert fields == sorted(fields), f"{kind} fields must be sorted (stable diffs)"
