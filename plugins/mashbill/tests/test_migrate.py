"""v0.1 → v0.2 migration — single-file ``{id}.json`` → folder layout."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mashbill.folder_io import list_feature_details, read_canvas, read_project
from mashbill.migrate import migrate_v01_to_v02
from mashbill.workspace import resolve_plot_root


@pytest.fixture
def plot_root(tmp_path: Path) -> Path:
    return resolve_plot_root(str(tmp_path))


# ---------------------------------------------------------------------------
# helpers — write a v0.1 sketch JSON without depending on the deleted
# ``mashbill.sketches`` module. Keeps the legacy format visible in the
# tests rather than hiding it behind a fixture builder.
# ---------------------------------------------------------------------------


def _v01_node(node_id: str, **overrides: Any) -> dict[str, Any]:
    """Build a v0.1 SketchNode dict, letting callers override any field."""
    base: dict[str, Any] = {
        "id": node_id,
        "label": node_id,
        "body": "",
        "x": 0,
        "y": 0,
        "width": 180,
        "height": 80,
        "color": "#ffffff",
        "shape": "rounded",
        "icon": None,
        "kind": None,
        "parent_id": None,
        "collapsed": False,
        "is_root": False,
        "mission": "",
        "core_values": "",
        "identity": "",
        "ref_actor_id": None,
    }
    base.update(overrides)
    return base


def _v01_seed_nodes() -> list[dict[str, Any]]:
    """The three root nodes v0.1 ``create_sketch`` used to plant."""
    return [
        _v01_node(
            "core-root",
            kind="core",
            label="alpha",
            x=-90,
            y=-70,
            width=180,
            height=140,
            color="#fde68a",
            shape="octagon",
            icon="star",
        ),
        _v01_node(
            "actor-root",
            kind="actor",
            label="Actors",
            is_root=True,
            parent_id="core-root",
            x=-320,
            y=180,
            width=140,
            height=140,
            color="#fecaca",
            shape="circle",
            icon="users",
        ),
        _v01_node(
            "service-root",
            kind="service",
            label="Services",
            is_root=True,
            parent_id="core-root",
            x=180,
            y=180,
            width=200,
            height=120,
            color="#bae6fd",
            shape="rounded",
            icon="zap",
        ),
    ]


def _v01_seed_edges() -> list[dict[str, Any]]:
    return [
        {
            "id": "e-core-actor",
            "source": "core-root",
            "target": "actor-root",
            "sourceHandle": None,
            "targetHandle": None,
            "label": "decomposes",
            "style": "dashed",
            "action_verb": "decomposes",
            "value_form": [],
        },
        {
            "id": "e-core-service",
            "source": "core-root",
            "target": "service-root",
            "sourceHandle": None,
            "targetHandle": None,
            "label": "decomposes",
            "style": "dashed",
            "action_verb": "decomposes",
            "value_form": [],
        },
    ]


def _write_v01_sketch(
    plot_root: Path,
    sketch_id: str,
    name: str,
    *,
    nodes: list[dict[str, Any]] | None = None,
    edges: list[dict[str, Any]] | None = None,
) -> None:
    """Drop a v0.1 ``{id}.json`` onto disk for the migrator to find."""
    doc = {
        "id": sketch_id,
        "name": name,
        "created": "2026-01-01",
        "updated": "2026-01-01T00:00:00+00:00",
        "version": 1,
        "nodes": nodes or _v01_seed_nodes(),
        "edges": edges or _v01_seed_edges(),
    }
    sketches_dir = plot_root / "sketches"
    sketches_dir.mkdir(exist_ok=True)
    (sketches_dir / f"{sketch_id}.json").write_text(
        json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# bare v0.1 seed (Core + Actor-root + Service-root only)
# ---------------------------------------------------------------------------


def test_migrates_bare_v01_sketch(plot_root: Path) -> None:
    _write_v01_sketch(plot_root, "alpha", "Alpha")
    migrated = migrate_v01_to_v02(plot_root)
    assert migrated == ["alpha"]

    # S2 flat layout: the project's files sit directly under plot_root.
    folder = plot_root
    assert (folder / "project.json").is_file()

    # v0.1 file was backed up in the (still-legacy) sketches/ drop-zone.
    assert (plot_root / "sketches" / "alpha.json.v01.bak").is_file()
    assert not (plot_root / "sketches" / "alpha.json").exists()

    # project metadata
    proj = read_project(plot_root, "alpha")
    assert proj.id == "alpha"
    assert proj.name == "Alpha"
    assert proj.version == 3  # v0.13 Phase 0


def test_migrated_foundation_canvas_has_seeds(plot_root: Path) -> None:
    """v0.13 Phase 0: migrated Foundation canvas hosts mission/core_value/
    identity (no project node — moved to ProjectDoc.anchors)."""
    _write_v01_sketch(plot_root, "alpha", "Alpha")
    migrate_v01_to_v02(plot_root)
    foundation = read_canvas(plot_root, "alpha", "foundation")
    kinds = sorted({n.kind for n in foundation.nodes if n.kind is not None})
    assert "mission" in kinds and "identity" in kinds and "core_value" in kinds
    assert "project" not in kinds  # evicted by v0.13 migrator
    assert "core" not in kinds
    # v0.26.0 (D-2026-05-25-A) — parent_id field gone. Foundation
    # nodes never carried parent_id chains anyway; the original check
    # is now satisfied by the field's absence.
    assert not any(hasattr(n, "parent_id") for n in foundation.nodes)


def test_migrated_actors_canvas_starts_empty_or_has_root(plot_root: Path) -> None:
    """v0.13 Phase 0: actors canvas has actors only (no project node)."""
    _write_v01_sketch(plot_root, "alpha", "Alpha")
    migrate_v01_to_v02(plot_root)
    actors = read_canvas(plot_root, "alpha", "actors")
    assert all(n.kind == "actor" for n in actors.nodes if n.kind)
    # v0.26.0 (D-2026-05-25-A) — parent_id field gone.
    assert not any(hasattr(n, "parent_id") for n in actors.nodes)


def test_migrated_services_canvas_has_no_nested(plot_root: Path) -> None:
    _write_v01_sketch(plot_root, "alpha", "Alpha")
    migrate_v01_to_v02(plot_root)
    overview = read_canvas(plot_root, "alpha", "services")
    # v0.26.0 (D-2026-05-25-A) — parent_id field gone. "No nested"
    # was a parent_id check; now we just confirm the field absence.
    assert not any(hasattr(n, "parent_id") for n in overview.nodes)
    # Bare v0.1 seed has service-root only; it becomes a top-level service.


def test_v10_upgrade_renames_core_dir_and_unparents_children(plot_root: Path) -> None:
    """v0.10 Foundation upgrade rewrites a pre-v0.10 disk:
    1. ``core/`` folder → ``foundation/``.
    2. ``canvas_kind = "core"`` → ``"foundation"``.
    3. legacy ``core``-kind octagon → ``project`` + ``shape="circle"``.
    4. ``identity_facet`` → ``identity`` + ``parent_id=None``.
    5. Children of the legacy core anchor get ``parent_id=None`` so the
       small anchor doesn't visually trap them.
    """
    from mashbill.migrate import upgrade_foundation_canvas_if_needed
    from mashbill.models import ProjectDoc

    # S2 flat layout: the project's files sit directly under plot_root.
    folder = plot_root
    (folder / "core").mkdir(parents=True, exist_ok=True)
    # Seed project.json directly (the pre-v0.10 on-disk state) so the upgrader
    # can read the authoritative name.
    (folder / "project.json").write_text(
        json.dumps(ProjectDoc(id="alpha", name="Alpha v1", version=3).model_dump()),
        encoding="utf-8",
    )

    (folder / "core" / "canvas.json").write_text(
        json.dumps(
            {
                "canvas_id": "core",
                "canvas_kind": "core",
                "feature_ref": None,
                "edges": [],
                "nodes": [
                    {
                        "id": "core-root",
                        "kind": "core",
                        "label": "Legacy",
                        "shape": "octagon",
                        "icon": "star",
                        "x": 0,
                        "y": 0,
                        "width": 180,
                        "height": 140,
                        "color": "#fde68a",
                        "body": "",
                        "parent_id": None,
                        "collapsed": False,
                        "is_root": False,
                        "mission": "",
                        "core_values": "",
                        "identity": "",
                        "ref_actor_id": None,
                    },
                    {
                        "id": "mission",
                        "kind": "mission",
                        "label": "M",
                        "shape": "rounded",
                        "icon": "star",
                        "x": 100,
                        "y": 0,
                        "width": 200,
                        "height": 90,
                        "color": "#fef3c7",
                        "body": "",
                        "parent_id": "core-root",
                        "collapsed": False,
                        "is_root": False,
                        "mission": "",
                        "core_values": "",
                        "identity": "",
                        "ref_actor_id": None,
                    },
                    {
                        "id": "facet-1",
                        "kind": "identity_facet",
                        "label": "Tone",
                        "shape": "rounded",
                        "icon": "star",
                        "x": -100,
                        "y": 0,
                        "width": 140,
                        "height": 60,
                        "color": "#fdba74",
                        "body": "",
                        "parent_id": "identity",
                        "collapsed": False,
                        "is_root": False,
                        "mission": "",
                        "core_values": "",
                        "identity": "",
                        "ref_actor_id": None,
                    },
                    {
                        "id": "identity",
                        "kind": "identity",
                        "label": "I",
                        "shape": "rounded",
                        "icon": "star",
                        "x": 200,
                        "y": 0,
                        "width": 200,
                        "height": 90,
                        "color": "#fed7aa",
                        "body": "",
                        "parent_id": "core-root",
                        "collapsed": False,
                        "is_root": False,
                        "mission": "",
                        "core_values": "",
                        "identity": "",
                        "ref_actor_id": None,
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    changed = upgrade_foundation_canvas_if_needed(plot_root, "alpha")
    assert changed is True

    # ``core/`` folder was renamed to ``foundation/`` on disk.
    assert not (folder / "core").exists()
    assert (folder / "foundation" / "canvas.json").is_file()

    foundation = read_canvas(plot_root, "alpha", "foundation")
    by_id = {n.id: n for n in foundation.nodes}

    # v0.13 Phase 0 — legacy ``core``/``project`` anchor evicted from canvas
    # to ProjectDoc.anchors. ``core-root`` no longer present in nodes.
    assert "core-root" not in by_id

    # Anchor position migrated to ProjectDoc.anchors["foundation"].
    proj = read_project(plot_root, "alpha")
    assert "foundation" in proj.anchors
    assert proj.anchors["foundation"].shape == "circle"

    # v0.26.0 (D-2026-05-25-A) — parent_id field gone. The original
    # "children un-parented" check is now trivially satisfied by the
    # field's absence. Containment, if any, would be expressed via
    # directed edges; the v0.26 read-side migration auto-creates them
    # from any pre-v0.26 parent_id (here Mission was a child of
    # core-root, which got evicted, so no edge survives).
    assert not hasattr(by_id["mission"], "parent_id")
    assert not hasattr(by_id["identity"], "parent_id")

    # identity_facet folded into identity.
    facet = by_id["facet-1"]
    assert facet.kind == "identity"
    assert not hasattr(facet, "parent_id")

    # Star icons stripped from the pillar kinds.
    assert by_id["mission"].icon is None
    assert by_id["identity"].icon is None
    assert facet.icon is None


def test_migration_is_idempotent(plot_root: Path) -> None:
    _write_v01_sketch(plot_root, "alpha", "Alpha")
    migrate_v01_to_v02(plot_root)
    # second pass — nothing to do (already migrated)
    assert migrate_v01_to_v02(plot_root) == []


# ---------------------------------------------------------------------------
# richer v0.1 — mission/core-values/identity text on core-root
# ---------------------------------------------------------------------------


def test_identity_fields_promoted_to_nodes(plot_root: Path) -> None:
    nodes = _v01_seed_nodes()
    # Patch core-root with identity text fields (v0.1 carried them on the node itself).
    for n in nodes:
        if n["id"] == "core-root":
            n["mission"] = "Deliver value"
            n["core_values"] = "Speed\nClarity"
            n["identity"] = "Tone: warm"
    _write_v01_sketch(plot_root, "alpha", "Alpha", nodes=nodes)

    migrate_v01_to_v02(plot_root)
    foundation = read_canvas(plot_root, "alpha", "foundation")
    core = foundation  # local alias keeps the rest of the assertion text simple
    # v0.9.1 dropped typed fields — legacy ``mission`` / ``identity``
    # text on the v0.1 core-root no longer survives migration (it would
    # need a ``details.md`` write, but the migration is intentionally
    # side-effect-free w.r.t. file IO). The structural nodes still get
    # created so the user can re-paste their content.
    kinds_present = {n.kind for n in core.nodes}
    assert "mission" in kinds_present
    assert "identity" in kinds_present
    # Two core_value nodes from "Speed\nClarity"
    values = [n for n in core.nodes if n.kind == "core_value"]
    labels = {n.label for n in values}
    assert {"Speed", "Clarity"} <= labels


# ---------------------------------------------------------------------------
# populated v0.1 — sub-services under service-root become Details
# ---------------------------------------------------------------------------


def test_v01_services_migrate_to_overview_without_details(plot_root: Path) -> None:
    nodes = _v01_seed_nodes()
    nodes.extend(
        [
            _v01_node(
                "order",
                kind="service",
                label="주문",
                parent_id="service-root",
            ),
            _v01_node(
                "order-cart",
                kind="service",
                label="장바구니",
                parent_id="order",
            ),
            _v01_node(
                "pay",
                kind="service",
                label="결제",
                parent_id="service-root",
            ),
        ]
    )
    edges = _v01_seed_edges()
    edges.append(
        {
            "id": "e-order-cart",
            "source": "order",
            "target": "order-cart",
            "sourceHandle": None,
            "targetHandle": None,
            "label": "decomposes",
            "style": "solid",
            "action_verb": "decomposes",
            "value_form": [],
        }
    )
    _write_v01_sketch(plot_root, "alpha", "Alpha", nodes=nodes, edges=edges)

    migrate_v01_to_v02(plot_root)
    overview = read_canvas(plot_root, "alpha", "services")
    labels = {n.label for n in overview.nodes}
    # Top-level v0.1 services land on the overview.
    assert "주문" in labels and "결제" in labels

    # D-2026-06-17-D — detail canvases are per **feature** now, and v0.1
    # predates the feature kind, so migration creates NO detail canvases. The
    # v0.1 service decomposition (the "장바구니" sub-service that used to seed
    # order's detail) is dropped — the user re-authors it as a feature after
    # migrating, and the live sync seeds that feature's detail on first open.
    assert list_feature_details(plot_root, "alpha") == []
    assert "장바구니" not in labels


# ---------------------------------------------------------------------------
# malformed v0.1 files
# ---------------------------------------------------------------------------


def test_malformed_v01_file_is_skipped(plot_root: Path) -> None:
    _write_v01_sketch(plot_root, "ok", "OK")
    (plot_root / "sketches" / "broken.json").write_text("not json", encoding="utf-8")
    migrated = migrate_v01_to_v02(plot_root)
    assert migrated == ["ok"]
    # Broken file is left alone
    assert (plot_root / "sketches" / "broken.json").exists()


def test_migrated_backup_is_inspectable(plot_root: Path) -> None:
    """The ``.v01.bak`` file is still valid JSON so humans can diff it
    against the new folder layout or roll back by hand."""
    _write_v01_sketch(plot_root, "alpha", "Alpha")
    migrate_v01_to_v02(plot_root)
    raw = json.loads((plot_root / "sketches" / "alpha.json.v01.bak").read_text(encoding="utf-8"))
    assert raw["id"] == "alpha"
    assert raw["version"] == 1


# ---------------------------------------------------------------------------
# v0.16.34 — page-load refetch storm regression (D-2026-05-13-K)
# ---------------------------------------------------------------------------


def test_upgrade_foundation_is_idempotent_when_anchor_in_project_doc(
    plot_root: Path,
) -> None:
    """Regression: page-load refetch storm.

    Pre-v0.13 ``upgrade_foundation_canvas_if_needed`` step 4 would
    synthesise a ``kind=project`` anchor node when none existed in
    ``canvas.json``. After v0.13 Phase 0 moved the anchor into
    ``ProjectDoc.anchors``, step 4 became a no-op-that-isn't:

      1. upgrade adds anchor node to canvas.json (write 1).
      2. ``_evict_legacy_project_anchor`` on next read removes it
         (write 2).
      3. Both writes touch the file → watcher → broadcast → viewer
         refetch → step 1 again → infinite loop.

    The guard added in v0.16.34 short-circuits step 4 when project.json
    already carries an anchor for ``foundation``. This test pins the
    new behaviour: calling ``upgrade_foundation_canvas_if_needed``
    twice on a v0.13-shaped project must not modify canvas.json on the
    second call.
    """
    from mashbill.folder_io import _canvas_file, _project_file, _write_json
    from mashbill.migrate import upgrade_foundation_canvas_if_needed

    project_id = "pj"
    project_dir = plot_root / project_id
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "foundation").mkdir(exist_ok=True)

    # v0.13-shaped project.json with anchors.foundation populated.
    _write_json(
        _project_file(plot_root, project_id),
        {
            "id": project_id,
            "name": "Test",
            "created": "2026-05-13",
            "updated": "2026-05-13T00:00:00+00:00",
            "version": 2,
            "anchors": {
                "foundation": {
                    "x": -75.0,
                    "y": -75.0,
                    "width": 150.0,
                    "height": 150.0,
                    "color": "#fef3c7",
                    "shape": "circle",
                }
            },
        },
    )
    # canvas.json with only user nodes (no kind=project entry).
    _write_json(
        _canvas_file(plot_root, project_id, "foundation"),
        {
            "canvas_id": "foundation",
            "canvas_kind": "foundation",
            "feature_ref": None,
            "nodes": [
                {
                    "id": "m1",
                    "label": "Mission",
                    "kind": "mission",
                    "x": 0,
                    "y": 0,
                    "width": 200,
                    "height": 100,
                    "color": "#fef3c7",
                    "shape": "rounded",
                    "icon": None,
                    "parent_id": None,
                    "collapsed": False,
                    "is_root": False,
                    "details_path": None,
                    "owner": None,
                }
            ],
            "edges": [],
        },
    )

    canvas_path = _canvas_file(plot_root, project_id, "foundation")
    # First call: ProjectDoc.anchors already has 'foundation' → no synthesis.
    changed_first = upgrade_foundation_canvas_if_needed(plot_root, project_id)
    assert changed_first is False, (
        "step 4 must not add a kind=project node when ProjectDoc.anchors "
        "already carries the anchor — that would create the v0.16.34 "
        "refetch-storm loop."
    )
    mtime_after_first = canvas_path.stat().st_mtime

    # Second call: still no-op.
    changed_second = upgrade_foundation_canvas_if_needed(plot_root, project_id)
    assert changed_second is False
    mtime_after_second = canvas_path.stat().st_mtime

    # File mtime must not advance on either call (write would advance it).
    assert mtime_after_first == mtime_after_second, (
        "canvas.json mtime advanced between two idle upgrades — that is "
        "the page-load refetch-storm signature."
    )


def test_upgrade_foundation_still_synthesises_anchor_for_pre_v013_project(
    plot_root: Path,
) -> None:
    """The guard added in v0.16.34 must not regress the original
    pre-v0.13 use case: a project.json without an anchor entry should
    still get its anchor synthesised on first read."""
    from mashbill.folder_io import _canvas_file, _project_file, _write_json
    from mashbill.migrate import upgrade_foundation_canvas_if_needed

    project_id = "pj"
    project_dir = plot_root / project_id
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "foundation").mkdir(exist_ok=True)

    # Pre-v0.13-shaped project.json — no 'anchors' field.
    _write_json(
        _project_file(plot_root, project_id),
        {
            "id": project_id,
            "name": "Legacy",
            "created": "2026-01-01",
            "updated": "2026-01-01T00:00:00+00:00",
            "version": 1,
        },
    )
    # canvas.json without any kind=project node either.
    _write_json(
        _canvas_file(plot_root, project_id, "foundation"),
        {
            "canvas_id": "foundation",
            "canvas_kind": "foundation",
            "feature_ref": None,
            "nodes": [],
            "edges": [],
        },
    )

    changed = upgrade_foundation_canvas_if_needed(plot_root, project_id)
    assert changed is True, "legacy project (no anchors) must get synthesis"

    raw = json.loads(_canvas_file(plot_root, project_id, "foundation").read_text(encoding="utf-8"))
    has_project_node = any(n.get("kind") == "project" for n in raw["nodes"])
    assert has_project_node, "step 4 must still seed the anchor when missing"
