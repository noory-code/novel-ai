"""Canvas + project document models (D-2026-06-11-B).

Extracted from the models.py god module. ``CanvasDoc`` is the per-canvas
container with all the structural validators; ``ProjectDoc`` is the
project-level metadata and anchor SSOT; ``AnchorPlacement`` is the
per-canvas-kind anchor visual.

A project is split into five canvas kinds:
  foundation        — project / mission / core_value / identity (singleton).
                      v0.10 renamed from ``core``.
  actors            — Actor definitions (singleton, SSOT for actor identities)
  services          — top-level services (singleton). v0.8 renamed from
                      ``services_overview``; paired with ``feature``
                      for the per-service drill-down.
  entities          — product data objects the services act on (singleton,
                      D-2026-06-17-I). AI-maintained conceptual map; symmetric
                      to ``actors`` (who acts vs what is acted on).
  feature    — per-service drill-down (one per service in overview)

Each ``CanvasDoc`` enforces its own allowed ``NodeKind`` set and structural
rules; shared validators (edge refs, parent cycles, unique ids) still apply.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from mashbill.models_foundation import PROJECT_ANCHOR_ID
from mashbill.models_kinds import Shape
from mashbill.models_union import SketchEdge, SketchNode

CanvasKind = Literal["foundation", "actors", "services", "entities", "feature"]

# Foundation refs (mission_ref / value_ref / identity_ref) retired 2026-06-20
# (D-2026-06-17-H / D-2026-06-20-G) — moved to the service inspector chips.
_FOUNDATION_REFS: set[str] = set()

_ALLOWED_KINDS_BY_CANVAS: dict[str, set[str]] = {
    "foundation": {"project", "mission", "core_value", "identity"},
    # v0.11.4 — project anchor is now visible on every primary canvas so the
    # mental model "everything spreads out from the project" reads at a
    # glance. The Foundation canvas remains the sole master (label-sync
    # source from ProjectDoc.name); the actors / services instances are
    # auto-seeded copies kept in sync.
    "actors": {"actor", "project"},
    # v0.12 — services canvas (top view) carries:
    #   - project anchor (centre)
    #   - category (thematic grouping)
    #   - service (leaf, child of a category via parent_id)
    # Categories sit at the top level; services are nested inside them.
    # D-2026-06-17-D — a ``feature`` (capability) nests under a service via a
    # directed edge; it is the sole drill target. All sub-service / refs /
    # composition still live in feature.
    "services": {"project", "category", "service", "feature"},
    # D-2026-06-17-I — the Entities canvas carries the product data objects the
    # services act on (글 / 댓글 / 사용자): the project anchor (centre) + entity
    # nodes. AI-maintained; seeded EMPTY (like services). Feature-action →
    # entity *reference* kinds are blocked-on-open (FEATURE canvas, separate).
    "entities": {"project", "entity"},
    # D-2026-06-17-D — the detail canvas drills into a **feature** (its
    # actions / rules), not a service. The root anchor is the feature node;
    # the wire ``canvas_kind`` stays ``feature`` until the canvas-string
    # rename (product-gated).
    "feature": {
        "feature",
        "rule",
        "step",
        "decision",
        "note",
        "actor_ref",
    }
    | _FOUNDATION_REFS,
}


class CanvasDoc(BaseModel):
    """One logical canvas (Core, Actors, Services Overview, or a Service Detail).

    Stored as ``.plot/sketches/{project_id}/{canvas_id}.json`` in v0.2.
    """

    canvas_id: str = Field(..., min_length=1)
    canvas_kind: CanvasKind
    # feature only: the ``feature`` node id this detail canvas drills into
    # (D-2026-06-17-D — feature is the drill target). Must equal ``canvas_id`` to
    # keep the 1:1 pairing with the Overview node. The field name + wire kind keep
    # the ``service`` prefix until the canvas-string rename (product-gated).
    feature_ref: str | None = None
    nodes: list[SketchNode] = Field(default_factory=list)
    edges: list[SketchEdge] = Field(default_factory=list)

    @model_validator(mode="after")
    def _unique_ids(self) -> CanvasDoc:
        if len({n.id for n in self.nodes}) != len(self.nodes):
            raise ValueError("node ids must be unique")
        if len({e.id for e in self.edges}) != len(self.edges):
            raise ValueError("edge ids must be unique")
        return self

    @model_validator(mode="after")
    def _edges_reference_nodes(self) -> CanvasDoc:
        # The synthetic project anchor lives in ``ProjectDoc.anchors``,
        # not in ``self.nodes`` — but user-drawn edges may legitimately
        # reference it per D-2026-05-04-B SPEC mandate. Treat its id as
        # a known endpoint for validation. See D-2026-05-13-M.
        node_ids = {n.id for n in self.nodes} | {PROJECT_ANCHOR_ID}
        dangling = [e for e in self.edges if e.source not in node_ids or e.target not in node_ids]
        if dangling:
            # Report the *missing endpoint ids*, not the edge ids.
            # The previous ``{e.id for e in dangling}`` produced misleading
            # error text (it surfaced edge ids as if they were missing
            # nodes), which sent D-2026-05-13-I diagnosis down a wrong
            # path. Fixed in D-2026-05-13-M.
            missing = sorted(
                {ep for e in dangling for ep in (e.source, e.target) if ep not in node_ids}
            )
            raise ValueError(f"edges reference unknown nodes: {missing}")
        return self

    # v0.26.0 (D-2026-05-25-A) — ``_parent_ids_are_valid`` removed
    # alongside the ``parent_id`` field. Hierarchy invariants (no
    # self-parent, no cycles) are now properties of the directed-edge
    # graph; if needed, add a ``_directed_edge_acyclic`` validator
    # later. Pre-v0.26 data is migrated read-side, not validated here.

    @model_validator(mode="after")
    def _notes_are_edgeless(self) -> CanvasDoc:
        """D-2026-06-17-F — a ``note`` is ambient canvas-global context, NOT a
        flow participant, so it NEVER takes an edge. Reject any edge whose
        source or target is a note node (mirrors the viewer ``handleConnect``
        guard so a hand-edited / MCP-written doc can't smuggle one in)."""
        note_ids = {n.id for n in self.nodes if n.kind == "note"}
        if not note_ids:
            return self
        offending = sorted(
            {ep for e in self.edges for ep in (e.source, e.target) if ep in note_ids}
        )
        if offending:
            raise ValueError(f"note nodes must be edgeless; edges touch notes: {offending}")
        return self

    @model_validator(mode="after")
    def _kinds_allowed_on_canvas(self) -> CanvasDoc:
        allowed = _ALLOWED_KINDS_BY_CANVAS[self.canvas_kind]
        strays = sorted(
            {n.kind for n in self.nodes if n.kind is not None and n.kind not in allowed}
        )
        if strays:
            raise ValueError(
                f"kinds not allowed on {self.canvas_kind!r} canvas: {strays} "
                f"(allowed: {sorted(allowed)})"
            )
        return self

    @model_validator(mode="after")
    def _foundation_canvas_rules(self) -> CanvasDoc:
        if self.canvas_kind != "foundation":
            return self
        # v0.13 Phase 0: project anchor is now stored in ProjectDoc.anchors,
        # not as a node here. Old v0.12 files may still have a project node;
        # tolerate it (the migrator removes them) but enforce uniqueness +
        # top-level if present.
        projects = [n for n in self.nodes if n.kind == "project"]
        if len(projects) > 1:
            raise ValueError(
                f"foundation canvas may carry at most one legacy project node; "
                f"found {len(projects)}"
            )
        # v0.26.0 (D-2026-05-25-A) — parent_id checks removed alongside
        # the field. Project-node top-levelness is now implicit (no
        # incoming directed edge); not validated at schema level.
        missions = [n for n in self.nodes if n.kind == "mission"]
        identities = [n for n in self.nodes if n.kind == "identity"]
        if len(missions) < 1:
            raise ValueError(
                f"foundation canvas requires at least one mission node; found {len(missions)}"
            )
        if len(identities) < 1:
            raise ValueError(
                f"foundation canvas requires at least one identity node; found {len(identities)}"
            )
        return self

    # v0.26.0 (D-2026-05-25-A) — ``_services_canvas_rules`` removed.
    # The "service must be nested in a category" and "category must be
    # top-level" invariants were enforced via ``parent_id``; with the
    # field gone, containment is expressed via directed edges, and the
    # canvas no longer enforces shape at the schema level. Domain
    # guidance moves to docs (CONCEPTS.md / SPEC.md §Services).

    @model_validator(mode="after")
    def _detail_canvas_rules(self) -> CanvasDoc:
        if self.canvas_kind != "feature":
            return self
        if not self.feature_ref:
            raise ValueError("feature canvas requires feature_ref")
        if self.feature_ref != self.canvas_id:
            raise ValueError(
                f"feature feature_ref {self.feature_ref!r} must match canvas_id {self.canvas_id!r}"
            )
        # D-2026-06-17-D — the detail canvas drills into a **feature**, so its
        # root anchor is the feature node (was a ``service`` pre-overhaul).
        root_features = [n for n in self.nodes if n.kind == "feature" and n.id == self.canvas_id]
        if not root_features:
            raise ValueError(
                f"feature canvas must contain a root feature with id {self.canvas_id!r}"
            )
        # v0.26.0 (D-2026-05-25-A) — composition-kind parent_id checks
        # removed alongside the field. Containment of step / rule / decision /
        # note under their root-feature is expressed via directed edges; not
        # validated at schema level.
        return self

    @model_validator(mode="after")
    def _actors_canvas_minimum(self) -> CanvasDoc:
        # v0.11 — IDENTITY.md "Service minimum baseline": every project needs
        # ≥ 2 actor classes (typically operator + user). Without two sides,
        # value exchange can't happen.
        if self.canvas_kind != "actors":
            return self
        actors = [n for n in self.nodes if n.kind == "actor"]
        if len(actors) < 2:
            raise ValueError(
                f"actors canvas requires at least 2 actor classes "
                f"(operator + user), got {len(actors)}. See IDENTITY.md."
            )
        return self

    @model_validator(mode="after")
    def _feature_actor_refs_minimum(self) -> CanvasDoc:
        # v0.27.16 (D-2026-05-28-K) — loosened from ≥ 2 to ≥ 1.
        # Per D-2026-05-28-J the operator side of a service is the
        # *service itself* (not a separate Admin / System actor),
        # so a single user-side actor_ref is enough. The pre-v0.27.16
        # rule ("≥ 2: operator + user") forced an Admin placeholder
        # on canvases that semantically had no second human actor,
        # which the user flagged as a category error on 2026-05-28.
        # We keep ≥ 1 because every step needs a subject (D-2026-05-28-J);
        # zero actor_refs means there's no one doing the steps.
        if self.canvas_kind != "feature":
            return self
        actor_refs = [n for n in self.nodes if n.kind == "actor_ref"]
        if len(actor_refs) < 1:
            raise ValueError(
                f"feature {self.canvas_id!r} requires at least 1 "
                f"actor_ref node (the subject of the service's steps), "
                f"got 0. See SPEC.md §Service composition model "
                f"(D-2026-05-28-J)."
            )
        return self


class AnchorPlacement(BaseModel):
    """v0.13 Phase 0: per-canvas position/visual of the Project anchor.

    Before v0.13, every primary canvas (foundation/actors/services) carried
    its own ``project`` kind node, redundantly storing label / position / size /
    colour / shape on each. ProjectDoc.name was the only true SSOT for the
    label; positions duplicated.

    v0.13 promotes the anchor itself to ProjectDoc — one ``AnchorPlacement``
    per canvas kind. Canvas .json files no longer carry a ``project`` node;
    the renderer derives the anchor from ProjectDoc + canvas_kind and injects
    it into React Flow's node array at render time.
    """

    x: float = -75.0
    y: float = -75.0
    width: float = 150.0
    height: float = 150.0
    color: str = "#fef3c7"
    shape: Shape = "circle"


def _default_anchors() -> dict[str, AnchorPlacement]:
    return {
        "foundation": AnchorPlacement(),
        "actors": AnchorPlacement(),
        "services": AnchorPlacement(),
        "entities": AnchorPlacement(),
    }


class ProjectDoc(BaseModel):
    """Project-level metadata. Stored as ``.plot/sketches/{project_id}/project.json``.

    Replaces v0.1's monolithic ``SketchDoc`` as the top-level entity; nodes and
    edges move into per-canvas ``CanvasDoc`` files alongside.

    v0.13 Phase 0: ``anchors`` becomes the SSOT for the per-canvas Project
    anchor (was duplicated as a ``project`` node in every canvas .json).
    """

    id: str = Field(..., min_length=1)
    name: str = ""
    created: str = ""  # ISO date
    updated: str = ""  # ISO datetime
    version: int = 3
    # v0.13 Phase 0 — per-canvas project anchor positions. Default-seeded so
    # any project loaded from a v0.12 file gets sensible defaults without an
    # explicit migration; the migrator overwrites these from the old per-
    # canvas ``project`` nodes if any are present.
    anchors: dict[str, AnchorPlacement] = Field(default_factory=_default_anchors)
    # v0.24.13 (D-2026-05-21-B) — project-level semver. Distinct from
    # ``version`` (schema migration counter). Represents the *blueprint
    # release version* — bumped explicitly via the publish endpoint
    # (major/minor/patch), each bump creates a git tag. Default "v0.1.0"
    # for new projects; migration backfills existing projects.
    blueprint_version: str = "v0.1.0"

    @field_validator("id")
    @classmethod
    def _kebab_id(cls, v: str) -> str:
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError(f"project id must be alphanumeric with -/_ only, got {v!r}")
        return v
