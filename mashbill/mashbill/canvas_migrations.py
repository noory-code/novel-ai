"""Read-path canvas healing: lazy migrations + foundation MD absorb + legacy anchor eviction.

Split out of the folder_io god-module (D-2026-06-10-D). folder_io.py re-exports
everything, so import sites and tests are unchanged.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from mashbill.edge_semantics import classify_edge
from mashbill.models import (
    CanvasDoc,
    CanvasKind,
)
from mashbill.storage import (  # noqa: F401
    _canvas_file,
    _ensure_project,
    _project_dir,
    _project_file,
    _read_json,
    _write_json,
    read_project,
    write_project,
)

_LEGACY_PUBLISHED_FILENAME_RE = re.compile(r"^(?P<kind>[a-z_]+)-(?P<slug>.+)-v(?P<v>\d+\.\d+)\.md$")


def _migrate_actor_isroot_to_false(raw: dict[str, Any]) -> dict[str, Any]:
    """v0.24.11 (D-2026-05-19-D) — reset legacy actor ``is_root=True``
    to False. Idempotent (no-op after first read).

    Background: pre-v0.24.11, ``actor.is_root`` was retained as a
    cross-canvas master marker (per SPEC.md). The user pinned 2026-05-19
    that every actor is a Symbol candidate (referenceable from the
    Service canvas via ``actor_ref``), so the boolean distinguishes
    nothing. Actor.is_root is now deprecated; service.is_root remains
    (FeatureDetail anchor marker).
    """
    nodes = raw.get("nodes")
    if not isinstance(nodes, list):
        return raw
    for node in nodes:
        if not isinstance(node, dict):
            continue
        if node.get("kind") == "actor" and node.get("is_root") is True:
            node["is_root"] = False
    return raw


def _migrate_published_flat_to_kind_slug(canvas_dir: Path) -> None:
    """Move legacy flat published files into the new kind/slug/version layout.

    Idempotent: looks only at direct ``.md`` children of
    ``<canvas_dir>/published/``. Once moved, no files match the regex
    there so subsequent calls are no-ops. Existing destinations are
    skipped (the new layout takes precedence — we never overwrite).
    """
    published_dir = canvas_dir / "published"
    if not published_dir.is_dir():
        return
    for entry in published_dir.iterdir():
        if not entry.is_file() or entry.suffix != ".md":
            continue
        match = _LEGACY_PUBLISHED_FILENAME_RE.match(entry.name)
        if not match:
            continue
        kind = match.group("kind")
        slug = match.group("slug")
        version = match.group("v")
        dest = published_dir / kind / slug / f"v{version}.md"
        if dest.exists():
            # New layout already has this version; the legacy file is
            # redundant. Leave it in place rather than silently delete
            # — caller can clean up after auditing.
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        entry.rename(dest)


# v0.24.3 (D-2026-05-18-A) — published slug-folder → id-folder migration.
# Pre-v0.24.3 layout used ``slugify(label)`` as the folder name, which
# could be Korean / CJK. v0.24.3 switches to node id (ASCII per Novel's
# id policy) for clean, rename-stable folder names. Idempotent —
# once renamed, the slug folder no longer exists so subsequent reads
# are no-ops.


def _migrate_published_slug_to_id(canvas_dir: Path, raw_canvas: dict[str, Any]) -> None:
    """Rename ``<canvas>/published/<kind>/<slug>/`` folders to
    ``<canvas>/published/<kind>/<node_id>/`` for every node whose
    id and label appear in the raw canvas. Nodes whose id already
    equals their slug (e.g. id="mission" + label="Mission") are
    a no-op rename. Missing slug folders are silently skipped.
    Conflicts (id folder already exists) leave the slug folder in
    place so the user can audit; we never overwrite.
    """
    from mashbill.slug import slugify

    published_dir = canvas_dir / "published"
    if not published_dir.is_dir():
        return
    nodes = raw_canvas.get("nodes")
    if not isinstance(nodes, list):
        return
    for node in nodes:
        if not isinstance(node, dict):
            continue
        kind = node.get("kind")
        node_id = node.get("id")
        label = node.get("label")
        if not isinstance(kind, str) or not isinstance(node_id, str):
            continue
        if not isinstance(label, str):
            continue
        slug = slugify(label) or "untitled"
        if slug == node_id:
            continue  # already at the new layout (or coincidentally identical)
        kind_dir = published_dir / kind
        if not kind_dir.is_dir():
            continue
        slug_dir = kind_dir / slug
        id_dir = kind_dir / node_id
        if not slug_dir.is_dir():
            continue
        if id_dir.exists():
            continue  # destination occupied — leave slug folder for audit
        slug_dir.rename(id_dir)


# v0.26.0 (D-2026-05-25-A) — ``_wrap_legacy_services_in_default_category``
# removed. The v0.12 "service must be nested in a category" invariant
# was enforced via ``parent_id`` (now removed). With the new directed
# edge model, services may sit at any level; the wrapper that seeded
# a fake default-category is no longer needed.


def _migrate_parent_id_to_directed_edges(
    plot_root: Path,
    project_id: str,
    canvas_kind: CanvasKind,
    service_id: str | None,
    raw: dict[str, Any],
) -> dict[str, Any]:
    """v0.26.0 (D-2026-05-25-A) — convert pre-v0.26 ``parent_id`` field
    to a directed edge from parent → child. Idempotent.

    For each node carrying a non-null ``parent_id``:
      1. Remove the ``parent_id`` key from the node dict.
      2. Append a directed edge ``parent → child`` to ``edges`` (with
         a stable id ``e_migrated_{node_id}``), unless an equivalent
         directed edge already exists.

    Also fills ``directed: True`` on any pre-v0.26 edge that lacks
    the field — that matches the new default (``SketchEdge.directed =
    True``) and preserves any explicit hierarchical intent from
    earlier sessions.

    On any actual change, persists back to disk so the file settles
    into the new model. Subsequent reads are no-ops.
    """
    nodes: list[dict[str, Any]] = list(raw.get("nodes") or [])
    edges: list[dict[str, Any]] = list(raw.get("edges") or [])

    changed = False
    existing_directed = {
        (e.get("source"), e.get("target")) for e in edges if e.get("directed", True)
    }
    rebuilt_nodes: list[dict[str, Any]] = []
    for n in nodes:
        pid = n.get("parent_id")
        if pid is None and "parent_id" not in n:
            rebuilt_nodes.append(n)
            continue
        # Drop parent_id from the node copy.
        new_node = {k: v for k, v in n.items() if k != "parent_id"}
        rebuilt_nodes.append(new_node)
        changed = True
        if pid is None or pid == n.get("id"):
            continue
        key = (pid, n.get("id"))
        if key in existing_directed:
            continue
        edges.append(
            {
                "id": f"e_migrated_{n.get('id')}",
                "source": pid,
                "target": n.get("id"),
                "sourceHandle": None,
                "targetHandle": None,
                "label": "",
                "style": "solid",
                "directed": True,
                "action_verb": None,
                "value_form": [],
            }
        )
        existing_directed.add(key)

    rebuilt_edges: list[dict[str, Any]] = []
    for e in edges:
        if "directed" not in e:
            rebuilt_edges.append({**e, "directed": True})
            changed = True
        else:
            rebuilt_edges.append(e)

    if not changed:
        return raw

    raw = {**raw, "nodes": rebuilt_nodes, "edges": rebuilt_edges}
    _write_json(_canvas_file(plot_root, project_id, canvas_kind, service_id), raw)
    return raw


def _migrate_assign_edge_relation(
    plot_root: Path,
    project_id: str,
    canvas_kind: CanvasKind,
    service_id: str | None,
    raw: dict[str, Any],
) -> dict[str, Any]:
    """v0.30.0 (D-2026-05-31-C) — assign the stored ``relation`` semantic
    to any edge that lacks it. Idempotent.

    For each edge with no ``relation`` key, set it to
    ``classify_edge(canvas_kind, <source-node kind>)``. The source kind
    is looked up from the canvas's own nodes; the synthetic project
    anchor (not in ``nodes``) resolves to ``None`` → ``classify_edge``
    handles it (flow, or inheritance on the actors canvas). On any
    actual change, persists back to disk so subsequent reads are no-ops.
    """
    edges: list[dict[str, Any]] = list(raw.get("edges") or [])
    if all("relation" in e for e in edges):
        return raw

    kind_by_id: dict[str, str] = {
        n.get("id"): n.get("kind") for n in (raw.get("nodes") or []) if n.get("id")
    }
    rebuilt_edges: list[dict[str, Any]] = []
    changed = False
    for e in edges:
        if "relation" in e:
            rebuilt_edges.append(e)
            continue
        src = e.get("source")
        source_kind = kind_by_id.get(src) if isinstance(src, str) else None
        rebuilt_edges.append({**e, "relation": classify_edge(canvas_kind, source_kind)})
        changed = True

    if not changed:
        return raw

    raw = {**raw, "edges": rebuilt_edges}
    _write_json(_canvas_file(plot_root, project_id, canvas_kind, service_id), raw)
    return raw


def _drop_disallowed_services_kinds(
    plot_root: Path,
    project_id: str,
    raw: dict[str, Any],
) -> dict[str, Any]:
    """v0.11.5 migration helper: silently drop ``mission_ref`` / ``value_ref``
    / ``identity_ref`` (and any other now-disallowed kinds) from the services
    top view. They live in ``feature`` from v0.11.5 onwards.
    Idempotent.

    v0.12 update: read the live ``_ALLOWED_KINDS_BY_CANVAS`` so future
    additions to the services-canvas allow-list don't trigger spurious
    drops here.
    """
    from mashbill.models import _ALLOWED_KINDS_BY_CANVAS

    nodes: list[dict[str, Any]] = list(raw.get("nodes") or [])
    allowed = _ALLOWED_KINDS_BY_CANVAS["services"]
    kept = [n for n in nodes if n.get("kind") in allowed or n.get("kind") is None]
    if len(kept) == len(nodes):
        return raw
    raw = {**raw, "nodes": kept}
    _write_json(_canvas_file(plot_root, project_id, "services"), raw)
    return raw


def _foundation_md_path(
    plot_root: Path, project_id: str, kind: str, node_id: str, label: str
) -> Path:
    """v0.13 Phase 3+6: per-node Markdown file path for a Foundation node.

    Layout: ``foundation/{kind}-{slugified-label}.md`` directly under the
    canvas folder (no per-node subfolder). The node's ``id`` is the
    stable identity; the slug derives from ``label`` and is regenerated
    on rename. We pin uniqueness by also embedding the kind so two
    differently-kinded nodes with the same label don't collide.
    """
    from mashbill.slug import slugify

    base_slug = slugify(label) if label.strip() else node_id
    return _project_dir(plot_root, project_id) / "foundation" / f"{kind}-{base_slug}.md"


def _legacy_md_dir(plot_root: Path, project_id: str) -> Path:
    return _project_dir(plot_root, project_id) / "foundation" / "_legacy"


def _absorb_md_typed_text_into_json(
    plot_root: Path, project_id: str, raw: dict[str, Any]
) -> dict[str, Any]:
    """v0.17 Phase 1 one-shot read-side migrator (D-2026-05-16-A).

    For each Foundation node of a typed-text kind (mission / core_value /
    identity), absorb the H2 typed sections + post-``---`` free prose
    from ``foundation/{kind}-{slug}.md`` into the JSON node (typed fields
    + new ``body`` field, all as MD-formatted strings), clear
    ``details_path`` to ``None``, and quarantine the source MD file to
    ``foundation/_legacy/{kind}-{slug}.md``.

    Conflict policy (4 scenarios):
      - JSON empty,   MD populated → MD wins; absorb.
      - JSON populated, MD missing → no-op for fields (JSON already SSoT).
      - Both populated              → JSON wins (latest); MD still quarantined.
      - Both empty                  → no-op.

    Idempotent: once the original MD path is gone, subsequent reads see
    no source file and skip. The ``_legacy/`` quarantine is never read.
    """
    from mashbill.md_template import parse_md_template
    from mashbill.models import FOUNDATION_MD_FIELDS, FOUNDATION_TYPED_TEXT_FIELDS

    nodes: list[dict[str, Any]] = list(raw.get("nodes") or [])
    changed = False
    new_nodes: list[dict[str, Any]] = []
    for n in nodes:
        kind = n.get("kind")
        if not isinstance(kind, str) or not FOUNDATION_MD_FIELDS.get(kind):
            new_nodes.append(n)
            continue
        md_path = _foundation_md_path(plot_root, project_id, kind, n["id"], n.get("label", ""))
        # No source MD → no field absorption + no quarantine move. But
        # Foundation typed-text kinds carry no ``details_path`` in v0.17+
        # (invariant per D-2026-05-16-A: JSON is SSOT for these kinds;
        # the viewer's MD-editor surface is gone). Clear unconditionally
        # if set; idempotent when already cleared.
        if not md_path.exists():
            if n.get("details_path") is not None:
                cleaned = {**n, "details_path": None}
                changed = True
                new_nodes.append(cleaned)
                continue
            new_nodes.append(n)
            continue
        parsed = parse_md_template(md_path.read_text(encoding="utf-8"), kind)
        merged = {**n}
        # Typed H2 fields: JSON value wins when present, else absorb MD.
        for field in FOUNDATION_TYPED_TEXT_FIELDS.get(kind, []):
            json_val = str(merged.get(field) or "")
            md_val = parsed.typed_fields.get(field, "")
            if not json_val.strip() and md_val.strip():
                merged[field] = md_val
        # body ← MD's post-``---`` free prose (same conflict policy).
        json_body = str(merged.get("body") or "")
        if not json_body.strip() and parsed.free_prose.strip():
            merged["body"] = parsed.free_prose
        # Foundation typed-text kinds carry no details_path in v0.17+.
        merged["details_path"] = None
        # Quarantine the source MD file. ``Path.rename`` is atomic within
        # the same filesystem; if the destination already exists (e.g.
        # duplicate slug across nodes), append the node-id short suffix
        # and try once more; if still colliding, leave the source in
        # place and continue (no data loss, just deferred cleanup).
        legacy_dir = _legacy_md_dir(plot_root, project_id)
        legacy_dir.mkdir(parents=True, exist_ok=True)
        dest = legacy_dir / md_path.name
        if dest.exists():
            short_id = str(n.get("id", ""))[:8] or "x"
            dest = legacy_dir / f"{md_path.stem}-{short_id}.md"
        if dest.exists():
            # Two collisions — give up moving (rare; leave on disk).
            new_nodes.append(merged)
            changed = True
            continue
        md_path.rename(dest)
        new_nodes.append(merged)
        changed = True
    if changed:
        raw = {**raw, "nodes": new_nodes}
        _write_json(_canvas_file(plot_root, project_id, "foundation"), raw)
    return raw


def collect_foundation_md_warnings(
    plot_root: Path, project_id: str, canvas: CanvasDoc
) -> dict[str, list[str]]:
    """v0.17 Phase 1 (D-2026-05-16-A): JSON is the sole SSOT for
    Foundation typed-text fields. The pre-v0.17 MD-template parser
    warnings are no longer surfaced because there are no MD files left
    at the canonical path after ``_absorb_md_typed_text_into_json``
    runs. Kept as a stable callable so the API response shape stays
    backward-compatible; Phase 6 will drop the call site entirely.
    """
    return {}


def _evict_legacy_project_anchor(
    plot_root: Path,
    project_id: str,
    canvas_kind: CanvasKind,
    raw: dict[str, Any],
) -> dict[str, Any]:
    """v0.13 Phase 0 migration helper: project anchor is now in
    ``ProjectDoc.anchors``. If an old canvas .json still carries a
    ``project`` kind node, copy its position/visual into ProjectDoc.anchors
    and remove the node. Idempotent — does nothing once cleaned up.
    """
    from mashbill.models import AnchorPlacement

    nodes: list[dict[str, Any]] = list(raw.get("nodes") or [])
    legacy_anchors = [n for n in nodes if n.get("kind") == "project"]
    if not legacy_anchors:
        # Defensive: an earlier eviction (without the edge cleanup that
        # landed in v0.13.0) may have left orphan edges referencing the
        # removed project node. Strip them now if any are still pointing
        # at a vanished id.
        #
        # v0.16.38 (D-2026-05-13-N) — the synthetic project anchor
        # ``PROJECT_ANCHOR_ID`` is a valid edge endpoint per
        # D-2026-05-04-B SPEC mandate even though it doesn't live in
        # ``nodes``. Whitelist it here so user-drawn anchor edges
        # aren't strip-and-rewritten on every read (which triggered
        # the watcher → broadcast → refetch loop reported by the
        # user on 2026-05-13 as *"새로고침을 하다보면 캔버스에 노드들이
        # 사라지는 이슈"*).
        from mashbill.models import PROJECT_ANCHOR_ID

        node_ids = {n.get("id") for n in nodes} | {PROJECT_ANCHOR_ID}
        edges: list[dict[str, Any]] = list(raw.get("edges") or [])
        kept_edges = [
            e for e in edges if e.get("source") in node_ids and e.get("target") in node_ids
        ]
        if len(kept_edges) != len(edges):
            raw = {**raw, "edges": kept_edges}
            _write_json(_canvas_file(plot_root, project_id, canvas_kind), raw)
        return raw
    try:
        proj = read_project(plot_root, project_id)
    except FileNotFoundError:
        # No project doc → can't migrate; just drop the node so the canvas
        # validates. Position is unrecoverable but defaults are sensible.
        kept = [n for n in nodes if n.get("kind") != "project"]
        raw = {**raw, "nodes": kept}
        _write_json(_canvas_file(plot_root, project_id, canvas_kind), raw)
        return raw
    legacy = legacy_anchors[0]
    anchor = AnchorPlacement(
        x=float(legacy.get("x", -75.0)),
        y=float(legacy.get("y", -75.0)),
        width=float(legacy.get("width", 150.0)),
        height=float(legacy.get("height", 150.0)),
        color=str(legacy.get("color", "#fef3c7")),
        shape=legacy.get("shape", "circle"),
    )
    new_anchors = {**proj.anchors, canvas_kind: anchor}
    proj = proj.model_copy(update={"anchors": new_anchors})
    write_project(plot_root, proj)
    evicted_ids = {n.get("id") for n in legacy_anchors}
    kept = [n for n in nodes if n.get("kind") != "project"]
    # v0.13 Phase 0: also drop any edges that referenced the evicted project
    # node — otherwise CanvasDoc validator fails with "edges reference
    # unknown nodes".
    all_edges: list[dict[str, Any]] = list(raw.get("edges") or [])
    kept_edges = [
        e
        for e in all_edges
        if e.get("source") not in evicted_ids and e.get("target") not in evicted_ids
    ]
    raw = {**raw, "nodes": kept, "edges": kept_edges}
    _write_json(_canvas_file(plot_root, project_id, canvas_kind), raw)
    return raw


