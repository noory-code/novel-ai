"""Canvas read/write + feature listing.

Split out of the folder_io god-module (D-2026-06-10-D). folder_io.py re-exports
everything, so import sites and tests are unchanged.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import ValidationError

from mashbill.canvas_migrations import (  # noqa: F401
    _LEGACY_PUBLISHED_FILENAME_RE,
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
from mashbill.models import (
    _ALLOWED_KINDS_BY_CANVAS,
    CanvasDoc,
    CanvasKind,
)
from mashbill.models_foundation import PROJECT_ANCHOR_ID
from mashbill.models_union import SketchNode, SketchNodeAdapter
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

# ---------------------------------------------------------------------------
# canvas-level IO
# ---------------------------------------------------------------------------

# Kinds removed from the palette (D-2026-06-19-G…J / D-2026-06-20-*). A node of
# a retired kind in an older canvas.json would fail ``CanvasDoc.model_validate``
# (its discriminant is gone from the union), so ``_drop_retired_kinds`` strips
# it (and any edge incident to it) on read — loss-free for surviving content
# (retiring ``group`` drops only the container, never its member step/decision
# nodes). Lives here (not canvas_migrations.py, which is at its 500-line
# ceiling) as a read-path helper tightly bound to ``read_canvas``. The set
# grows as each kind is retired.
RETIRED_KINDS: frozenset[str] = frozenset(
    {"group", "mission_ref", "value_ref", "identity_ref", "metric", "content"}
)


def _drop_retired_kinds(
    plot_root: Path,
    project_id: str,
    canvas_kind: CanvasKind,
    service_id: str | None,
    raw: dict[str, Any],
) -> dict[str, Any]:
    """Drop nodes whose ``kind`` was retired, plus any edge incident to a
    dropped node, so a project authored before the retirement keeps loading.
    Idempotent; persists the healed canvas on first read."""
    nodes: list[dict[str, Any]] = list(raw.get("nodes") or [])
    retired_ids = {n.get("id") for n in nodes if n.get("kind") in RETIRED_KINDS}
    if not retired_ids:
        return raw
    kept_nodes = [n for n in nodes if n.get("kind") not in RETIRED_KINDS]
    edges: list[dict[str, Any]] = list(raw.get("edges") or [])
    kept_edges = [
        e
        for e in edges
        if e.get("source") not in retired_ids and e.get("target") not in retired_ids
    ]
    raw = {**raw, "nodes": kept_nodes, "edges": kept_edges}
    _write_json(_canvas_file(plot_root, project_id, canvas_kind, service_id), raw)
    return raw


def _drop_dangling_edges(
    plot_root: Path,
    project_id: str,
    canvas_kind: CanvasKind,
    service_id: str | None,
    raw: dict[str, Any],
) -> dict[str, Any]:
    """Drop edges whose source or target node is absent, so a canvas.json
    corrupted on disk (a node removed without its incident edges) loads instead
    of 400'ing on GET (``CanvasDoc`` hard-rejects ``edges reference unknown
    nodes``). The synthetic project anchor (``PROJECT_ANCHOR_ID``) lives in
    ``ProjectDoc.anchors``, not ``nodes``, but is a valid endpoint
    (D-2026-05-04-B), so an edge to it is kept. The *write* path still rejects
    dangling edges — the viewer prunes before save (D-2026-06-21-R); this heals
    only already-persisted corruption. Idempotent; persists the healed canvas on
    first read. (D-2026-06-21-X)"""
    node_ids = {n.get("id") for n in (raw.get("nodes") or [])} | {PROJECT_ANCHOR_ID}
    edges: list[dict[str, Any]] = list(raw.get("edges") or [])
    kept = [e for e in edges if e.get("source") in node_ids and e.get("target") in node_ids]
    if len(kept) == len(edges):
        return raw
    raw = {**raw, "edges": kept}
    _write_json(_canvas_file(plot_root, project_id, canvas_kind, service_id), raw)
    return raw


def read_canvas(
    plot_root: Path,
    project_id: str,
    canvas_kind: CanvasKind,
    service_id: str | None = None,
) -> CanvasDoc:
    _ensure_project(plot_root, project_id)
    if canvas_kind == "foundation":
        # Heal Foundation canvases written under pre-v0.10 schemas (legacy
        # ``core`` canvas folder + ``core``/``identity_facet`` node kinds +
        # missing Project anchor) before Pydantic sees the raw dict.
        # Imported here to keep migrate.py optional on the hot path for
        # non-foundation kinds.
        from mashbill.migrate import upgrade_foundation_canvas_if_needed

        upgrade_foundation_canvas_if_needed(plot_root, project_id)
    path = _canvas_file(plot_root, project_id, canvas_kind, service_id)
    raw = _read_json(path)
    # v0.13 Phase 0 — project anchor moved to ``ProjectDoc.anchors``. If an
    # old canvas still carries a ``project`` kind node, evict it: copy its
    # position/visual to ProjectDoc.anchors[canvas] and remove from nodes.
    if canvas_kind in ("foundation", "actors", "services", "entities"):
        raw = _evict_legacy_project_anchor(plot_root, project_id, canvas_kind, raw)
    # v0.24.11 (D-2026-05-19-D) — actor.is_root semantic deprecated; reset
    # any pre-v0.24.11 ``is_root=true`` on actor nodes to False on first
    # read. Service.is_root is preserved (still meaningful as the
    # FeatureDetail anchor marker). See [[project_plot_symbol_concept]].
    if canvas_kind == "actors":
        raw = _migrate_actor_isroot_to_false(raw)
    # v0.17 Phase 1 (D-2026-05-16-A) — JSON is the single SSOT for
    # Foundation typed-text fields. On first read of any pre-v0.17
    # project, absorb the typed H2 sections + post-``---`` body from
    # ``foundation/{kind}-{slug}.md`` into the JSON node, clear
    # ``details_path``, and quarantine the source MD file to
    # ``foundation/_legacy/``. Subsequent reads are no-ops (the
    # original path no longer exists).
    if canvas_kind == "foundation":
        raw = _absorb_md_typed_text_into_json(plot_root, project_id, raw)
    # v0.11.5 — services canvas no longer accepts Foundation refs (they
    # moved to feature). Drop any stale ones from older projects so
    # the canvas validates on open. Same idempotent pattern.
    if canvas_kind == "services":
        raw = _drop_disallowed_services_kinds(plot_root, project_id, raw)
    # v0.26.0 (D-2026-05-25-A) — convert pre-v0.26 ``parent_id`` field
    # to a directed edge from parent → child. Idempotent. Persists
    # back to disk on first read so the file format settles into the
    # new model without needing a write-side trigger.
    raw = _migrate_parent_id_to_directed_edges(plot_root, project_id, canvas_kind, service_id, raw)
    # v0.30.0 (D-2026-05-31-C) — assign the stored ``relation`` semantic
    # to any pre-v0.30 edge that lacks it, via classify_edge(canvas,
    # source-node kind). Idempotent; persists on first read.
    raw = _migrate_assign_edge_relation(plot_root, project_id, canvas_kind, service_id, raw)
    # v0.23.0 (D-2026-05-17-I) — migrate legacy flat published MD layout
    # (<canvas>/published/<kind>-<slug>-v<X>.md) to the kind/slug/version.md
    # hierarchy. Idempotent.
    canvas_dir = _canvas_file(plot_root, project_id, canvas_kind, service_id).parent
    _migrate_published_flat_to_kind_slug(canvas_dir)
    # v0.24.3 (D-2026-05-18-A) — migrate slug-folder layout to id-folder.
    # Reads node id↔label from the raw canvas so we can compute the
    # old slug folder name and rename it to the node id.
    _migrate_published_slug_to_id(canvas_dir, raw)
    # 2026-06-20 (D-2026-06-19-H …) — drop nodes of retired kinds (e.g. group)
    # + their incident edges so projects authored before a kind's retirement
    # still validate. Loss-free for surviving content. Applies to every canvas.
    raw = _drop_retired_kinds(plot_root, project_id, canvas_kind, service_id, raw)
    # D-2026-06-21-X — drop edges whose endpoint node is absent (corrupted on
    # disk) so the canvas opens instead of 400'ing. Runs last so it catches a
    # dangling edge regardless of which migration above produced it. The write
    # path still rejects them (viewer prunes pre-save, D-2026-06-21-R).
    raw = _drop_dangling_edges(plot_root, project_id, canvas_kind, service_id, raw)
    return CanvasDoc.model_validate(raw)


# v0.23.0 (D-2026-05-17-I) — published MD layout migration.
# Pre-v0.23.0 layout was flat: ``<canvas>/published/<kind>-<slug>-vN.M.md``.
# v0.23.0+ layout groups by kind + slug: ``<canvas>/published/<kind>/<slug>/vN.M.md``.
# Same data, better navigation: all versions of a logical document live in
# one folder, and that folder is grouped under its kind.
def write_canvas(plot_root: Path, project_id: str, canvas: CanvasDoc) -> None:
    _ensure_project(plot_root, project_id)
    service_id = canvas.feature_ref if canvas.canvas_kind == "feature" else None
    path = _canvas_file(plot_root, project_id, canvas.canvas_kind, service_id)
    # v0.22.0 (D-2026-05-17-H) — preserve server-managed
    # ``_publish_baseline`` across PUTs. The client doesn't round-trip
    # this field (it's a server-managed dirty baseline), so a PUT from
    # the viewer would otherwise clobber it back to ``None`` and reset
    # every clean node to dirty. Read the existing on-disk canvas and
    # carry any non-None baseline forward for nodes whose incoming
    # baseline is ``None``.
    existing_baselines: dict[str, dict[str, Any]] = {}
    if path.is_file():
        try:
            existing_raw = _read_json(path)
            existing = CanvasDoc.model_validate(existing_raw)
            existing_baselines = {
                n.id: n.publish_baseline for n in existing.nodes if n.publish_baseline is not None
            }
        except (FileNotFoundError, ValueError, ValidationError):
            existing_baselines = {}
    if existing_baselines:
        preserved = [
            n.model_copy(update={"publish_baseline": existing_baselines[n.id]})
            if (n.publish_baseline is None and n.id in existing_baselines)
            else n
            for n in canvas.nodes
        ]
        canvas = canvas.model_copy(update={"nodes": preserved})
    raw = canvas.model_dump(by_alias=True)
    # v0.17 Phase 1 (D-2026-05-16-A) — JSON is the sole SSOT for
    # Foundation typed-text fields. The v0.13 ``_split_foundation_typed_
    # text_to_md`` write-side helper is gone; Pydantic now serialises
    # every field (typed + body) into the JSON output directly.
    _write_json(path, raw)
    try:
        meta = read_project(plot_root, project_id)
    except FileNotFoundError:
        return
    # v0.13 Phase 0: project label SSOT is ProjectDoc.name; no longer derived
    # from a per-canvas project node (the node is gone). Renames go through
    # ``rename_project`` directly. We just bump updated below.
    write_project(plot_root, meta)


# ---------------------------------------------------------------------------
# single-node content patch (D-2026-06-26-D)
# ---------------------------------------------------------------------------

# Per-kind *content* fields a coach may write via ``update_node`` — the kind's
# free-text prose only. This is an **allow-list, not a deny-list** (the first cut
# was `model_fields - base_fields`, which silently let every per-kind
# structural / reference / lifecycle field through as "writable" — a coach could
# repoint a service's actor references, lock an identity's derive→confirm
# lifecycle, or rewrite a rule's permission map; D-2026-06-26-D red-team). An
# allow-list is **fail-safe**: a field absent here is NOT writable, so a new kind
# (or a new structural field on an existing kind) defaults to protected until
# someone classifies it. Deliberately ABSENT and therefore protected: ``ref_*``
# id arrays + ``actor_ref.ref_actor_id`` (cross-node references — set via the
# pick-or-create flow, not free text), ``status`` / ``provenance`` (identity
# derive→confirm lifecycle), ``polarity`` / ``order`` (step structure), ``side``
# (actor classification), ``actor_permissions`` (rule permission map). ``label``
# (the node's name) is always writable, added separately. Mirrors the existing
# per-kind content maps (``FOUNDATION_TYPED_TEXT_FIELDS``). Every union kind must
# have an entry — pinned by ``tests/test_update_node.py`` so a new kind forces
# the content-vs-structural decision instead of silently leaking.
_WRITABLE_CONTENT_FIELDS: dict[str, tuple[str, ...]] = {
    "project": (),
    "mission": ("statement", "body"),
    "core_value": ("body",),  # v0.45 (D-2026-07-02-A): definition removed → name + body
    "identity": ("description", "body"),
    "actor": ("body",),
    "actor_ref": (),
    "service": ("problem", "value_created"),
    "feature": ("proposed",),
    "category": ("theme", "body"),
    "step": ("outcome", "body"),
    "decision": ("body",),
    "note": ("body",),
    "rule": ("policy", "enforcement", "body"),
    "entity": ("summary",),
}

# Always writable on every kind: the node's name / title.
_WRITABLE_LABEL = "label"


def writable_node_fields(node: SketchNode) -> list[str]:
    """The content fields a coach may patch on ``node``: ``label`` + the kind's
    free-text prose (the per-kind allow-list :data:`_WRITABLE_CONTENT_FIELDS`).

    The SSOT for "what is writable" — used both by :func:`update_node` (to filter
    a patch) and by the chat context builder (to tell the agent which fields an
    empty selected node accepts, so it can fill a blank node). Structural /
    reference / lifecycle fields are **not** writable (set through their own
    flows, never a free-text content patch — Rule 7); the allow-list is fail-safe
    for future kinds. Deterministic order: ``label`` first, then the kind's
    content fields that actually exist on the model.
    """
    content = _WRITABLE_CONTENT_FIELDS.get(node.kind, ())
    model_fields = type(node).model_fields
    return [_WRITABLE_LABEL, *(f for f in content if f in model_fields)]


def update_node(
    plot_root: Path,
    project_id: str,
    canvas_kind: CanvasKind,
    node_id: str,
    fields: dict[str, Any],
    service_id: str | None = None,
) -> dict[str, Any]:
    """Patch ONE node's content fields in place (read-modify-write).

    Reads the canvas, finds ``node_id``, merges only the writable content fields
    (see :func:`writable_node_fields`) from ``fields``, re-validates the patched
    node against its kind, then re-validates the **whole** ``CanvasDoc`` and
    writes it atomically via :func:`write_canvas` (which also preserves the
    server-managed publish baseline). Re-validating the whole doc — not just the
    one node — keeps every canvas-level invariant (unique ids, edge refs, kind
    allow-list, per-canvas minimums) honest after the patch.

    Within this read-modify-write only the target node's content changes; every
    other node and all edges are written back unchanged. It is **not** a
    transactional lock, though — like every Novel write it is last-write-wins, so a
    user edit to a *different* node landing between this read and its write is not
    merged (the window is one synchronous tool call; fine at human pace).

    Protected / unknown keys in ``fields`` are dropped and returned under
    ``rejected_fields`` (Fail-soft on a partly-valid patch, but Fail-Fast in the
    response so the caller sees a typo'd or non-writable field). Raises
    ``ValueError`` when the node is absent (this also covers the synthetic project
    anchor, which lives in ``ProjectDoc.anchors`` not ``nodes``) or when no
    writable field is supplied. A wrong field *type* raises through re-validation.

    Returns ``{"node": <updated node dict>, "rejected_fields": [...]}``.
    """
    canvas = read_canvas(plot_root, project_id, canvas_kind, service_id)
    target = next((n for n in canvas.nodes if n.id == node_id), None)
    if target is None:
        raise ValueError(
            f"node not found on {canvas_kind} canvas: {node_id!r} "
            "(the project anchor is not a node — it lives in ProjectDoc.anchors)"
        )
    allowed = set(writable_node_fields(target))
    patch = {k: v for k, v in fields.items() if k in allowed}
    rejected = sorted(set(fields) - allowed)
    if not patch:
        raise ValueError(
            f"no writable fields in patch for {target.kind} node {node_id!r}; "
            f"writable: {sorted(allowed)}, got: {sorted(fields)}"
        )
    merged = {**target.model_dump(), **patch}
    new_node = SketchNodeAdapter.validate_python(merged)
    new_nodes = [new_node if n.id == node_id else n for n in canvas.nodes]
    # model_copy does not re-run validators (pydantic v2) — round-trip through
    # model_validate so the whole-canvas invariants are enforced before the write.
    updated = CanvasDoc.model_validate(
        canvas.model_copy(update={"nodes": new_nodes}).model_dump(by_alias=True)
    )
    write_canvas(plot_root, project_id, updated)
    return {"node": new_node.model_dump(by_alias=True), "rejected_fields": rejected}


# Server-side placement for a freshly created node — a column staggered down by
# how many of its kind already exist, so successive creates don't stack on the
# anchor (generalised from the old masters.py drop zone). The user drags it after.
_FRESH_X = 160.0
_FRESH_Y0 = 120.0
_FRESH_DY = 80.0


def _compute_fresh_position(existing: list[SketchNode], kind: str) -> tuple[float, float]:
    """Where a new ``kind`` node is dropped on a canvas that already holds
    ``existing`` nodes.

    **Cluster with its own kind (D-2026-07-02-C).** Novel's essence is
    thinking-through-sight, so a new node must JOIN the visual group of its kind,
    not land at a fixed generic spot ignoring where the siblings actually sit.
    When same-kind nodes exist, left-align to that cluster and drop just below its
    lowest member (stacking the group downward). Only the first node of a kind
    (no siblings yet) uses the generic drop lane, staggered by total node count so
    distinct first-of-kind creates don't overlap. Best-effort — last-write-wins
    means two *concurrent* creates can still collide (named limit, D-2026-06-27-B)."""
    same_kind = [n for n in existing if n.kind == kind]
    if same_kind:
        x = min(n.x for n in same_kind)
        y = max(n.y for n in same_kind) + _FRESH_DY
        return x, y
    return _FRESH_X, _FRESH_Y0 + _FRESH_DY * len(existing)


def creatable_kinds(canvas_kind: str) -> set[str]:
    """The kinds :func:`create_node` may append to ``canvas_kind``.

    The canvas allow-list (:data:`_ALLOWED_KINDS_BY_CANVAS`) minus two it must
    never mint as a fresh node: ``project`` (the synthetic anchor lives in
    ``ProjectDoc.anchors``, present in some allow-lists only vestigially) and,
    on the feature canvas, ``feature`` (its root feature is bootstrapped
    exogenously — the canvas validator requires it to already exist, so a second
    feature is never appended). D-2026-06-27-B.
    """
    allowed = set(_ALLOWED_KINDS_BY_CANVAS.get(canvas_kind, set())) - {"project"}
    if canvas_kind == "feature":
        allowed -= {"feature"}
    return allowed


def create_node(
    plot_root: Path,
    project_id: str,
    canvas_kind: CanvasKind,
    kind: str,
    fields: dict[str, Any] | None = None,
    service_id: str | None = None,
) -> dict[str, Any]:
    """Append ONE new node — the clobber-safe way to add a node, and the single
    SSOT for node creation (D-2026-06-27-B).

    The mirror of :func:`update_node` for *adding* instead of editing: validate
    ``kind`` is creatable on ``canvas_kind`` (see :func:`creatable_kinds`), mint a
    unique id and auto-position the node **server-side** (never from the caller),
    apply only the kind's *writable content* fields from ``fields`` (the same
    :func:`writable_node_fields` allow-list ``update_node`` uses — ``label`` + the
    kind's typed text; structural / visual / reference / server fields are
    rejected and returned under ``rejected_fields``), then ``read_canvas`` →
    append the one node → re-validate the **whole** ``CanvasDoc`` (unique ids,
    kind allow-list, per-canvas minimums, edge refs) → atomic :func:`write_canvas`.
    Every other node and all edges are written back unchanged (clobber-safe).

    The node is **bare**: it carries no edges and no containment — those are
    drawn separately (directed-edge-only since v0.26.0), never auto-wired here.
    A cross-canvas master (e.g. a new actor referenced from a service) is minted
    via the reference pick-or-create flow (:func:`mashbill.masters.create_master`,
    which now delegates here), not by calling this on the wrong canvas.

    Like every Novel write this is **last-write-wins** at human pace (same as
    ``update_node``): a concurrent edit to another node on the same canvas, or two
    concurrent same-kind creates, may collide / be lost. The write also reaches
    the viewer via the file watcher, which clears the undo stack (same limit as
    D-2026-06-26-D). ``canvas_kind`` ∈ ``foundation`` / ``actors`` / ``services``
    / ``entities`` / ``feature``; ``service_id`` is required when
    ``canvas_kind == "feature"``. Raises ``ValueError`` when ``kind`` is not
    creatable on the canvas.

    Returns ``{"node": <new node dict>, "rejected_fields": [...]}`` — the same
    shape as :func:`update_node`.
    """
    allowed = creatable_kinds(canvas_kind)
    if kind not in allowed:
        raise ValueError(
            f"cannot create a {kind!r} node on the {canvas_kind!r} canvas; "
            f"creatable kinds: {sorted(allowed)}"
        )
    canvas = read_canvas(plot_root, project_id, canvas_kind, service_id)
    node_id = f"{kind}_{uuid4().hex[:8]}"
    x, y = _compute_fresh_position(canvas.nodes, kind)
    base = SketchNodeAdapter.validate_python({"id": node_id, "kind": kind, "x": x, "y": y})
    allowed_fields = set(writable_node_fields(base))
    incoming = fields or {}
    patch = {k: v for k, v in incoming.items() if k in allowed_fields}
    rejected = sorted(set(incoming) - allowed_fields)
    merged = {**base.model_dump(), **patch}
    new_node = SketchNodeAdapter.validate_python(merged)
    # Re-validate the WHOLE doc (not just the node) so a fresh node can never
    # break a canvas-level invariant — the same guard update_node relies on.
    updated = CanvasDoc.model_validate(
        canvas.model_copy(update={"nodes": [*canvas.nodes, new_node]}).model_dump(by_alias=True)
    )
    write_canvas(plot_root, project_id, updated)
    return {"node": new_node.model_dump(by_alias=True), "rejected_fields": rejected}


def list_feature_details(plot_root: Path, project_id: str) -> list[str]:
    """Return the service ids for which a Detail canvas exists.
    v0.8 layout: each service lives at ``services/{sid}/`` and its detail
    canvas is the sibling ``detail.json`` alongside ``index.md``. Folders
    without a ``detail.json`` (e.g. a service connected to a folder but
    whose detail was archived) are skipped."""
    _ensure_project(plot_root, project_id)
    services_folder = _project_dir(plot_root, project_id) / "services"
    if not services_folder.is_dir():
        return []
    return sorted(
        sid.name
        for sid in services_folder.iterdir()
        if sid.is_dir() and (sid / "detail.json").is_file()
    )
