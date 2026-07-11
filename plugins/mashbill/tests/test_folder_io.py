"""Folder-based project IO for Novel v0.8 (wrapper-less canvas-grouped layout).

Layout
------

    .plot/{project_id}/
      project.json                   — ProjectDoc metadata
      foundation/canvas.json         — CanvasDoc (canvas_kind = "foundation")
      actors/canvas.json             — CanvasDoc (canvas_kind = "actors")
      services/
        canvas.json                  — top-view (canvas_kind = "services")
        {service_id}/
          index.md                   — Service node long-form (opt-in)
          detail.json                — CanvasDoc (canvas_kind = "feature")
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mashbill.folder_io import (
    create_project,
    delete_project,
    list_feature_details,
    read_canvas,
    read_project,
    write_canvas,
    write_project,
)
from mashbill.models import (
    ActorNode,
    ActorRefNode,
    CanvasDoc,
    FeatureNode,
)
from mashbill.workspace import resolve_plot_root


@pytest.fixture
def plot_root(tmp_path: Path) -> Path:
    # D-2026-06-11-C/D: workspace = tmp_path IS the git repo. Novel never
    # auto-inits, but publish tests need a real repo, so we init here.
    from mashbill.git_store import init_workspace_repo

    init_workspace_repo(tmp_path)
    return resolve_plot_root(str(tmp_path))


# ---------------------------------------------------------------------------
# create_project
# ---------------------------------------------------------------------------


def test_create_project_builds_flat_layout(plot_root: Path) -> None:
    """S2 (D-2026-06-21-AB): one project per .noory/plot, stored **flat** —
    project.json + canvas dirs land directly under the root, with no
    intermediate {project_id}/ folder."""
    proj = create_project(plot_root, "alpha", "Alpha")
    assert proj.id == "alpha"
    assert proj.name == "Alpha"
    assert proj.version == 3  # v0.13 Phase 0
    assert (plot_root / "project.json").is_file()
    assert (plot_root / "foundation" / "canvas.json").is_file()
    assert (plot_root / "actors" / "canvas.json").is_file()
    assert (plot_root / "services" / "canvas.json").is_file()
    # no nested {project_id}/ layer
    assert not (plot_root / "alpha").exists()


def test_read_project_with_wrong_id_raises(plot_root: Path) -> None:
    """Flat layout addresses the lone project by the root, so a mismatched
    id must still 404 rather than silently returning the only project."""
    create_project(plot_root, "alpha", "Alpha")
    with pytest.raises(FileNotFoundError):
        read_project(plot_root, "bravo")


def test_create_project_foundation_starts_blank(plot_root: Path) -> None:
    """D-2026-07-04-P — blank-canvas start: no Mission/Core value/Identity
    seeds and no anchor edges (supersedes the D-2026-06-21-H seed layout).
    Content lands only through the conversation / the user's hand."""
    create_project(plot_root, "alpha", "Alpha")
    foundation = read_canvas(plot_root, "alpha", "foundation")
    assert foundation.canvas_kind == "foundation"
    assert foundation.nodes == []
    assert foundation.edges == []


def test_create_project_actors_starts_blank(plot_root: Path) -> None:
    """D-2026-07-04-P — no Operator/User placeholder actors (supersedes the
    v0.11 seed pair and its ≥ 2-actor minimum)."""
    create_project(plot_root, "alpha", "Alpha")
    actors = read_canvas(plot_root, "alpha", "actors")
    assert actors.canvas_kind == "actors"
    assert actors.nodes == []
    assert actors.edges == []


def test_create_project_seeds_services_canvas(plot_root: Path) -> None:
    """v0.13 Phase 0: services canvas starts empty (no project node)."""
    create_project(plot_root, "alpha", "Alpha")
    overview = read_canvas(plot_root, "alpha", "services")
    assert overview.canvas_kind == "services"
    assert all(n.kind != "project" for n in overview.nodes)


def test_create_project_seeds_anchors_in_project_doc(plot_root: Path) -> None:
    """v0.13 Phase 0: ProjectDoc carries anchor placements per canvas."""
    proj = create_project(plot_root, "alpha", "Alpha")
    assert "foundation" in proj.anchors
    assert "actors" in proj.anchors
    assert "services" in proj.anchors
    assert proj.anchors["foundation"].shape == "circle"


