"""Legacy v0.1 SketchDoc Pydantic models (D-2026-06-11-B).

Extracted from the migrate.py god module. v0.1 stored everything as one
``{id}.json`` under ``sketches/``. v0.4 dropped that format but migration
still needs to *read* it, so the Pydantic model lives here rather than
polluting ``mashbill/models.py``. Identical shape + validators to the
former ``SketchDoc``; kept strict so a corrupt file fails up-front instead
of producing a half-migrated folder.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from mashbill.models import SketchEdge

_V01_COMPOSITION_KINDS = {"rule", "content"}


class _V01SketchNode(BaseModel):
    """Legacy v0.1 god-object node. Migration-only.

    The current per-kind discriminated union (`SketchNode` in models.py)
    cannot parse v0.1 raw JSON because v0.1 stored typed text fields
    (``mission`` / ``core_values`` / ``identity`` strings, plus the
    full god field pool) on every node. This class is a permissive
    superset that accepts any v0.1 node shape so the migration can read
    legacy data, then constructs the right per-kind class for output.

    No discriminator dispatch — ``kind`` is a free-form string here so
    pre-v0.5 kinds like ``core`` / ``identity_facet`` parse before
    ``_normalise_legacy_node_kinds`` rewrites them.
    """

    id: str = Field(..., min_length=1)
    label: str = ""
    x: float = 0.0
    y: float = 0.0
    width: float = 180.0
    height: float = 80.0
    color: str = "#ffffff"
    shape: str = "rounded"
    icon: str | None = None
    kind: str = ""
    parent_id: str | None = None
    collapsed: bool = False
    is_root: bool = False
    details_path: str | None = None

    # Legacy v0.1 / v0.2 root-text fields. Live only on the legacy data;
    # current per-kind classes do not carry them.
    mission: str = ""
    core_values: str = ""
    identity: str = ""

    # Forward-compat fields the migration may need to read from later
    # legacy revisions (v0.2 → v0.10) before re-emitting as per-kind
    # classes. Permissive defaults; unknown keys ignored.
    # side: removed in current model (US-303); kept here only for reading
    # very old v0.x data during migration.
    side: Literal["operator", "user"] | None = None
    motivation: str = ""
    pain: str = ""

    model_config = {"extra": "ignore"}


class _V01SketchDoc(BaseModel):
    """Legacy v0.1 single-file sketch document. Migration-only.

    Loaded from ``.plot/sketches/{id}.json`` (the pre-v0.4 layout) and
    broken apart into the v0.4 folder-per-project + canvas files.
    """

    id: str = Field(..., min_length=1)
    name: str = ""
    created: str = ""  # ISO date (YYYY-MM-DD)
    updated: str = ""  # ISO datetime
    version: int = 1
    nodes: list[_V01SketchNode] = Field(default_factory=list)
    edges: list[SketchEdge] = Field(default_factory=list)

    @field_validator("id")
    @classmethod
    def _kebab_id(cls, v: str) -> str:
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError(f"sketch id must be alphanumeric with -/_ only, got {v!r}")
        return v

    @model_validator(mode="after")
    def _edges_reference_nodes(self) -> _V01SketchDoc:
        node_ids = {n.id for n in self.nodes}
        dangling = [e for e in self.edges if e.source not in node_ids or e.target not in node_ids]
        if dangling:
            missing = sorted({e.id for e in dangling})
            raise ValueError(f"edges reference unknown nodes: {missing}")
        if len({e.id for e in self.edges}) != len(self.edges):
            raise ValueError("edge ids must be unique")
        if len({n.id for n in self.nodes}) != len(self.nodes):
            raise ValueError("node ids must be unique")
        return self

    @model_validator(mode="after")
    def _parent_ids_are_valid(self) -> _V01SketchDoc:
        by_id = {n.id: n for n in self.nodes}
        for n in self.nodes:
            if n.parent_id is None:
                continue
            if n.parent_id == n.id:
                raise ValueError(f"node {n.id!r} cannot be its own parent")
            if n.parent_id not in by_id:
                raise ValueError(f"node {n.id!r}.parent_id points to unknown node {n.parent_id!r}")
        for start in self.nodes:
            seen: set[str] = set()
            current: str | None = start.id
            while current is not None:
                if current in seen:
                    raise ValueError(f"parent chain contains a cycle at node {current!r}")
                seen.add(current)
                parent = by_id[current]
                current = parent.parent_id
        return self

    @model_validator(mode="after")
    def _at_most_one_root_per_kind(self) -> _V01SketchDoc:
        # Legacy ``core`` root is normalised to ``project`` in _read_v01_sketch.
        cores = [n for n in self.nodes if n.kind == "project"]
        if len(cores) > 1:
            raise ValueError(
                f"at most one project node allowed per sketch; found {sorted(n.id for n in cores)}"
            )
        roots = [n for n in self.nodes if n.is_root]
        by_kind: dict[str, list[str]] = {}
        for r in roots:
            if r.kind not in ("actor", "service"):
                raise ValueError(
                    f"node {r.id!r} is_root=True but kind is {r.kind!r} "
                    "(only actor or service may be is_root)"
                )
            by_kind.setdefault(r.kind, []).append(r.id)
        for kind, ids in by_kind.items():
            if len(ids) > 1:
                raise ValueError(f"at most one {kind}-root allowed per sketch; found {sorted(ids)}")
        return self

    @model_validator(mode="after")
    def _composition_kinds_live_in_service(self) -> _V01SketchDoc:
        by_id = {n.id: n for n in self.nodes}
        for n in self.nodes:
            if n.kind not in _V01_COMPOSITION_KINDS:
                continue
            if n.parent_id is None:
                raise ValueError(
                    f"node {n.id!r} of kind {n.kind!r} requires a parent_id "
                    "(must live inside a service)"
                )
            parent = by_id.get(n.parent_id)
            if parent is not None and parent.kind != "service":
                raise ValueError(
                    f"node {n.id!r} of kind {n.kind!r} must be a child of a service, "
                    f"but parent {n.parent_id!r} has kind {parent.kind!r}"
                )
        return self


def _normalise_legacy_node_kinds(nodes: list[dict[str, object]]) -> bool:
    """Rewrite node kinds that were removed in v0.5 to their canonical form.

    Returns True iff any node was rewritten — callers that persist canvases
    can use this to decide whether to re-save the file.

    Transformations:
      - ``kind="core"`` → ``kind="project"`` + ``shape="circle"``. The anchor
        also loses the stale ``icon="star"`` (the seeded default) since v0.5
        surfaces node identity via the top-left kind tag, not a star icon.
      - Any node whose ``parent_id`` pointed at a legacy ``core``-kind node
        is un-parented (``parent_id=None``). In v0.2 the octagon served as
        a container and mission/identity were nested inside; v0.5 treats
        them as peers around the small Project anchor, so leaving the old
        parent link would visually trap the children inside the anchor.
      - ``kind="identity_facet"`` → ``kind="identity"`` + ``parent_id=None``.
      - Any Mission / CoreValue / Identity node carrying the seeded
        ``icon="star"`` has the icon cleared (star retired from the palette).
    """
    changed = False
    legacy_core_ids: set[str] = set()
    for n in nodes:
        if isinstance(n, dict) and n.get("kind") == "core":
            node_id = n.get("id")
            if isinstance(node_id, str):
                legacy_core_ids.add(node_id)

    for n in nodes:
        if not isinstance(n, dict):
            continue
        kind = n.get("kind")
        if kind == "core":
            n["kind"] = "project"
            if n.get("shape") in (None, "", "octagon"):
                n["shape"] = "circle"
            changed = True
        elif kind == "identity_facet":
            n["kind"] = "identity"
            n["parent_id"] = None
            changed = True

        if n.get("parent_id") in legacy_core_ids:
            n["parent_id"] = None
            changed = True

        # Read the post-rewrite kind so facets migrated to ``identity`` also
        # lose their seeded star. ``project`` gets cleaned alongside the
        # three pillar kinds — no Core-canvas kind keeps a star in v0.5.
        current_kind = n.get("kind")
        if (
            current_kind in ("project", "mission", "core_value", "identity")
            and n.get("icon") == "star"
        ):
            n["icon"] = None
            changed = True

    return changed
