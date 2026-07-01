"""Per-canvas v0.1 → v0.2 builders (D-2026-06-11-B).

Extracted from the migrate.py god module. Converts a parsed legacy v0.1
``_V01SketchDoc`` into the four current canvases:

  * Foundation — promotes legacy root text fields into v0.5 top-level
    nodes and plants the v0.5 Project anchor in the centre.
  * Actors    — actor subtree, parent chain cleaned, ≥2 actor pad.
  * Services  — top-level services wrapped under a default category.
  * feature per top-level service — descendants converted to
    per-kind classes, with the v0.11 actor_ref seeds (operator + user).

Each helper takes ``_V01SketchNode`` instances and returns current
per-kind classes; the v0.1 god-object lives only in the legacy parser.
"""

from __future__ import annotations

from mashbill.migrate_v01_models import _V01SketchNode
from mashbill.models import (
    ActorNode,
    CanvasDoc,
    CategoryNode,
    CoreValueNode,
    IdentityNode,
    MissionNode,
    ProjectNode,
    ServiceNode,
    SketchEdge,
    SketchNode,
)


def _build_foundation_canvas(core_root: _V01SketchNode | None, project_name: str) -> CanvasDoc:
    """Promote v0.1 root text fields (mission / core_values / identity) into
    v0.5 top-level nodes on the Core canvas, and plant the v0.5 Project
    anchor in the centre. Empty fields get placeholder nodes so the
    ``_core_canvas_rules`` validator (≥ 1 mission, ≥ 1 identity, exactly
    1 project) stays happy.
    """
    nodes: list[SketchNode] = [
        ProjectNode(
            id="project",
            label=project_name,
            x=-75,
            y=-75,
            width=150,
            height=150,
            color="#fef3c7",
            shape="circle",
        ),
    ]

    # v0.9.1 dropped typed fields — legacy ``mission`` text on core-root
    # has nowhere structured to land. The user can paste it into the new
    # node's ``details.md`` after migration if they care; we don't auto-
    # synthesise an MD file here to keep migration side-effect-free.
    nodes.append(
        MissionNode(
            id="mission",
            label="Mission",
            x=-360,
            y=-45,
            width=200,
            height=90,
            color="#fef3c7",
            shape="rounded",
        )
    )

    # Core values split on newlines so each becomes its own node. If the
    # old field was empty, seed one placeholder so the pillar is visible.
    cv_raw = (core_root.core_values if core_root else "").strip()
    if cv_raw:
        lines = [line.strip() for line in cv_raw.splitlines() if line.strip()]
    else:
        lines = ["Core value"]
    for i, line in enumerate(lines):
        nodes.append(
            CoreValueNode(
                id=f"core-value-{i + 1}",
                label=line,
                x=-90,
                y=-260 + i * 96,
                width=180,
                height=80,
                color="#fde68a",
                shape="rounded",
            )
        )

    # Same: legacy ``identity`` text is dropped. User can paste it into
    # the new node's ``details.md`` after migration.
    nodes.append(
        IdentityNode(
            id="identity",
            label="Voice",
            x=160,
            y=-45,
            width=200,
            height=90,
            color="#fed7aa",
            shape="rounded",
        )
    )

    return CanvasDoc(canvas_id="foundation", canvas_kind="foundation", nodes=nodes)


def _build_actors_canvas(
    actor_nodes: list[_V01SketchNode],
    actor_root: _V01SketchNode | None,
    edges: list[SketchEdge],
) -> CanvasDoc:
    """Actor subtree. If actor-root was the only content, keep it as a
    top-level actor; sub-actors keep their parent_id relative to it.
    Edges reaching outside the subtree are dropped.

    Converts each legacy v0.1 ``_V01SketchNode`` into a current-schema
    ``ActorNode`` at the boundary; downstream helpers
    (``_backfill_actor_sides`` / ``_ensure_minimum_actors``) operate on
    the per-kind class.
    """
    _ = actor_root  # kept for signature compatibility; v0.26 made root unused
    cleaned: list[ActorNode] = []
    for n in actor_nodes:
        # v0.26.0 (D-2026-05-25-A) — parent_id field removed from v0.2
        # schema. Hierarchy is now expressed via directed edges, which
        # the v0.26 read-side migration auto-creates from any pre-v0.26
        # parent_id on disk. Here we just drop the field on the way
        # into v0.2 models.
        cleaned.append(
            ActorNode(
                id=n.id,
                label=n.label,
                x=n.x,
                y=n.y,
                width=n.width,
                height=n.height,
                color=n.color,
                shape=n.shape,  # type: ignore[arg-type]
                icon=n.icon,
                collapsed=n.collapsed,
                is_root=False,  # is_root meaningless across canvases
                details_path=n.details_path,
                # D-2026-06-15-J: actor is identity-only. motivation/pain
                # are per-service now (actor_ref), so a legacy v0.1 actor's
                # motivation/pain are not carried onto the v0.2 actor
                # master (accepted tradeoff; realistic legacy data is empty).
                side=n.side,
            )
        )
    cleaned_ids = {n.id for n in cleaned}
    scoped_edges = [e for e in edges if e.source in cleaned_ids and e.target in cleaned_ids]
    # v0.11 — actors canvas requires ≥ 2 actor classes. Pad with placeholders
    # if a legacy v0.1 sketch had fewer; the user can rename them. Also
    # backfill ``side`` on legacy actors that have it unset (default = "user"
    # since the typical legacy pattern was "one user-side actor").
    cleaned = _backfill_actor_sides(cleaned)
    cleaned = _ensure_minimum_actors(cleaned)
    return CanvasDoc(
        canvas_id="actors",
        canvas_kind="actors",
        nodes=list(cleaned),
        edges=scoped_edges,
    )


