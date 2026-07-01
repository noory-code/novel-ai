"""Node-kind taxonomy + shared `BaseNodeFields` (D-2026-06-11-B).

Extracted from the models.py god module (993 LOC) so each per-area model
file can sit under the 500-line monorepo rule. This file is the lowest
layer — no node-class definitions, only the literal taxonomies and the
shared base every per-kind class extends.
"""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

Shape = Literal[
    "rectangle",
    "rounded",
    "circle",
    "ellipse",
    "diamond",
    "hexagon",
    "octagon",
]

# v0.2 node kinds. See PHILOSOPHY.md (P5, P11).
#
# Canvas anchors (Core):
#   project          — central anchor of the Core canvas; exactly 1 per project,
#                      auto-seeded, cannot be deleted, label mirrors ProjectDoc.name.
#   mission          — statement of purpose; 1..N per Core canvas.
#   core_value       — a value the project commits to; 0..N per Core canvas.
#   identity         — an aspect of the project's identity (label = "Voice" /
#                      "Energy" / "Speech style" / "Visual tone" / …); 1..N peers.
#                      v0.5 absorbed the former ``identity_facet`` kind.
#   actor            — a class of people in the value economy. People only —
#                      external APIs / systems / bots / infrastructure are
#                      *not* actors (out of scope until Mode 2 / time-axis).
#                      v0.11 redefines this from "person/system/organisation"
#                      to "class of people" — see plot/docs/IDENTITY.md.
#   actor_ref        — reference to an actor (Service canvases); carries
#                      ``ref_actor_id`` pointing at an actor in the Actor canvas.
#   service          — value-creating hub (Overview root, Detail root, sub-service).
#   rule             — composition element inside a service (Detail only).
#   content          — composition element inside a service (Detail only).
#
# Sub-service and sub-actor are not new kinds — they're service/actor with
# a non-null parent_id (hierarchy / decomposition).
#
# Deprecated (migrated on open by ``migrate._migrate_v04_core_schema``):
#   core             — former Core root anchor (octagon). Removed in v0.3;
#                      remaining disk nodes are converted to ``project``.
#   identity_facet   — child of identity. Absorbed into ``identity`` in v0.5
#                      with parent_id cleared (flat peer model).
NodeKind = Literal[
    "project",
    "mission",
    "core_value",
    "identity",
    "actor",
    "actor_ref",
    "service",
    # feature — a capability the service offers (D-2026-06-17-D /
    #   D-2026-06-19-H). Behaviour grouping under a service; the sole drill
    #   target (opens its Feature canvas). NOT an independent value unit.
    "feature",
    "rule",
    # mission_ref / value_ref / identity_ref retired 2026-06-20
    # (D-2026-06-17-H / D-2026-06-20-G): Foundation references moved to the
    # service inspector's chip pickers (ref_value_ids / ref_identity_ids).
    # v0.10 Step 5: composition kinds inside a feature canvas.
    #   metric — how the service is measured (KPI, success rate, latency).
    #   step   — an ordered procedural step in the service's flow.
    "step",
    # v0.28.0: decision — a flowchart decision (diamond) branch point in a
    #   feature flow (user choice or system judgment). See
    #   docs/DECISIONS.md D-2026-05-30-C.
    "decision",
    # note — canvas-global ambient memo on the Feature canvas (D-2026-06-17-F).
    #   Edgeless (never participates in an edge); injected into the AI framing.
    "note",
    # v0.12: ``category`` is a thematic grouping of services. Replaces what
    # used to be the "top-level service" idiom — categories are pure
    # containers (no value creation themselves), and the actual services
    # they contain are leaf nodes (no further sub-service nesting). See
    # docs/IDENTITY.md for the why.
    "category",
]

# Composition kinds: must live inside a service (applies to SketchDoc and
# feature CanvasDoc alike).
# v0.10 Step 5: metric + step join the family. v0.28.0: decision joins.
# v0.29.0 group joined; retired 2026-06-20 (D-2026-06-19-H — chunking = feature
# level + folding is a view affordance, not a node kind).
_COMPOSITION_KINDS = {"rule", "step", "decision"}


ValueForm = Literal[
    "economic",  # 경제 — 돈, 결제, 수수료
    "attention",  # 주목 — 관심, 트래픽, 도달
    "social",  # 사회 — 이름, 명성, 관계, 신뢰
    "cognitive",  # 인지 — 정보, 데이터, 노하우
    "experience",  # 경험 — 즐거움, 편의, 성취
    "access",  # 접근권 — 기회, 멤버십, 독점성
    "effort",  # 시간·노력 — 투입 시간, 창의 노동
]