def test_create_duplicate_raises(plot_root: Path) -> None:
    create_project(plot_root, "alpha", "Alpha")
    with pytest.raises(FileExistsError):
        create_project(plot_root, "alpha", "Again")


def test_create_second_project_in_same_root_rejected(plot_root: Path) -> None:
    """One project per ``.noory/plot`` dir (one-project-per-dir, S3 /
    D-2026-06-21-AA). Creating a *second* project — even with a fresh id —
    under a root that already holds one is rejected. ``FileExistsError`` is
    what the HTTP create endpoint maps to 409. Multiple services live in
    sibling directories, each with its own ``.noory/plot``.
    """
    create_project(plot_root, "alpha", "Alpha")
    with pytest.raises(FileExistsError):
        create_project(plot_root, "beta", "Beta")


def test_create_in_sibling_dirs_is_allowed(tmp_path: Path) -> None:
    """Two projects in sibling workspace directories — each with its own
    ``.noory/plot`` — both succeed. The one-per-dir guard is per-root, not
    per-workspace (D-2026-06-21-AA / D-2026-06-12-A narrowed).
    """
    (tmp_path / "web").mkdir()
    (tmp_path / "api").mkdir()
    root_a = resolve_plot_root(str(tmp_path / "web"))
    root_b = resolve_plot_root(str(tmp_path / "api"))
    create_project(root_a, "web", "Web")
    create_project(root_b, "api", "Api")
    assert read_project(root_a, "web").id == "web"
    assert read_project(root_b, "api").id == "api"


# ---------------------------------------------------------------------------
# read / write
# ---------------------------------------------------------------------------


def test_read_project_returns_metadata(plot_root: Path) -> None:
    proj = create_project(plot_root, "alpha", "Alpha")
    loaded = read_project(plot_root, "alpha")
    assert loaded.id == "alpha"
    assert loaded.name == "Alpha"
    assert loaded.created == proj.created


def test_write_project_updates_timestamp(plot_root: Path) -> None:
    proj = create_project(plot_root, "alpha", "Alpha")
    before = proj.updated
    renamed = proj.model_copy(update={"name": "Renamed"})
    write_project(plot_root, renamed)
    loaded = read_project(plot_root, "alpha")
    assert loaded.name == "Renamed"
    assert loaded.updated >= before


def test_read_missing_project_raises(plot_root: Path) -> None:
    with pytest.raises(FileNotFoundError):
        read_project(plot_root, "ghost")


def test_write_canvas_round_trip(plot_root: Path) -> None:
    create_project(plot_root, "alpha", "Alpha")
    canvas = CanvasDoc(
        canvas_id="actors",
        canvas_kind="actors",
        nodes=[
            ActorNode(id="user", label="사용자"),
            ActorNode(id="admin", label="관리자"),
        ],
    )
    write_canvas(plot_root, "alpha", canvas)
    loaded = read_canvas(plot_root, "alpha", "actors")
    # v0.11.4 read backfills the project anchor; just check the actor labels.
    actor_labels = sorted(n.label for n in loaded.nodes if n.kind == "actor")
    assert actor_labels == ["관리자", "사용자"]


def test_write_canvas_rejects_wrong_project(plot_root: Path) -> None:
    create_project(plot_root, "alpha", "Alpha")
    with pytest.raises(FileNotFoundError):
        write_canvas(
            plot_root,
            "ghost",
            CanvasDoc(
                canvas_id="actors",
                canvas_kind="actors",
                nodes=[
                    ActorNode(id="op", label="O"),
                    ActorNode(id="user", label="U"),
                ],
            ),
        )


def test_read_missing_canvas_raises(plot_root: Path) -> None:
    create_project(plot_root, "alpha", "Alpha")
    # Valid project, but no such detail canvas
    with pytest.raises(FileNotFoundError):
        read_canvas(plot_root, "alpha", "feature", service_id="nope")


# ---------------------------------------------------------------------------
# services-detail
# ---------------------------------------------------------------------------


def test_list_feature_details_empty_by_default(plot_root: Path) -> None:
    create_project(plot_root, "alpha", "Alpha")
    assert list_feature_details(plot_root, "alpha") == []


