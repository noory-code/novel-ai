"""format F intake — the Solera "read" half of the Plot↔Solera contract (INT-3).

Solera reads **format F** (docs/specs/format-f.md) as a *neutral* format: it
never imports Plot and never path-references the Plot tree (R8 — guarded by
``tests/test_independence.py``). The only thing it knows is the format's own
directory convention (a service bundle ``vS`` sits next to ``_project/{vP}``).

Two pieces:
- :func:`import_release` — copy a frozen ``vS`` bundle + its ``based_on`` ``vP``
  slice into ``specs/{label}/`` (immutable → immutable). Story files then point
  at ``specs/{label}`` (their own folder), so Solera runs with or without Plot.
- :func:`diff_releases` — the deterministic ID-diff (changed / removed / added)
  that drives re-pinning on a re-publish. A pure function over two manifests.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from solera.workspace import Workspace


def diff_releases(
    old_elements: list[dict[str, Any]], new_elements: list[dict[str, Any]]
) -> dict[str, list[str]]:
    """Compare two manifests' ``elements`` by stable id + content hash.

    - ``changed`` — same id, different hash → the work realizing it goes stale.
    - ``removed`` — id gone → that work is orphaned → escalate (not auto-repin).
    - ``added`` — new id → a new work candidate.

    Deterministic and pure (format-f.md §5): the harness must be able to trust
    the verdict, so this is plain code, never an LLM step.
    """
    old = {e["id"]: e["hash"] for e in old_elements}
    new = {e["id"]: e["hash"] for e in new_elements}
    return {
        "changed": sorted(i for i in old if i in new and old[i] != new[i]),
        "removed": sorted(i for i in old if i not in new),
        "added": sorted(i for i in new if i not in old),
    }


def import_release(ws: Workspace, source_vs_dir: Path, *, label: str) -> dict[str, Any]:
    """Copy a frozen service release ``vS`` (and the ``vP`` slice it is based on)
    into ``specs/{label}/`` and return the ``vS`` manifest.

    ``source_vs_dir`` is a published service bundle directory (e.g. the
    ``published/{slug}/vS{N}/`` Plot wrote). The user wires that path in; Solera
    does not reach into Plot. The ``based_on`` ``vP`` lives at
    ``<published>/_project/{based_on}`` per the format's convention.
    """
    manifest: dict[str, Any] = json.loads(
        (source_vs_dir / "manifest.json").read_text(encoding="utf-8")
    )
    based_on = manifest.get("based_on")
    if not based_on:
        raise ValueError(f"service release {source_vs_dir} has no based_on vP")

    vp_dir = source_vs_dir.parent.parent / "_project" / based_on
    if not (vp_dir / "manifest.json").is_file():
        raise FileNotFoundError(f"based_on snapshot not found: {vp_dir}")

    dest = ws.specs_dir / label
    if dest.exists():
        raise FileExistsError(f"spec already imported: {dest}")
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_vs_dir, dest / "service")
    shutil.copytree(vp_dir, dest / "project")
    return manifest