# ---------------------------------------------------------------------------
# v0.15 Phase 1 — 15-way discriminated union (god ``SketchNode`` retired)
# ---------------------------------------------------------------------------
#
# Through v0.14 the canvas node model was a single god ``SketchNode``
# class carrying every typed field for every kind as a default-empty
# string / None. v0.15 splits this per kind via a Pydantic discriminated
# union (one ``BaseNodeFields`` subclass per kind, dispatched on the
# ``kind`` literal). See D-2026-05-12-B for the rationale.


class BaseNodeFields(BaseModel):
    """Shared graph-level fields for every canvas node kind.

    Every per-kind class extends this; typed text fields are declared on
    the per-kind class only (no god-object pool of all fields).

    The ``_details_path_is_safe`` validator runs on every subclass so
    that any node carrying a ``details_path`` is path-traversal-checked
    at construction time.
    """

    id: str = Field(..., min_length=1)
    label: str = ""
    x: float = 0.0
    y: float = 0.0
    # v0.24.15 (D-2026-05-24-A) — reduced from 140×60 to 80×36, follow-up
    # to D-2026-05-17-N. Tighter default suits Services / FeatureDetail
    # hub-spoke layouts without overflow. Existing nodes keep their own
    # values in canvas.json; only nodes that omit width/height (defaults
    # filled by Pydantic) get the new size.
    width: float = 80.0
    height: float = 36.0
    color: str = "#ffffff"
    shape: Shape = "rounded"
    icon: str | None = None
    # v0.26.0 (D-2026-05-25-A) — ``parent_id`` removed. Hierarchy /
    # containment is now expressed via directed edges (``SketchEdge.directed``).
    # The v0.26 read-time migration in ``folder_io._migrate_parent_id_to_directed_edges``
    # converts pre-v0.26 ``parent_id`` to directed edges on first read.
    collapsed: bool = False
    is_root: bool = False
    details_path: str | None = None
    # v0.16.12 — owner identifier for multi-user prep. ``None`` when
    # authored by an anonymous / single-user session. Server fills
    # from session context once multi-user lands.
    owner: str | None = None
    # v0.17.2 Phase 2 (D-2026-05-16-C) — per-node version laying the
    # ground for Phase 3 "Publish" (MAJOR bump) + Phase 4 MINOR
    # propagation. Format: ``v<MAJOR>.<MINOR>`` (e.g. ``v1.0`` /
    # ``v2.3``). Defaults to ``v1.0`` so pre-Phase-2 canvases auto-fill
    # on read; first write after open serialises the new key.
    version: str = "v1.0"
    # v0.22.0 (D-2026-05-17-H) — publish dirty baseline. Captures the
    # content snapshot at the most recent publish (typed-text fields +
    # label + body + incident edges); visual fields excluded. Server
    # compares this to the current node + incident edges to compute
    # ``_dirty`` for the Inspector's publish button gate. ``None`` ⇒
    # never published (or pre-v0.22.0 migration) ⇒ treated as dirty
    # (initial publish is always allowed). Persisted in canvas.json
    # under the leading-underscore alias to mark it server-managed.
    publish_baseline: dict[str, Any] | None = Field(default=None, alias="_publish_baseline")

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def _details_path_is_safe(self) -> BaseNodeFields:
        if self.details_path is None:
            return self
        path = self.details_path.strip()
        if not path:
            raise ValueError(f"node {self.id!r} details_path must not be blank")
        if path.startswith("/"):
            raise ValueError(f"node {self.id!r} details_path must be relative, got {path!r}")
        # Reject ``..`` segments to prevent escape; normalise slashes first.
        parts = path.replace("\\", "/").split("/")
        if any(part == ".." or part == "" for part in parts):
            raise ValueError(
                f"node {self.id!r} details_path must not contain '..' or empty segments"
            )
        return self

    @model_validator(mode="after")
    def _version_is_valid(self) -> BaseNodeFields:
        if not re.match(r"^v\d+\.\d+$", self.version):
            raise ValueError(
                f"node {self.id!r} version must match ``^v\\d+\\.\\d+$`` "
                f"(e.g. ``v1.0``), got {self.version!r}"
            )
        return self