def _detail_with_actor_refs(service_id: str = "order") -> CanvasDoc:
    """v0.27.16 (D-2026-05-28-K) — feature invariant loosened to
    ≥ 1 actor_ref. This fixture keeps the 2-actor seed because most
    folder_io tests don't care about the count — they exercise sync /
    publish / archive logic that needs *some* doc to bounce off. The
    invariant itself is covered by ``test_canvas_doc.py``.

    Root is a feature (D-2026-06-17-D — the detail canvas drills into a
    feature, not a service)."""
    return CanvasDoc(
        canvas_id=service_id,
        canvas_kind="feature",
        feature_ref=service_id,
        nodes=[
            FeatureNode(id=service_id, label="주문"),
            ActorRefNode(
                id=f"{service_id}-op",
                label="→ op",
                ref_actor_id="operator",

            ),
            ActorRefNode(
                id=f"{service_id}-user",
                label="→ user",
                ref_actor_id="user",

            ),
        ],
    )


def test_write_and_list_feature(plot_root: Path) -> None:
    create_project(plot_root, "alpha", "Alpha")
    detail = _detail_with_actor_refs("order")
    write_canvas(plot_root, "alpha", detail)
    assert list_feature_details(plot_root, "alpha") == ["order"]
    loaded = read_canvas(plot_root, "alpha", "feature", service_id="order")
    assert loaded.feature_ref == "order"
    assert loaded.nodes[0].id == "order"


def test_detail_canvas_path_uses_service_id(plot_root: Path) -> None:
    create_project(plot_root, "alpha", "Alpha")
    detail = _detail_with_actor_refs("order")
    write_canvas(plot_root, "alpha", detail)
    assert (plot_root / "services" / "order" / "detail.json").is_file()


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


def test_delete_project_removes_folder(plot_root: Path) -> None:
    create_project(plot_root, "alpha", "Alpha")
    delete_project(plot_root, "alpha")
    # S2 flat layout: the .noory/plot root survives (empty "create here"
    # slot), but the project's files are gone.
    assert plot_root.is_dir()
    assert not (plot_root / "project.json").exists()
    assert not (plot_root / "foundation").exists()


def test_delete_missing_project_raises(plot_root: Path) -> None:
    with pytest.raises(FileNotFoundError):
        delete_project(plot_root, "never-existed")


# ---------------------------------------------------------------------------
# git repo wiring (v0.4)
# ---------------------------------------------------------------------------


def test_create_project_does_not_init_git_at_plot_root(plot_root: Path) -> None:
    """D-2026-06-11-D — Novel never auto-inits. The workspace fixture initialised
    the repo at the workspace root (`tmp_path`, not `plot_root`); create_project
    must not synthesise a nested `.git/` under `.noory/plot/`."""
    create_project(plot_root, "alpha", "Alpha")
    # No nested repo at the plot data root (flat layout — the project IS
    # the root's contents).
    assert not (plot_root / ".git").exists()


def test_create_project_leaves_workspace_repo_empty(plot_root: Path) -> None:
    """Quiet-repo principle: project creation does not commit. The workspace
    repo (initialised by the fixture) stays at zero commits."""
    import subprocess

    create_project(plot_root, "alpha", "Alpha")
    workspace = plot_root.parent.parent
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"],
        cwd=workspace,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0


def test_write_canvas_does_not_commit(plot_root: Path) -> None:
    """Editing a canvas must not bump the git log — only tags do."""
    import subprocess

    create_project(plot_root, "alpha", "Alpha")
    write_canvas(
        plot_root,
        "alpha",
        CanvasDoc(
            canvas_id="actors",
            canvas_kind="actors",
            nodes=[
                ActorNode(id="op", label="O"),
                ActorNode(id="u", label="U"),
            ],
        ),
    )
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"],
        cwd=plot_root,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0  # still no commits


# ---------------------------------------------------------------------------
# v0.16.38 — D-2026-05-13-N: anchor edges survive the defensive orphan-edge
# cleanup in ``_evict_legacy_project_anchor``.
# ---------------------------------------------------------------------------


