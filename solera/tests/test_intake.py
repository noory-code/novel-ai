"""format F intake (INT-3) — the Solera "read" half of the Plot↔Solera contract.

Solera reads format F as a **neutral format** (docs/specs/format-f.md): it does
not import Plot or know the bundle came from Plot. These tests build synthetic
bundles by hand to prove exactly that independence — no plot_mcp anywhere.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from solera.intake import diff_releases, import_release
from solera.workspace import Workspace


def test_diff_releases_changed_removed_added() -> None:
    old = [
        {"id": "feature/login", "kind": "feature", "hash": "aaa"},
        {"id": "service/auth", "kind": "service", "hash": "bbb"},
        {"id": "entity/session", "kind": "entity", "hash": "ccc"},
    ]
    new = [
        {"id": "feature/login", "kind": "feature", "hash": "AAA"},  # changed
        {"id": "service/auth", "kind": "service", "hash": "bbb"},  # same
        {"id": "feature/signup", "kind": "feature", "hash": "ddd"},  # added
        # entity/session removed
    ]
    d = diff_releases(old, new)
    assert d == {
        "changed": ["feature/login"],
        "removed": ["entity/session"],
        "added": ["feature/signup"],
    }


def _write_bundle(root: Path, rel: str, manifest: dict) -> Path:
    d = root / rel
    (d / "design").mkdir(parents=True, exist_ok=True)
    (d / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (d / "design" / "service.md").write_text("# Auth\n", encoding="utf-8")
    return d


def test_import_rejects_unsupported_format_f_version(tmp_path: Path) -> None:
    """Cross-repo contract guard (INT-1c): the reader pins the format version it
    understands, so a Plot that bumps format_f_version without Solera following
    fails loudly here instead of silently mis-reading the contract."""
    from solera.intake import SUPPORTED_FORMAT_F_VERSION

    published = tmp_path / "published"
    _write_bundle(
        published,
        "_project/vP1",
        {"format_f_version": SUPPORTED_FORMAT_F_VERSION, "scope": "project",
         "release": "vP1", "elements": []},
    )
    vs_dir = _write_bundle(
        published,
        "auth/vS1",
        {"format_f_version": SUPPORTED_FORMAT_F_VERSION + 999, "scope": "service",
         "service": "service/auth", "release": "vS1", "based_on": "vP1",
         "elements": [], "refs": {}},
    )
    ws = Workspace(tmp_path / ".noory" / "solera")
    with pytest.raises(ValueError, match="format_f_version"):
        import_release(ws, vs_dir, label="vS1")


def test_import_release_copies_service_and_its_project_slice(tmp_path: Path) -> None:
    # Synthetic published tree (as Plot would write it) — NO plot import.
    published = tmp_path / "published"
    _write_bundle(
        published,
        "_project/vP1",
        {"format_f_version": 1, "scope": "project", "release": "vP1",
         "elements": [{"id": "actor/user", "kind": "actor", "hash": "x"}]},
    )
    vs_dir = _write_bundle(
        published,
        "auth/vS1",
        {"format_f_version": 1, "scope": "service", "service": "service/auth",
         "release": "vS1", "based_on": "vP1",
         "elements": [{"id": "service/auth", "kind": "service", "hash": "y"}],
         "refs": {"actors": ["actor/user"], "anchors": {}, "entities": []}},
    )

    ws = Workspace(tmp_path / ".noory" / "solera")
    manifest = import_release(ws, vs_dir, label="vS1")

    assert manifest["service"] == "service/auth"
    spec = ws.specs_dir / "vS1"
    assert (spec / "service" / "manifest.json").is_file()  # the vS bundle
    assert (spec / "project" / "manifest.json").is_file()  # its based_on vP slice
    # import is a copy — the source is untouched (immutable→immutable)
    assert (vs_dir / "manifest.json").is_file()
