"""Codegen viewer-target resolution after the open-core cut (D-2026-06-20-M).

The viewer left this (MIT, headless) engine repo for the proprietary app repo
(D-2026-06-20-L). The engine no longer hardcodes the app's path: the viewer
write-target comes ONLY from the ``MASHBILL_VIEWER_ROOT`` env var. Unset → the
viewer artifacts are not this repo's concern (engine self-copy still written);
set → the dev cross-repo regen writes ``wire.gen.ts`` + the viewer
``wire-contract.json`` under that root. This pins that contract so the engine
never silently recreates a ``viewer/`` dir inside ``noory-ai`` again.
"""

from __future__ import annotations

from pathlib import Path

from mashbill import schema_export, ts_codegen


def test_wire_ts_target_is_none_when_env_unset(monkeypatch) -> None:
    monkeypatch.delenv("MASHBILL_VIEWER_ROOT", raising=False)
    assert ts_codegen.wire_ts_path() is None


def test_wire_ts_target_resolves_under_env_root(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("MASHBILL_VIEWER_ROOT", str(tmp_path))
    target = ts_codegen.wire_ts_path()
    assert target == tmp_path.resolve() / "src" / "domain" / "wire.gen.ts"


def test_viewer_contract_target_is_none_when_env_unset(monkeypatch) -> None:
    monkeypatch.delenv("MASHBILL_VIEWER_ROOT", raising=False)
    assert schema_export.viewer_contract_path() is None


def test_viewer_contract_target_resolves_under_env_root(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("MASHBILL_VIEWER_ROOT", str(tmp_path))
    target = schema_export.viewer_contract_path()
    assert target == tmp_path.resolve() / "src" / "schema" / "wire-contract.json"


def test_write_wire_ts_skips_without_env(monkeypatch) -> None:
    """No env → no write, returns None (engine-alone checkout is a no-op)."""
    monkeypatch.delenv("MASHBILL_VIEWER_ROOT", raising=False)
    assert ts_codegen.write_wire_ts() is None


def test_write_wire_ts_writes_under_env_root(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("MASHBILL_VIEWER_ROOT", str(tmp_path))
    written = ts_codegen.write_wire_ts()
    assert written == tmp_path.resolve() / "src" / "domain" / "wire.gen.ts"
    assert written.read_text(encoding="utf-8") == ts_codegen.generate_wire_ts()