def _backfill_actor_sides(nodes: list[ActorNode]) -> list[ActorNode]:
    """v0.11 migration helper: legacy actor nodes have ``side = None``.
    Default them to ``"user"`` so the model is self-consistent. Users can
    flip individual actors to ``"operator"`` via the Inspector after open.
    """
    out: list[ActorNode] = []
    for n in nodes:
        if n.side is None:
            out.append(n.model_copy(update={"side": "user"}))
        else:
            out.append(n)
    return out


def _ensure_minimum_actors(nodes: list[ActorNode]) -> list[ActorNode]:
    """v0.11 migration helper: pad an under-populated actors canvas with
    placeholder classes so the new ≥ 2 validator doesn't reject open.
    Idempotent — adds only what's missing.
    """
    has_operator = any(n.side == "operator" for n in nodes)
    has_user = any(n.side == "user" for n in nodes)
    pad: list[ActorNode] = []
    used_ids = {n.id for n in nodes}
    if not has_operator:
        oid = "operator" if "operator" not in used_ids else "operator-seed"
        pad.append(
            ActorNode(
                id=oid,
                label="Operator",
                side="operator",
                x=-160,
                y=-50,
                width=140,
                height=80,
                color="#bae6fd",
                shape="rounded",
            )
        )
    if not has_user and len(nodes) + len(pad) < 2:
        uid = "user" if "user" not in used_ids else "user-seed"
        pad.append(
            ActorNode(
                id=uid,
                label="User",
                side="user",
                x=40,
                y=-50,
                width=140,
                height=80,
                color="#fecaca",
                shape="rounded",
            )
        )
    return nodes + pad


def _v01_to_service(n: _V01SketchNode) -> ServiceNode:
    """Convert a legacy v0.1 ``service``-kind node into a current
    ``ServiceNode``. v0.1 did not carry the v0.10+ typed-text fields
    (``what`` / ``value_created`` / ``scope`` / ``trigger`` / ``how`` /
    ``outcome``); defaults stay empty. Drops legacy ``is_root`` /
    ``mission`` / ``core_values`` / ``identity`` god-pool fields.

    v0.26.0 (D-2026-05-25-A) — parent_id field removed; the optional
    ``parent_id`` argument is gone. Hierarchy is now expressed via
    directed edges, auto-created by the read-side migration in
    ``folder_io._migrate_parent_id_to_directed_edges`` for any
    pre-v0.26 raw data that still carries ``parent_id`` on disk.
    """
    return ServiceNode(
        id=n.id,
        label=n.label,
        x=n.x,
        y=n.y,
        width=n.width,
        height=n.height,
        color=n.color,
        shape=n.shape,  # type: ignore[arg-type]
        icon=n.icon,
        collapsed=n.collapsed,
        is_root=False,
        details_path=n.details_path,
    )


def _split_services(
    service_nodes: list[_V01SketchNode],
    service_root: _V01SketchNode | None,
    edges: list[SketchEdge],
) -> tuple[CanvasDoc, list[CanvasDoc]]:
    """Top-level services become Overview nodes (no nesting); each
    top-level service + its descendants becomes a Detail canvas.
    ``service-root`` itself is dropped — it was a layout anchor only.

    Converts legacy v0.1 ``_V01SketchNode`` instances into current
    per-kind classes at the boundary.
    """
    service_root_id = service_root.id if service_root else None

    # Top-level = direct children of service-root, OR a service that has no
    # parent at all in the input set.
    top_level: list[_V01SketchNode] = []
    for n in service_nodes:
        if n.kind != "service":
            continue
        if n.id == service_root_id:
            continue  # drop the anchor
        parent = n.parent_id
        if parent is None or parent == service_root_id:
            top_level.append(n)

    # v0.12 — services canvas now requires services to be nested inside a
    # category. Wrap all v0.1-migrated top-level services under a single
    # default category so the migrated canvas validates. Users can split
    # into more thematic categories afterwards.
    overview_nodes: list[SketchNode] = []
    if top_level:
        overview_nodes.append(
            CategoryNode(
                id="default-category",
                label="Services",
                theme="Migrated services",
                x=-200,
                y=-50,
                width=200,
                height=100,
                color="#e2e8f0",
                shape="rounded",
            )
        )
    for n in top_level:
        # v0.26.0 (D-2026-05-25-A) — no parent_id; v0.1 services come
        # in as flat overview nodes. The "Migrated services" category
        # is still seeded above as a visual grouping; relating services
        # to it is the user's job via a directed edge once they open
        # the canvas.
        overview_nodes.append(_v01_to_service(n))
    overview_ids = {n.id for n in overview_nodes}
    overview_edges = [e for e in edges if e.source in overview_ids and e.target in overview_ids]
    overview = CanvasDoc(
        canvas_id="services",
        canvas_kind="services",
        nodes=overview_nodes,
        edges=overview_edges,
    )

    # D-2026-06-17-D — detail canvases are per **feature** now (the drill
    # target), and v0.1 predates the feature kind. So migration produces the
    # overview only; v0.1 service decomposition (sub-services / rules that used
    # to seed a per-service detail) is dropped — the user re-authors it as
    # features after migrating, and the live overview↔detail sync seeds each
    # feature's detail on first open.
    return overview, []