def test_read_canvas_preserves_anchor_edges_across_repeated_reads(
    plot_root: Path,
) -> None:
    """Regression: anchor edges (source/target = PROJECT_ANCHOR_ID) must
    survive the defensive orphan-edge cleanup in
    ``_evict_legacy_project_anchor``. Prior to D-2026-05-13-N the
    cleanup's ``node_ids`` set excluded the synthetic anchor id, so
    every read stripped anchor edges from disk and the watcher fired,
    causing the refetch storm + on-screen 'edges disappear after
    reload' symptom (user 2026-05-13).

    This test: write a foundation canvas with two anchor edges, read
    it three times, assert canvas.json's edges array is unchanged and
    the file's mtime does not advance between reads (write would
    advance mtime — the storm trigger)."""
    from mashbill.folder_io import _canvas_file
    from mashbill.models import (
        PROJECT_ANCHOR_ID,
        CoreValueNode,
        IdentityNode,
        MissionNode,
        SketchEdge,
    )

    create_project(plot_root, "alpha", "Alpha")
    write_canvas(
        plot_root,
        "alpha",
        CanvasDoc(
            canvas_id="foundation",
            canvas_kind="foundation",
            nodes=[
                MissionNode(id="m", label="Mission"),
                CoreValueNode(id="cv", label="CoreValue"),
                IdentityNode(id="id1", label="Identity"),
            ],
            edges=[
                SketchEdge(
                    id="e_anchor_1",
                    source=PROJECT_ANCHOR_ID,
                    target="m",
                ),
                SketchEdge(
                    id="e_anchor_2",
                    source="cv",
                    target=PROJECT_ANCHOR_ID,
                ),
            ],
        ),
    )

    canvas_path = _canvas_file(plot_root, "alpha", "foundation")
    mtime_baseline = canvas_path.stat().st_mtime

    # Three idle reads must leave the file untouched.
    for _ in range(3):
        doc = read_canvas(plot_root, "alpha", "foundation")
        assert len(doc.edges) == 2, "anchor edges must survive read — D-2026-05-13-N regression"
        edge_endpoints = {(e.source, e.target) for e in doc.edges}
        assert (PROJECT_ANCHOR_ID, "m") in edge_endpoints
        assert ("cv", PROJECT_ANCHOR_ID) in edge_endpoints

    mtime_after = canvas_path.stat().st_mtime
    assert mtime_after == mtime_baseline, (
        "canvas.json mtime advanced between idle reads — the defensive "
        "cleanup is rewriting anchor edges away. That's the v0.16.38 "
        "storm trigger D-2026-05-13-N must prevent."
    )


def test_orphan_non_anchor_edges_still_stripped(plot_root: Path) -> None:
    """The anchor whitelist must not break the original orphan-edge
    cleanup intent: edges referencing a truly missing node (not the
    anchor) should still be stripped on read."""
    import json

    from mashbill.folder_io import _canvas_file
    from mashbill.models import CoreValueNode, IdentityNode, MissionNode

    create_project(plot_root, "alpha", "Alpha")
    canvas_path = _canvas_file(plot_root, "alpha", "foundation")

    # Manually write a foundation canvas with an orphan edge bypassing
    # Pydantic validation — simulating a pre-v0.13.0 storage state.
    raw = {
        "canvas_id": "foundation",
        "canvas_kind": "foundation",
        "feature_ref": None,
        "nodes": [
            MissionNode(id="m", label="M").model_dump(),
            CoreValueNode(id="cv", label="CV").model_dump(),
            IdentityNode(id="id1", label="Id").model_dump(),
        ],
        "edges": [
            {
                "id": "e_orphan",
                "source": "ghost_node",  # not in nodes, not the anchor
                "target": "m",
                "sourceHandle": None,
                "targetHandle": None,
                "label": None,
                "style": "solid",
                "action_verb": None,
                "value_form": [],
            },
        ],
    }
    canvas_path.write_text(json.dumps(raw), encoding="utf-8")

    # First read should strip the orphan edge.
    doc = read_canvas(plot_root, "alpha", "foundation")
    assert len(doc.edges) == 0, "orphan (non-anchor) edge must still be stripped"


# ---------------------------------------------------------------------------
# v0.17 Phase 1 — JSON SSOT (D-2026-05-16-A) absorption migrator
# ---------------------------------------------------------------------------


