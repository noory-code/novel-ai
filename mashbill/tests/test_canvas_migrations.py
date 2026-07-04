"""Unit tests for ``mashbill.canvas_migrations`` — the read-path healing
helpers (lazy migrations, foundation MD absorb, legacy anchor eviction).

These exercise the migration helpers *directly* (rather than only through
``read_canvas``) so the branch-level behaviour each migrator owns is pinned
in isolation: the no-op guards, the file-move side effects, the persist
points, and the conflict/give-up policies. A regression in any one of these
transforms would silently corrupt user data on the next read — that is the
whole point of these guards.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mashbill.canvas_migrations import (
    _absorb_md_typed_text_into_json,
    _drop_disallowed_services_kinds,
    _evict_legacy_project_anchor,
    _foundation_md_path,
    _legacy_md_dir,
    _migrate_actor_isroot_to_false,
    _migrate_assign_edge_relation,
    _migrate_parent_id_to_directed_edges,
    _migrate_published_flat_to_kind_slug,
    _migrate_published_slug_to_id,
    collect_foundation_md_warnings,
)
from mashbill.folder_io import _canvas_file, _project_dir, create_project, read_project
from mashbill.workspace import resolve_plot_root


@pytest.fixture
def plot_root(tmp_path: Path) -> Path:
    from mashbill.git_store import init_workspace_repo

    init_workspace_repo(tmp_path)
    return resolve_plot_root(str(tmp_path))


# ---------------------------------------------------------------------------
# _migrate_actor_isroot_to_false (D-2026-05-19-D)
# ---------------------------------------------------------------------------


def test_actor_isroot_reset_only_actors_with_is_root_true() -> None:
    """Only ``actor`` nodes with ``is_root is True`` flip to False; a
    non-actor with is_root=True and an actor already False are untouched."""
    raw = {
        "nodes": [
            {"kind": "actor", "id": "a", "is_root": True},
            {"kind": "actor", "id": "b", "is_root": False},
            {"kind": "service", "id": "s", "is_root": True},  # not an actor
        ]
    }
    out = _migrate_actor_isroot_to_false(raw)
    by_id = {n["id"]: n for n in out["nodes"]}
    assert by_id["a"]["is_root"] is False  # the only one that flips
    assert by_id["b"]["is_root"] is False
    assert by_id["s"]["is_root"] is True  # service keeps its marker


def test_actor_isroot_reset_tolerates_non_list_and_non_dict() -> None:
    """``nodes`` missing / not a list → raw returned verbatim; a non-dict
    entry inside the list is skipped without raising."""
    # nodes absent entirely.
    assert _migrate_actor_isroot_to_false({}) == {}
    # nodes not a list.
    assert _migrate_actor_isroot_to_false({"nodes": "oops"}) == {"nodes": "oops"}
    # non-dict entry is skipped; the dict actor still migrates.
    raw = {"nodes": ["junk", {"kind": "actor", "id": "a", "is_root": True}]}
    out = _migrate_actor_isroot_to_false(raw)
    assert out["nodes"][0] == "junk"
    assert out["nodes"][1]["is_root"] is False


# ---------------------------------------------------------------------------
# _migrate_published_flat_to_kind_slug
# ---------------------------------------------------------------------------


def test_published_flat_file_moved_into_kind_slug_layout(plot_root: Path) -> None:
    """A legacy flat ``mission-our-mission-v1.2.md`` is relocated to
    ``published/mission/our-mission/v1.2.md`` and the flat file disappears."""
    create_project(plot_root, "alpha", "Alpha")
    pub = _project_dir(plot_root, "alpha") / "foundation" / "published"
    pub.mkdir(parents=True, exist_ok=True)
    flat = pub / "mission-our-mission-v1.2.md"
    flat.write_text("# published body", encoding="utf-8")

    _migrate_published_flat_to_kind_slug(_project_dir(plot_root, "alpha") / "foundation")

    dest = pub / "mission" / "our-mission" / "v1.2.md"
    assert dest.is_file()
    assert dest.read_text(encoding="utf-8") == "# published body"
    assert not flat.exists(), "the legacy flat file is renamed, not copied"


def test_published_flat_skips_non_matching_and_no_published_dir(plot_root: Path) -> None:
    """Files that don't match the legacy regex stay put; absence of a
    ``published/`` dir is a silent no-op."""
    create_project(plot_root, "alpha", "Alpha")
    foundation = _project_dir(plot_root, "alpha") / "foundation"
    # No published/ dir yet → no-op, no crash.
    _migrate_published_flat_to_kind_slug(foundation)

    pub = foundation / "published"
    pub.mkdir(parents=True, exist_ok=True)
    not_versioned = pub / "README.md"  # no -vX.Y suffix → no match
    not_versioned.write_text("keep me", encoding="utf-8")
    _migrate_published_flat_to_kind_slug(foundation)
    assert not_versioned.exists()
    assert not (pub / "readme").exists()


def test_published_flat_existing_destination_left_in_place(plot_root: Path) -> None:
    """If the new-layout destination already holds this version, the legacy
    flat file is NOT moved or deleted (never overwrite — leave for audit)."""
    create_project(plot_root, "alpha", "Alpha")
    pub = _project_dir(plot_root, "alpha") / "foundation" / "published"
    dest = pub / "mission" / "our-mission" / "v1.2.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("new-layout wins", encoding="utf-8")
    flat = pub / "mission-our-mission-v1.2.md"
    flat.write_text("legacy redundant", encoding="utf-8")

    _migrate_published_flat_to_kind_slug(pub.parent)

    assert flat.exists(), "redundant legacy file is left in place, not deleted"
    assert dest.read_text(encoding="utf-8") == "new-layout wins", "destination untouched"


# ---------------------------------------------------------------------------
# _migrate_published_slug_to_id (D-2026-05-18-A)
# ---------------------------------------------------------------------------


def test_published_slug_folder_renamed_to_node_id(plot_root: Path) -> None:
    """A ``published/mission/<slug>/`` folder is renamed to
    ``published/mission/<node_id>/`` when the raw canvas maps a node whose
    slugified label != its id."""
    create_project(plot_root, "alpha", "Alpha")
    canvas_dir = _project_dir(plot_root, "alpha") / "foundation"
    slug_dir = canvas_dir / "published" / "mission" / "our-mission"
    slug_dir.mkdir(parents=True, exist_ok=True)
    (slug_dir / "v1.0.md").write_text("body", encoding="utf-8")

    raw = {"nodes": [{"kind": "mission", "id": "m1", "label": "Our Mission"}]}
    _migrate_published_slug_to_id(canvas_dir, raw)

    id_dir = canvas_dir / "published" / "mission" / "m1"
    assert id_dir.is_dir()
    assert (id_dir / "v1.0.md").read_text(encoding="utf-8") == "body"
    assert not slug_dir.exists(), "slug folder is renamed away"


def test_published_slug_noop_when_slug_equals_id(plot_root: Path) -> None:
    """When slugify(label) == id the rename is skipped (folder stays)."""
    create_project(plot_root, "alpha", "Alpha")
    canvas_dir = _project_dir(plot_root, "alpha") / "foundation"
    same = canvas_dir / "published" / "mission" / "mission"
    same.mkdir(parents=True, exist_ok=True)
    (same / "v1.0.md").write_text("body", encoding="utf-8")

    # label "Mission" slugifies to "mission" == id → no-op.
    raw = {"nodes": [{"kind": "mission", "id": "mission", "label": "Mission"}]}
    _migrate_published_slug_to_id(canvas_dir, raw)
    assert same.is_dir(), "identical slug/id folder must not be touched"


def test_published_slug_conflict_leaves_slug_folder(plot_root: Path) -> None:
    """If the id-folder destination already exists, the slug folder is left
    in place for audit (never overwrite)."""
    create_project(plot_root, "alpha", "Alpha")
    canvas_dir = _project_dir(plot_root, "alpha") / "foundation"
    slug_dir = canvas_dir / "published" / "mission" / "our-mission"
    slug_dir.mkdir(parents=True, exist_ok=True)
    (slug_dir / "slug.md").write_text("slug", encoding="utf-8")
    id_dir = canvas_dir / "published" / "mission" / "m1"
    id_dir.mkdir(parents=True, exist_ok=True)
    (id_dir / "id.md").write_text("id", encoding="utf-8")

    raw = {"nodes": [{"kind": "mission", "id": "m1", "label": "Our Mission"}]}
    _migrate_published_slug_to_id(canvas_dir, raw)

    assert slug_dir.is_dir(), "occupied destination → slug folder survives"
    assert (slug_dir / "slug.md").exists()
    assert (id_dir / "id.md").exists()


def test_published_slug_skips_when_kind_dir_or_slug_dir_missing(plot_root: Path) -> None:
    """No ``published/<kind>/`` dir, or no ``<slug>/`` under it → silent skip,
    no crash, nothing created."""
    create_project(plot_root, "alpha", "Alpha")
    canvas_dir = _project_dir(plot_root, "alpha") / "foundation"
    (canvas_dir / "published").mkdir(parents=True, exist_ok=True)
    # kind dir 'mission' does not exist.
    raw = {"nodes": [{"kind": "mission", "id": "m1", "label": "Our Mission"}]}
    _migrate_published_slug_to_id(canvas_dir, raw)
    assert not (canvas_dir / "published" / "mission").exists()


def test_published_slug_skips_when_slug_dir_absent_but_kind_dir_present(
    plot_root: Path,
) -> None:
    """The ``<kind>/`` dir exists but holds no ``<slug>/`` folder → no rename,
    no id-folder created (line 127/128 guard)."""
    create_project(plot_root, "alpha", "Alpha")
    canvas_dir = _project_dir(plot_root, "alpha") / "foundation"
    (canvas_dir / "published" / "mission").mkdir(parents=True, exist_ok=True)
    raw = {"nodes": [{"kind": "mission", "id": "m1", "label": "Our Mission"}]}
    _migrate_published_slug_to_id(canvas_dir, raw)
    assert not (canvas_dir / "published" / "mission" / "m1").exists()


def test_published_slug_guards_malformed_nodes(plot_root: Path) -> None:
    """``nodes`` not a list, a non-dict entry, and nodes missing
    id/label/kind types are all skipped without raising and without
    creating anything (lines 107-118 guards)."""
    create_project(plot_root, "alpha", "Alpha")
    canvas_dir = _project_dir(plot_root, "alpha") / "foundation"
    slug_dir = canvas_dir / "published" / "mission" / "our-mission"
    slug_dir.mkdir(parents=True, exist_ok=True)

    # nodes not a list → early return, slug folder untouched.
    _migrate_published_slug_to_id(canvas_dir, {"nodes": "nope"})
    assert slug_dir.is_dir()

    # non-dict entry + a node with non-string id + a node with non-string
    # label are all skipped; the slug folder is never renamed.
    raw = {
        "nodes": [
            "junk",
            {"kind": "mission", "id": 5, "label": "Our Mission"},  # id not str
            {"kind": "mission", "id": "m1", "label": 99},  # label not str
        ]
    }
    _migrate_published_slug_to_id(canvas_dir, raw)
    assert slug_dir.is_dir(), "all entries skipped → slug folder survives"
    assert not (canvas_dir / "published" / "mission" / "m1").exists()


# ---------------------------------------------------------------------------
# _migrate_parent_id_to_directed_edges (D-2026-05-25-A)
# ---------------------------------------------------------------------------


def test_parent_id_becomes_directed_edge(plot_root: Path) -> None:
    """A node with ``parent_id`` loses the field and gains a directed edge
    parent → child (stable id ``e_migrated_<child>``), persisted to disk."""
    create_project(plot_root, "alpha", "Alpha")
    raw = {
        "canvas_id": "actors",
        "canvas_kind": "actors",
        "nodes": [
            {"id": "p", "kind": "actor", "label": "Parent"},
            {"id": "c", "kind": "actor", "label": "Child", "parent_id": "p"},
        ],
        "edges": [],
    }
    out = _migrate_parent_id_to_directed_edges(plot_root, "alpha", "actors", None, raw)

    child = next(n for n in out["nodes"] if n["id"] == "c")
    assert "parent_id" not in child, "parent_id stripped from the node"
    edge = next(e for e in out["edges"] if e["id"] == "e_migrated_c")
    assert (edge["source"], edge["target"]) == ("p", "c")
    assert edge["directed"] is True
    # persisted: re-reading the raw file shows the migrated shape.
    on_disk = json.loads(_canvas_file(plot_root, "alpha", "actors").read_text("utf-8"))
    assert any(e["id"] == "e_migrated_c" for e in on_disk["edges"])


def test_parent_id_skips_self_parent_and_existing_edge(plot_root: Path) -> None:
    """No edge is created when parent_id == own id, nor when an equivalent
    directed edge already exists; the field is still dropped."""
    create_project(plot_root, "alpha", "Alpha")
    raw = {
        "canvas_id": "actors",
        "canvas_kind": "actors",
        "nodes": [
            {"id": "p", "kind": "actor", "label": "P"},
            {"id": "c", "kind": "actor", "label": "C", "parent_id": "p"},
            {"id": "self", "kind": "actor", "label": "S", "parent_id": "self"},
        ],
        # an equivalent p -> c edge already present.
        "edges": [{"id": "pre", "source": "p", "target": "c", "directed": True}],
    }
    out = _migrate_parent_id_to_directed_edges(plot_root, "alpha", "actors", None, raw)

    assert not any(e["id"] == "e_migrated_c" for e in out["edges"]), (
        "existing equivalent edge → no duplicate migrated edge"
    )
    assert not any(e["id"] == "e_migrated_self" for e in out["edges"]), "self-parent → no edge"
    assert all("parent_id" not in n for n in out["nodes"])


def test_parent_id_backfills_directed_field_on_legacy_edges(plot_root: Path) -> None:
    """An edge lacking ``directed`` is rewritten with directed=True even when
    no parent_id migration happens (the new default)."""
    create_project(plot_root, "alpha", "Alpha")
    raw = {
        "canvas_id": "actors",
        "canvas_kind": "actors",
        "nodes": [
            {"id": "a", "kind": "actor", "label": "A"},
            {"id": "b", "kind": "actor", "label": "B"},
        ],
        "edges": [{"id": "e1", "source": "a", "target": "b"}],  # no 'directed'
    }
    out = _migrate_parent_id_to_directed_edges(plot_root, "alpha", "actors", None, raw)
    assert out["edges"][0]["directed"] is True


def test_parent_id_noop_returns_same_object(plot_root: Path) -> None:
    """No parent_id anywhere and every edge already carries ``directed`` →
    the function returns the raw object unchanged (no rewrite/persist)."""
    create_project(plot_root, "alpha", "Alpha")
    raw = {
        "canvas_id": "actors",
        "canvas_kind": "actors",
        "nodes": [{"id": "a", "kind": "actor", "label": "A"}],
        "edges": [{"id": "e1", "source": "a", "target": "a", "directed": True}],
    }
    out = _migrate_parent_id_to_directed_edges(plot_root, "alpha", "actors", None, raw)
    assert out is raw, "nothing changed → original object returned"


# ---------------------------------------------------------------------------
# _migrate_assign_edge_relation (D-2026-05-31-C)
# ---------------------------------------------------------------------------


def test_assign_edge_relation_keeps_existing_and_assigns_missing(plot_root: Path) -> None:
    """An edge that already has ``relation`` is preserved verbatim; an edge
    without it gets classify_edge(canvas, source-kind). On the foundation
    canvas a ``mission`` source resolves to ``injection``."""
    create_project(plot_root, "alpha", "Alpha")
    raw = {
        "canvas_id": "foundation",
        "canvas_kind": "foundation",
        "nodes": [
            {"id": "m", "kind": "mission", "label": "M"},
            {"id": "x", "kind": "identity", "label": "X"},
        ],
        "edges": [
            {"id": "kept", "source": "m", "target": "x", "relation": "flow"},
            {"id": "new", "source": "m", "target": "x"},  # missing relation
        ],
    }
    out = _migrate_assign_edge_relation(plot_root, "alpha", "foundation", None, raw)
    by_id = {e["id"]: e for e in out["edges"]}
    assert by_id["kept"]["relation"] == "flow", "existing relation untouched"
    assert by_id["new"]["relation"] == "injection", "mission source → injection"


def test_assign_edge_relation_noop_when_all_present(plot_root: Path) -> None:
    """When every edge already has a ``relation`` the function returns raw
    unchanged (the early all() guard fires)."""
    create_project(plot_root, "alpha", "Alpha")
    raw = {
        "canvas_id": "foundation",
        "canvas_kind": "foundation",
        "nodes": [{"id": "m", "kind": "mission", "label": "M"}],
        "edges": [{"id": "e", "source": "m", "target": "m", "relation": "flow"}],
    }
    out = _migrate_assign_edge_relation(plot_root, "alpha", "foundation", None, raw)
    assert out is raw


def test_assign_edge_relation_unknown_source_falls_through_to_flow(plot_root: Path) -> None:
    """An edge whose source is not a node in the canvas (e.g. the synthetic
    project anchor) resolves source_kind=None → classify_edge → ``flow`` on a
    non-actors canvas."""
    create_project(plot_root, "alpha", "Alpha")
    raw = {
        "canvas_id": "foundation",
        "canvas_kind": "foundation",
        "nodes": [{"id": "m", "kind": "mission", "label": "M"}],
        "edges": [{"id": "e", "source": "__project_anchor__", "target": "m"}],
    }
    out = _migrate_assign_edge_relation(plot_root, "alpha", "foundation", None, raw)
    assert out["edges"][0]["relation"] == "flow"


# ---------------------------------------------------------------------------
# _drop_disallowed_services_kinds (v0.11.5)
# ---------------------------------------------------------------------------


def test_drop_disallowed_services_kinds_removes_only_disallowed(plot_root: Path) -> None:
    """Nodes whose kind is outside the live services allow-list are dropped;
    allowed kinds and kind-less nodes survive. Result is persisted."""
    create_project(plot_root, "alpha", "Alpha")
    raw = {
        "canvas_id": "services",
        "canvas_kind": "services",
        "nodes": [
            {"id": "svc", "kind": "service", "label": "S"},  # allowed
            {"id": "cat", "kind": "category", "label": "C"},  # allowed
            {"id": "mr", "kind": "mission_ref", "label": "M"},  # disallowed
            {"id": "none", "kind": None, "label": "N"},  # kept (kind is None)
        ],
        "edges": [],
    }
    out = _drop_disallowed_services_kinds(plot_root, "alpha", raw)
    kept_ids = {n["id"] for n in out["nodes"]}
    assert kept_ids == {"svc", "cat", "none"}, "only mission_ref dropped"
    on_disk = json.loads(_canvas_file(plot_root, "alpha", "services").read_text("utf-8"))
    assert {n["id"] for n in on_disk["nodes"]} == {"svc", "cat", "none"}


def test_drop_disallowed_services_kinds_noop_when_all_allowed(plot_root: Path) -> None:
    """All-allowed input → raw returned unchanged (no rewrite)."""
    create_project(plot_root, "alpha", "Alpha")
    raw = {
        "canvas_id": "services",
        "canvas_kind": "services",
        "nodes": [{"id": "svc", "kind": "service", "label": "S"}],
        "edges": [],
    }
    out = _drop_disallowed_services_kinds(plot_root, "alpha", raw)
    assert out is raw


# ---------------------------------------------------------------------------
# _absorb_md_typed_text_into_json — non-MD kind skip branch
# ---------------------------------------------------------------------------


def test_absorb_md_skips_non_foundation_md_kind(plot_root: Path) -> None:
    """A node whose kind has no FOUNDATION_MD_FIELDS entry (e.g. ``actor``)
    passes through untouched — no MD lookup, no details_path clearing."""
    create_project(plot_root, "alpha", "Alpha")
    raw = {
        "canvas_id": "foundation",
        "canvas_kind": "foundation",
        "nodes": [{"id": "a", "kind": "actor", "label": "A", "details_path": "x.md"}],
        "edges": [],
    }
    out = _absorb_md_typed_text_into_json(plot_root, "alpha", raw)
    assert out is raw, "no foundation-MD node present → untouched object"
    assert out["nodes"][0]["details_path"] == "x.md", "non-MD kind keeps details_path"


def test_absorb_md_happy_path_absorbs_fields_and_quarantines(plot_root: Path) -> None:
    """JSON empty + MD populated → typed field + body absorbed verbatim,
    details_path cleared, source MD moved to ``foundation/_legacy/``."""
    create_project(plot_root, "alpha", "Alpha")
    label = "Mission"
    md_path = _foundation_md_path(plot_root, "alpha", "mission", "m", label)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(
        "# Mission\n\n## Mission\nWe **help** users.\n\n---\nFree prose here.",
        encoding="utf-8",
    )
    raw = {
        "canvas_id": "foundation",
        "canvas_kind": "foundation",
        "nodes": [{"id": "m", "kind": "mission", "label": label, "details_path": "stale.md"}],
        "edges": [],
    }
    out = _absorb_md_typed_text_into_json(plot_root, "alpha", raw)
    mission = out["nodes"][0]
    assert mission["statement"] == "We **help** users."
    assert mission["body"] == "Free prose here.\n"  # parser appends trailing \n
    assert mission["details_path"] is None
    assert not md_path.exists(), "source MD moved out of the canonical path"
    assert (_legacy_md_dir(plot_root, "alpha") / md_path.name).exists()


def test_absorb_md_clears_details_path_when_no_md(plot_root: Path) -> None:
    """No source MD on disk but the node carries a stale ``details_path`` →
    it is cleared to None (the v0.17 invariant) and the node marked changed
    (lines 348-352)."""
    create_project(plot_root, "alpha", "Alpha")
    raw = {
        "canvas_id": "foundation",
        "canvas_kind": "foundation",
        "nodes": [{"id": "m", "kind": "mission", "label": "M", "details_path": "old.md"}],
        "edges": [],
    }
    out = _absorb_md_typed_text_into_json(plot_root, "alpha", raw)
    assert out["nodes"][0]["details_path"] is None


def test_absorb_md_clean_passthrough_when_no_md_and_no_details_path(
    plot_root: Path,
) -> None:
    """A foundation-MD-kind node with no source MD and no ``details_path`` is
    passed through untouched and the doc is left unchanged (lines 353-354)."""
    create_project(plot_root, "alpha", "Alpha")
    raw = {
        "canvas_id": "foundation",
        "canvas_kind": "foundation",
        "nodes": [{"id": "m", "kind": "mission", "label": "M"}],  # no details_path
        "edges": [],
    }
    out = _absorb_md_typed_text_into_json(plot_root, "alpha", raw)
    assert out is raw, "nothing to absorb or clear → original object returned"


def test_published_slug_to_id_noop_without_published_dir(plot_root: Path) -> None:
    """No ``published/`` dir at all → early return, nothing created
    (line 104-105 guard)."""
    create_project(plot_root, "alpha", "Alpha")
    canvas_dir = _project_dir(plot_root, "alpha") / "foundation"
    raw = {"nodes": [{"kind": "mission", "id": "m1", "label": "Our Mission"}]}
    _migrate_published_slug_to_id(canvas_dir, raw)  # must not raise
    assert not (canvas_dir / "published").exists()


def test_absorb_md_collision_give_up_leaves_source_on_disk(plot_root: Path) -> None:
    """When BOTH the base legacy name AND the short-id-suffixed name are
    already taken, the migrator gives up moving the source MD (no data
    loss): the source file stays, the node is still marked changed."""
    create_project(plot_root, "alpha", "Alpha")
    label = "Mission"
    node_id = "m_abcdefgh"
    # Source MD at the canonical path.
    md_path = _foundation_md_path(plot_root, "alpha", "mission", node_id, label)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text("# Mission\n\n## Mission\nstatement text\n", encoding="utf-8")

    # Pre-occupy BOTH legacy destinations so rename gives up.
    legacy = _legacy_md_dir(plot_root, "alpha")
    legacy.mkdir(parents=True, exist_ok=True)
    base_dest = legacy / md_path.name
    base_dest.write_text("occupied base", encoding="utf-8")
    short_id = node_id[:8]
    suffixed_dest = legacy / f"{md_path.stem}-{short_id}.md"
    suffixed_dest.write_text("occupied suffixed", encoding="utf-8")

    raw = {
        "canvas_id": "foundation",
        "canvas_kind": "foundation",
        "nodes": [{"id": node_id, "kind": "mission", "label": label}],
        "edges": [],
    }
    out = _absorb_md_typed_text_into_json(plot_root, "alpha", raw)

    assert md_path.exists(), "two collisions → source MD left on disk (no data loss)"
    # The field absorption still happened (changed=True path).
    mission = out["nodes"][0]
    assert mission["statement"] == "statement text"
    # Pre-existing legacy files are untouched.
    assert base_dest.read_text(encoding="utf-8") == "occupied base"
    assert suffixed_dest.read_text(encoding="utf-8") == "occupied suffixed"


# ---------------------------------------------------------------------------
# _evict_legacy_project_anchor — FileNotFoundError (no project doc) branch
# ---------------------------------------------------------------------------


def test_evict_legacy_anchor_drops_node_when_project_doc_missing(plot_root: Path) -> None:
    """A legacy ``kind=project`` node with NO project.json on disk → the
    node is dropped (so the canvas validates) and the result persisted,
    rather than raising."""
    # Deliberately do NOT create_project — there is no project.json.
    canvas_dir = _project_dir(plot_root, "ghost") / "foundation"
    canvas_dir.mkdir(parents=True, exist_ok=True)
    raw = {
        "canvas_id": "foundation",
        "canvas_kind": "foundation",
        "nodes": [
            {"id": "__project_anchor__", "kind": "project", "label": "P", "x": 1.0},
            {"id": "m", "kind": "mission", "label": "M"},
        ],
        "edges": [],
    }
    out = _evict_legacy_project_anchor(plot_root, "ghost", "foundation", raw)
    kinds = [n["kind"] for n in out["nodes"]]
    assert "project" not in kinds, "legacy project node dropped"
    assert "mission" in kinds, "other nodes survive"
    on_disk = json.loads(_canvas_file(plot_root, "ghost", "foundation").read_text("utf-8"))
    assert not any(n["kind"] == "project" for n in on_disk["nodes"])


def test_evict_legacy_anchor_strips_orphan_non_anchor_edges(plot_root: Path) -> None:
    """No legacy ``project`` node, but an edge points at a vanished id → the
    orphan edge is stripped and persisted. Edges touching the synthetic
    anchor (``__project_anchor__``) are whitelisted and survive — the
    v0.16.38 (D-2026-05-13-N) storm fix (lines 436-446)."""
    create_project(plot_root, "alpha", "Alpha")
    raw = {
        "canvas_id": "actors",
        "canvas_kind": "actors",
        "nodes": [{"id": "a", "kind": "actor", "label": "A"}],
        "edges": [
            {"id": "orphan", "source": "ghost", "target": "a"},  # ghost not a node
            {"id": "anchor", "source": "__project_anchor__", "target": "a"},  # whitelisted
        ],
    }
    out = _evict_legacy_project_anchor(plot_root, "alpha", "actors", raw)
    kept_ids = {e["id"] for e in out["edges"]}
    assert kept_ids == {"anchor"}, "orphan stripped, anchor edge survives"
    on_disk = json.loads(_canvas_file(plot_root, "alpha", "actors").read_text("utf-8"))
    assert {e["id"] for e in on_disk["edges"]} == {"anchor"}


def test_evict_legacy_anchor_noop_when_no_legacy_and_edges_clean(plot_root: Path) -> None:
    """No legacy project node and every edge endpoint is valid → raw is
    returned unchanged (no rewrite)."""
    create_project(plot_root, "alpha", "Alpha")
    raw = {
        "canvas_id": "actors",
        "canvas_kind": "actors",
        "nodes": [{"id": "a", "kind": "actor", "label": "A"}],
        "edges": [{"id": "e", "source": "a", "target": "a"}],
    }
    out = _evict_legacy_project_anchor(plot_root, "alpha", "actors", raw)
    assert out is raw


def test_collect_foundation_md_warnings_is_empty_stub(plot_root: Path) -> None:
    """v0.17 Phase 1: JSON is the sole SSOT for typed text, so the MD-warning
    callable is a stable empty-dict stub (backward-compatible response shape)."""
    from mashbill.folder_io import read_canvas

    create_project(plot_root, "alpha", "Alpha")
    canvas = read_canvas(plot_root, "alpha", "foundation")
    assert collect_foundation_md_warnings(plot_root, "alpha", canvas) == {}


def test_evict_legacy_anchor_migrates_position_into_project_doc(plot_root: Path) -> None:
    """With a real project.json present, the legacy project node's geometry
    is copied into ProjectDoc.anchors[canvas] and the node + its edges are
    removed from the canvas."""
    create_project(plot_root, "alpha", "Alpha")
    raw = {
        "canvas_id": "actors",
        "canvas_kind": "actors",
        "nodes": [
            {
                "id": "__project_anchor__",
                "kind": "project",
                "label": "P",
                "x": 12.0,
                "y": 34.0,
                "width": 200.0,
                "height": 210.0,
                "color": "#abcdef",
                "shape": "circle",
            },
            {"id": "a", "kind": "actor", "label": "A"},
        ],
        "edges": [
            {"id": "e", "source": "__project_anchor__", "target": "a"},  # references anchor
        ],
    }
    out = _evict_legacy_project_anchor(plot_root, "alpha", "actors", raw)

    assert all(n["kind"] != "project" for n in out["nodes"]), "anchor node evicted"
    assert out["edges"] == [], "edge referencing the evicted anchor stripped"

    proj = read_project(plot_root, "alpha")
    anchor = proj.anchors["actors"]
    assert (anchor.x, anchor.y) == (12.0, 34.0)
    assert (anchor.width, anchor.height) == (200.0, 210.0)
    assert anchor.color == "#abcdef"
