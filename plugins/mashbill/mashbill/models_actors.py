"""Actor + service node classes (D-2026-06-11-B).

Extracted from the models.py god module. Contains the 7 non-Foundation
canvas-anchor node kinds: actor / actor_ref / service / category +
mission_ref / value_ref / identity_ref. The four ref classes carry their
own ``@model_validator`` that mirrors the dispatch ``_ref_kind_requires_ref_id``
on the retired god ``SketchNode``.
"""

from __future__ import annotations

from typing import Literal

from pydantic import ConfigDict, Field, model_validator

from mashbill.models_kinds import BaseNodeFields


class ActorNode(BaseNodeFields):
    """v0.15 Phase 1: ``actor`` kind. A class of people in the value
    economy (PHILOSOPHY P5, IDENTITY.md ``Actor as class``).

    (side removed US-303; legacy data ignored)"""

    model_config = ConfigDict(extra="ignore")
    kind: Literal["actor"] = "actor"
    body: str = ""


class ActorRefNode(BaseNodeFields):
    """``actor_ref`` kind — a **read-only anchor** (D-2026-06-19-I). On the
    Feature canvas it marks the flow's subject ("who starts / who can"); it is
    NOT a value-exchange editor. Its former per-(actor×service) fields —
    ``gives`` / ``receives`` / ``motivation`` / ``pain`` — are **retired**
    (supersedes `D-2026-06-15-J`): role-level value lives on the Actors
    relationship edges, aggregate value on the service "뭐가 좋아지나?". Carries
    only ``ref_actor_id`` (the master it points at). (side removed US-303)"""

    model_config = ConfigDict(extra="ignore")
    kind: Literal["actor_ref"] = "actor_ref"
    ref_actor_id: str | None = None

    @model_validator(mode="after")
    def _ref_actor_id_required(self) -> ActorRefNode:
        if not self.ref_actor_id:
            raise ValueError(f"node {self.id!r} of kind 'actor_ref' requires ref_actor_id")
        return self


class ServiceNode(BaseNodeFields):
    """``service`` kind — the outcome-owning hub (PHILOSOPHY P5). It groups
    the capabilities that help one or more human actors reach one coherent
    outcome. Multi-actor value exchange is allowed but not required.

    D-2026-06-17-B / D-2026-06-20-F — the inspector is **5 question-titled
    fields**: 2 typed-text (왜 필요한가? = ``problem``; 뭐가 좋아지나? =
    ``value_created``) + 3 multi-select **reference** lists rendered as chips
    (누가 참여하나? = ``ref_actor_ids`` → actors; 뭘 양보 못 하나? =
    ``ref_value_ids`` → core_values; 어떤 결로 다가가나? = ``ref_identity_ids``
    → identities). The old 9 free-text fields (target_side / what / scope /
    trigger / how / outcome / do / dont / body) are **deleted** (discard, no
    migration — no production data yet, D-2026-06-20-F). Refs are id arrays on
    the service (Option B), not separate ``*_ref`` nodes."""

    kind: Literal["service"] = "service"
    problem: str = ""
    value_created: str = ""
    # Reference picks (Option B, D-2026-06-20-F) — ids of master nodes the chips
    # point at: actors (Actors canvas), core_values + identities (Foundation).
    ref_actor_ids: list[str] = Field(default_factory=list)
    ref_value_ids: list[str] = Field(default_factory=list)
    ref_identity_ids: list[str] = Field(default_factory=list)


class FeatureNode(BaseNodeFields):
    """``feature`` kind (D-2026-06-17-D / D-2026-06-19-H). A capability the
    service offers (글쓰기 / 편집) — a **behaviour grouping under a service**,
    not a separate outcome. A feature that starts to own a distinct outcome is
    promoted to a service. The **sole drill target**: clicking a feature opens its
    Feature canvas (a UX flowchart). Nested under a service via a directed
    edge (the same child mechanism category→service uses).

    ``proposed`` = the one-line "무엇을 할 수 있나?" capability summary."""

    kind: Literal["feature"] = "feature"
    proposed: str = ""
    # D-2026-07-05-E — participation chain: WHO acts in this feature, picked
    # from (narrowed to, coached/UI-soft) its service's participants.
    ref_actor_ids: list[str] = Field(default_factory=list)


class CategoryNode(BaseNodeFields):
    """v0.15 Phase 1: ``category`` kind. An optional visual grouping used only
    when two or more services share a useful theme or surface. It owns no
    outcome. ``ref_actor_ids`` can name the human roles shared by the group;
    the relation remains coached/UI-soft, never a validator. ``theme`` is the
    one-line statement of the common thread."""

    kind: Literal["category"] = "category"
    theme: str = ""
    body: str = ""
    ref_actor_ids: list[str] = Field(default_factory=list)


# mission_ref / value_ref / identity_ref retired 2026-06-20 (D-2026-06-17-H /
# D-2026-06-20-G): Foundation references moved to the service inspector's chip
# pickers (core_value + identity) — they were redundant standalone nodes. The
# only surviving standalone reference node is `actor_ref` (read-only anchor).