def _seed_foundation_with_md(
    plot_root: Path,
    project_id: str,
    *,
    json_mission_statement: str = "",
    json_mission_body: str = "",
    md_statement: str | None = "We help **users** discover.\n\n- A\n- B",
    md_free_prose: str | None = "Longer notes here.\n## subsection\nWith MD syntax.",
    mission_label: str = "Mission",
    json_details_path: str | None = None,
) -> tuple[Path, Path]:
    """Helper: bootstrap a foundation canvas with the default mission +
    core_value + identity nodes (validator requires all three) and a
    legacy MD file alongside the mission node at the canonical path.
    Returns (canvas_path, md_path). Set md_* to None to skip writing
    that MD section; set json_* to pre-populate JSON values."""
    import json as _json

    from mashbill.folder_io import _canvas_file, _foundation_md_path
    from mashbill.models import CoreValueNode, IdentityNode, MissionNode

    create_project(plot_root, project_id, project_id.capitalize())
    canvas_path = _canvas_file(plot_root, project_id, "foundation")
    mission_dict = MissionNode(id="m", label=mission_label).model_dump()
    if json_mission_statement:
        mission_dict["statement"] = json_mission_statement
    if json_mission_body:
        mission_dict["body"] = json_mission_body
    if json_details_path is not None:
        mission_dict["details_path"] = json_details_path
    core_value_dict = CoreValueNode(id="cv", label="Value").model_dump()
    identity_dict = IdentityNode(id="id1", label="Persona").model_dump()
    raw = {
        "canvas_id": "foundation",
        "canvas_kind": "foundation",
        "feature_ref": None,
        "nodes": [mission_dict, core_value_dict, identity_dict],
        "edges": [],
    }
    canvas_path.write_text(_json.dumps(raw), encoding="utf-8")

    md_path = _foundation_md_path(plot_root, project_id, "mission", "m", mission_label)
    md_chunks: list[str] = [f"# {mission_label}", ""]
    if md_statement is not None:
        md_chunks += ["## Mission", md_statement, ""]
    if md_free_prose is not None:
        md_chunks += ["---", md_free_prose]
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text("\n".join(md_chunks), encoding="utf-8")
    return canvas_path, md_path


def test_absorb_md_typed_text_into_json_basic(plot_root: Path) -> None:
    """JSON empty + MD populated → typed fields + body filled (MD-syntax
    strings preserved verbatim), MD moved to ``foundation/_legacy/``,
    details_path cleared to None."""
    from mashbill.folder_io import _legacy_md_dir

    canvas_path, md_path = _seed_foundation_with_md(plot_root, "alpha")

    doc = read_canvas(plot_root, "alpha", "foundation")
    mission = next(n for n in doc.nodes if n.kind == "mission")

    assert mission.statement == "We help **users** discover.\n\n- A\n- B"
    # parse_md_template normalises free-prose to rstripped + trailing "\n".
    assert mission.body == "Longer notes here.\n## subsection\nWith MD syntax.\n"
    assert mission.details_path is None

    assert not md_path.exists(), "original MD must be moved out of the canonical path"
    legacy_md = _legacy_md_dir(plot_root, "alpha") / md_path.name
    assert legacy_md.exists(), "legacy quarantine must contain the original MD"


def test_absorb_md_typed_text_into_json_both_populated_json_wins(plot_root: Path) -> None:
    """JSON populated + MD populated → JSON values retained; MD still
    quarantined."""
    from mashbill.folder_io import _legacy_md_dir

    canvas_path, md_path = _seed_foundation_with_md(
        plot_root,
        "alpha",
        json_mission_statement="json-wins",
        json_mission_body="json-body-wins",
    )

    doc = read_canvas(plot_root, "alpha", "foundation")
    mission = next(n for n in doc.nodes if n.kind == "mission")
    assert mission.statement == "json-wins"
    assert mission.body == "json-body-wins"
    assert not md_path.exists()
    legacy_md = _legacy_md_dir(plot_root, "alpha") / md_path.name
    assert legacy_md.exists(), "MD is quarantined regardless of conflict outcome"


