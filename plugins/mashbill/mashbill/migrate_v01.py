"""Legacy v0.1 → v0.2 migration loop (D-2026-06-11-B).

Extracted from the migrate.py god module. Walks every
``.plot/sketches/{id}.json`` looking for v0.1 docs, parses each strictly
via the legacy ``_V01SketchDoc`` model, then writes the four current
canvases via the per-canvas builders in ``migrate_builders``. Files that
don't parse are left in place so the user can fix them by hand.
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path

from mashbill.folder_io import _canvas_file, _project_dir, _project_file, _write_json
from mashbill.migrate_builders import (
    _build_actors_canvas,
    _build_foundation_canvas,
    _split_services,
)
from mashbill.migrate_v01_models import (
    _normalise_legacy_node_kinds,
    _V01SketchDoc,
    _V01SketchNode,
)
from mashbill.models import ProjectDoc


def _read_v01_sketch(path: Path) -> _V01SketchDoc:
    """Read one v0.1 ``{id}.json`` file. Raises on missing / malformed."""
    if not path.exists():
        raise FileNotFoundError(f"sketch not found: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    # v0.1 files may carry kinds that were retired in v0.5 (``core`` anchor,
    # ``identity_facet`` children). Rewrite them up-front so Pydantic's
    # post-v0.5 ``NodeKind`` Literal accepts the document.
    _normalise_legacy_node_kinds(raw.get("nodes", []))
    return _V01SketchDoc.model_validate(raw)


def migrate_v01_to_v02(plot_root: Path) -> list[str]:
    """Migrate every v0.1 ``{id}.json`` under ``sketches/`` to the v0.2 folder layout.

    Returns the list of project ids that were migrated (may be empty).
    Files that don't parse as v0.1 are skipped and stay in place.
    """
    sketches_dir = plot_root / "sketches"
    if not sketches_dir.is_dir():
        return []
    migrated: list[str] = []
    for path in sorted(sketches_dir.glob("*.json")):
        # Skip files that were already renamed to .v01.bak.
        if path.name.endswith(".v01.bak"):
            continue
        try:
            doc = _read_v01_sketch(path)
        except (ValueError, json.JSONDecodeError):
            continue
        # S2 (D-2026-06-21-AB): flat layout — ``_project_dir`` returns the
        # root for a fresh project, so "already migrated" is a project.json
        # check, not folder existence (the root always exists). One project per
        # root (D-2026-06-21-AA): a second sketch under the same root is skipped
        # rather than stacked.
        if _project_file(plot_root, doc.id).exists() or (plot_root / "project.json").is_file():
            _backup(path)
            continue
        _migrate_one(plot_root, doc)
        _backup(path)
        migrated.append(doc.id)
    return migrated


def _backup(path: Path) -> None:
    backup = path.with_suffix(path.suffix + ".v01.bak")
    path.replace(backup)


def _migrate_one(plot_root: Path, doc: _V01SketchDoc) -> None:
    folder = _project_dir(plot_root, doc.id)
    folder.mkdir(parents=True, exist_ok=True)
    # v0.8: no longer seed a ``services-detail/`` folder — detail canvases
    # live alongside their service under ``services/{sid}/detail.json``
    # and are created lazily by ``sync_details_with_overview``.

    # --- project metadata -----------------------------------------------
    proj = ProjectDoc(
        id=doc.id,
        name=doc.name or doc.id,
        created=doc.created or date.today().isoformat(),
        updated=datetime.now(UTC).isoformat(),
        version=3,  # v0.13 Phase 0
    )
    _write_json(_project_file(plot_root, doc.id), proj.model_dump())

    # --- classify nodes -------------------------------------------------
    by_id = {n.id: n for n in doc.nodes}
    # ``kind == "core"`` was normalised to ``"project"`` in _read_v01_sketch.
    core_root = next((n for n in doc.nodes if n.kind == "project"), None)
    actor_root = next((n for n in doc.nodes if n.kind == "actor" and n.is_root), None)
    service_root = next((n for n in doc.nodes if n.kind == "service" and n.is_root), None)

    def _in_subtree(node: _V01SketchNode, root_id: str) -> bool:
        cur: _V01SketchNode | None = node
        while cur is not None:
            if cur.id == root_id:
                return True
            cur = by_id.get(cur.parent_id) if cur.parent_id else None
        return False

    actor_nodes: list[_V01SketchNode] = []
    service_nodes: list[_V01SketchNode] = []
    for n in doc.nodes:
        if n.kind == "project":
            continue  # project anchor handled by _build_foundation_canvas
        if actor_root and _in_subtree(n, actor_root.id):
            actor_nodes.append(n)
        elif service_root and _in_subtree(n, service_root.id):
            service_nodes.append(n)
        elif n.kind == "actor":
            actor_nodes.append(n)
        elif n.kind in ("service", "rule", "content"):
            service_nodes.append(n)
        # identity-kind nodes would go to core but v0.1 didn't have them.

    # --- write foundation canvas ---------------------------------------
    foundation_canvas = _build_foundation_canvas(core_root, proj.name)
    _write_json(
        _canvas_file(plot_root, doc.id, "foundation"),
        foundation_canvas.model_dump(by_alias=True),
    )

    # --- write actors canvas --------------------------------------------
    actors_canvas = _build_actors_canvas(actor_nodes, actor_root, doc.edges)
    _write_json(
        _canvas_file(plot_root, doc.id, "actors"),
        actors_canvas.model_dump(by_alias=True),
    )

    # --- split services into overview + details -------------------------
    overview, detail_canvases = _split_services(service_nodes, service_root, doc.edges)
    _write_json(
        _canvas_file(plot_root, doc.id, "services"),
        overview.model_dump(by_alias=True),
    )
    for detail in detail_canvases:
        _write_json(
            _canvas_file(plot_root, doc.id, "feature", service_id=detail.canvas_id),
            detail.model_dump(by_alias=True),
        )
