"""Foundation-canvas inline schema upgrade (D-2026-06-11-B).

Extracted from the migrate.py god module. ``upgrade_foundation_canvas_if_needed``
is called from ``folder_io.read_canvas`` to heal a Foundation canvas
written under any pre-v0.10 schema — including the ``core`` octagon anchor
and the legacy ``identity_facet`` children. Idempotent and safe to call
on every load.
"""

from __future__ import annotations

import json
from pathlib import Path

from mashbill.folder_io import _canvas_file, _project_dir, _project_file, _write_json
from mashbill.migrate_v01_models import _normalise_legacy_node_kinds
from mashbill.models import ProjectNode


def upgrade_foundation_canvas_if_needed(plot_root: Path, project_id: str) -> bool:
    """Heal a Foundation canvas written under any pre-v0.10 schema.

    Rewrites the raw ``foundation/canvas.json`` on disk so subsequent
    reads are cheap and Pydantic parsing never trips on retired kinds.
    Returns True iff the file was rewritten. Safe to call on every load
    (idempotent).

    Operations (applied in order):
      0. v0.10 layout: rename ``core/`` folder → ``foundation/`` if the
         old name exists and the new one doesn't.
      1. ``canvas_kind="core"`` → ``canvas_kind="foundation"``.
      2. ``kind="core"`` (legacy octagon) → ``kind="project"``,
         ``shape="circle"``.
      3. ``kind="identity_facet"`` → ``kind="identity"``,
         ``parent_id=None``.
      4. If no Project anchor exists, synthesise one at centre using the
         project's ``ProjectDoc.name`` as label.
    """
    project_dir = _project_dir(plot_root, project_id)
    legacy_dir = project_dir / "core"
    new_dir = project_dir / "foundation"

    # 0. Rename ``core/`` → ``foundation/`` if needed.
    if legacy_dir.is_dir() and not new_dir.exists():
        legacy_dir.rename(new_dir)

    path = _canvas_file(plot_root, project_id, "foundation")
    if not path.exists():
        return False
    raw = json.loads(path.read_text(encoding="utf-8"))

    changed = False

    # 1. Bump canvas_kind if a stale ``core`` value made it onto disk.
    if raw.get("canvas_kind") == "core":
        raw["canvas_kind"] = "foundation"
        if raw.get("canvas_id") == "core":
            raw["canvas_id"] = "foundation"
        changed = True

    nodes = raw.get("nodes")
    if not isinstance(nodes, list):
        return changed

    # 2-3. Legacy node-kind rewrites.
    if _normalise_legacy_node_kinds(nodes):
        changed = True

    # 4. Project anchor synthesis (pre-v0.13 only).
    #    v0.13 Phase 0 moved the anchor to ``ProjectDoc.anchors``. If the
    #    project.json already carries an anchor for ``foundation``, this
    #    migration step is a no-op — synthesising an anchor node would
    #    immediately be evicted by ``_evict_legacy_project_anchor`` on the
    #    next read, creating an add→evict→write→watcher→broadcast→refetch
    #    loop (the v0.16.34 storm root cause, D-2026-05-13-K).
    has_project = any(isinstance(n, dict) and n.get("kind") == "project" for n in nodes)
    if not has_project:
        proj_already_anchored = _project_doc_has_anchor(plot_root, project_id, "foundation")
        if not proj_already_anchored:
            project_name = _read_project_name(plot_root, project_id)
            taken_ids = {n.get("id") for n in nodes if isinstance(n, dict)}
            nodes.insert(0, _project_anchor_dict(project_name, taken_ids))
            raw["nodes"] = nodes
            changed = True

    if changed:
        _write_json(path, raw)
    return changed


def _project_doc_has_anchor(plot_root: Path, project_id: str, canvas_kind: str) -> bool:
    """Return True iff ``project.json`` already carries an anchor entry
    for the given canvas kind. Used by step 4 of
    ``upgrade_foundation_canvas_if_needed`` to short-circuit the
    pre-v0.13 anchor synthesis when v0.13 Phase 0 has already migrated
    the anchor to ``ProjectDoc.anchors``."""
    project_file = _project_file(plot_root, project_id)
    if not project_file.exists():
        return False
    try:
        doc = json.loads(project_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    anchors = doc.get("anchors")
    if not isinstance(anchors, dict):
        return False
    return canvas_kind in anchors


def _read_project_name(plot_root: Path, project_id: str) -> str:
    """Best-effort read of ``project.json``'s ``name``; falls back to id."""
    proj_path = _project_file(plot_root, project_id)
    try:
        raw = json.loads(proj_path.read_text(encoding="utf-8"))
        name = raw.get("name")
        if isinstance(name, str) and name.strip():
            return name
    except (OSError, json.JSONDecodeError):
        pass
    return project_id


def _project_anchor_dict(project_name: str, taken_ids: set[str | None]) -> dict[str, object]:
    anchor_id = "project"
    suffix = 1
    while anchor_id in taken_ids:
        suffix += 1
        anchor_id = f"project-{suffix}"
    return ProjectNode(
        id=anchor_id,
        label=project_name,
        x=-75,
        y=-75,
        width=150,
        height=150,
        color="#fef3c7",
        shape="circle",
        icon="compass",
    ).model_dump()