def test_absorb_md_typed_text_into_json_no_md_file(plot_root: Path) -> None:
    """No MD on disk → no field absorption. details_path cleared only
    if it pointed at the canonical (absent) MD path."""
    import json as _json

    from mashbill.folder_io import _canvas_file, _foundation_md_path
    from mashbill.models import CoreValueNode, IdentityNode, MissionNode

    create_project(plot_root, "alpha", "Alpha")
    canonical_rel = str(
        _foundation_md_path(plot_root, "alpha", "mission", "m", "Mission").relative_to(plot_root)
    ).replace("\\", "/")

    canvas_path = _canvas_file(plot_root, "alpha", "foundation")
    mission_dict = MissionNode(id="m", label="Mission", statement="kept").model_dump()
    mission_dict["details_path"] = canonical_rel
    raw = {
        "canvas_id": "foundation",
        "canvas_kind": "foundation",
        "feature_ref": None,
        "nodes": [
            mission_dict,
            CoreValueNode(id="cv", label="Value").model_dump(),
            IdentityNode(id="id1", label="Persona").model_dump(),
        ],
        "edges": [],
    }
    canvas_path.write_text(_json.dumps(raw), encoding="utf-8")

    doc = read_canvas(plot_root, "alpha", "foundation")
    mission = next(n for n in doc.nodes if n.kind == "mission")
    assert mission.statement == "kept"
    assert mission.details_path is None, "canonical-pointing details_path is cleared"


def test_absorb_md_typed_text_into_json_idempotent(plot_root: Path) -> None:
    """Calling read_canvas three times moves the MD exactly once; the
    _legacy/ directory carries one entry; mtime is stable on repeat."""
    from mashbill.folder_io import _legacy_md_dir

    canvas_path, md_path = _seed_foundation_with_md(plot_root, "alpha")
    read_canvas(plot_root, "alpha", "foundation")
    legacy_dir = _legacy_md_dir(plot_root, "alpha")
    legacy_entries_after_first = sorted(p.name for p in legacy_dir.iterdir())
    canvas_mtime_after_first = canvas_path.stat().st_mtime

    for _ in range(2):
        read_canvas(plot_root, "alpha", "foundation")

    legacy_entries_after_third = sorted(p.name for p in legacy_dir.iterdir())
    assert legacy_entries_after_third == legacy_entries_after_first, (
        "_legacy/ must not gain duplicates across repeated reads"
    )
    assert canvas_path.stat().st_mtime == canvas_mtime_after_first, (
        "canvas.json mtime must be stable on idle reads after the one-shot migration"
    )


def test_absorb_md_typed_text_into_json_preserves_md_syntax(plot_root: Path) -> None:
    """Typed field values + body retain MD syntax (bold, bullets,
    headings, newlines) verbatim."""
    raw_md_value = "**Bold** and `code`.\n\n- bullet one\n- bullet two"
    body_md = "## Long-form\n\nMore *italic* text.\n\n```python\nprint('hi')\n```"

    _seed_foundation_with_md(
        plot_root,
        "alpha",
        md_statement=raw_md_value,
        md_free_prose=body_md,
    )

    doc = read_canvas(plot_root, "alpha", "foundation")
    mission = next(n for n in doc.nodes if n.kind == "mission")
    assert mission.statement == raw_md_value
    # parse_md_template normalises free-prose to rstripped + trailing "\n".
    assert mission.body == body_md + "\n"


def test_absorb_md_typed_text_into_json_post_hr_text_lands_in_body(plot_root: Path) -> None:
    """The post-``---`` free-prose section maps to the new body field."""
    _seed_foundation_with_md(
        plot_root,
        "alpha",
        md_statement="foo",
        md_free_prose="long notes\n## subsection",
    )
    doc = read_canvas(plot_root, "alpha", "foundation")
    mission = next(n for n in doc.nodes if n.kind == "mission")
    assert mission.statement == "foo"
    assert mission.body == "long notes\n## subsection\n"


def test_absorb_md_typed_text_into_json_duplicate_slug_collision(plot_root: Path) -> None:
    """A pre-existing _legacy entry at the same slug must not be
    overwritten; the migrator appends the short node-id suffix and
    keeps both files."""
    import json as _json

    from mashbill.folder_io import _canvas_file, _foundation_md_path, _legacy_md_dir
    from mashbill.models import CoreValueNode, IdentityNode, MissionNode

    create_project(plot_root, "alpha", "Alpha")
    canvas_path = _canvas_file(plot_root, "alpha", "foundation")

    legacy_dir = _legacy_md_dir(plot_root, "alpha")
    legacy_dir.mkdir(parents=True, exist_ok=True)
    existing = legacy_dir / "mission-mission.md"
    existing.write_text("# preexisting legacy content", encoding="utf-8")

    mission_dict = MissionNode(id="m_aaaaaaaa", label="Mission").model_dump()
    canvas_path.write_text(
        _json.dumps(
            {
                "canvas_id": "foundation",
                "canvas_kind": "foundation",
                "feature_ref": None,
                "nodes": [
                    mission_dict,
                    CoreValueNode(id="cv", label="Value").model_dump(),
                    IdentityNode(id="id1", label="Persona").model_dump(),
                ],
                "edges": [],
            }
        ),
        encoding="utf-8",
    )
    md_path = _foundation_md_path(plot_root, "alpha", "mission", "m_aaaaaaaa", "Mission")
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text("# Mission\n\n## What we do\nnew content\n", encoding="utf-8")

    read_canvas(plot_root, "alpha", "foundation")

    assert existing.read_text(encoding="utf-8") == "# preexisting legacy content", (
        "pre-existing _legacy entry must not be overwritten"
    )
    suffixed = legacy_dir / "mission-mission-m_aaaaaa.md"
    assert suffixed.exists(), (
        f"collision-suffixed legacy file must be created; "
        f"have {sorted(p.name for p in legacy_dir.iterdir())}"
    )
    assert "new content" in suffixed.read_text(encoding="utf-8")


def test_migrate_assign_edge_relation_on_read(plot_root: Path) -> None:
    """v0.30.0 (D-2026-05-31-C) — a pre-v0.30 edge with no ``relation``
    key gets one assigned on first read via classify_edge(canvas,
    source-node kind). Idempotent: a second read does not rewrite."""
    import json

    from mashbill.folder_io import _canvas_file

    create_project(plot_root, "alpha", "Alpha")
    # Write a raw foundation canvas.json whose edges lack ``relation``
    # (simulating pre-v0.30 data): mission -> anchor (essence source =>
    # injection) and a non-essence edge (=> flow).
    path = _canvas_file(plot_root, "alpha", "foundation")
    raw = {
        "canvas_id": "foundation",
        "canvas_kind": "foundation",
        "nodes": [
            {"id": "m", "label": "Mission", "kind": "mission"},
            {"id": "id1", "label": "Identity", "kind": "identity"},
        ],
        "edges": [
            {"id": "e1", "source": "m", "target": "id1"},
            {"id": "e2", "source": "id1", "target": "m"},
        ],
    }
    path.write_text(json.dumps(raw), encoding="utf-8")

    doc = read_canvas(plot_root, "alpha", "foundation")
    by_id = {e.id: e for e in doc.edges}
    # mission source => injection; identity source => injection too
    # (both are essence masters on the foundation canvas).
    assert by_id["e1"].relation == "injection"
    assert by_id["e2"].relation == "injection"

    # Idempotent: a second read leaves the file's mtime unchanged.
    mtime = path.stat().st_mtime
    read_canvas(plot_root, "alpha", "foundation")
    assert path.stat().st_mtime == mtime, "second read must not rewrite"


def test_migrate_assign_edge_relation_actors_inheritance(plot_root: Path) -> None:
    """On the actors canvas every directed edge migrates to
    ``inheritance`` regardless of source kind (single edge type)."""
    import json

    from mashbill.folder_io import _canvas_file

    create_project(plot_root, "alpha", "Alpha")
    path = _canvas_file(plot_root, "alpha", "actors")
    raw = {
        "canvas_id": "actors",
        "canvas_kind": "actors",
        "nodes": [
            {"id": "a1", "label": "Operator", "kind": "actor"},
            {"id": "a2", "label": "User", "kind": "actor"},
        ],
        "edges": [
            {"id": "e1", "source": "a1", "target": "a2"},
        ],
    }
    path.write_text(json.dumps(raw), encoding="utf-8")

    doc = read_canvas(plot_root, "alpha", "actors")
    assert doc.edges[0].relation == "inheritance"
