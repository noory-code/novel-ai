"""Composition-kind node classes (D-2026-06-11-B).

Extracted from the models.py god module. Composition kinds live inside
``feature`` canvases — metric / step / decision / group / rule /
content. Each captures one slice of how a service is realised.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from mashbill.models_kinds import BaseNodeFields

# metric retired 2026-06-20 (D-2026-06-20-H): below action altitude / not
# needed; produced value is implied by the result node + flow edge.


class StepNode(BaseNodeFields):
    """v0.15 Phase 1.2: ``step`` kind. An ordered procedural step in the
    service flow. ``order`` may be None for unordered / parallel branches."""

    kind: Literal["step"] = "step"
    order: int | None = None
    outcome: str = ""
    body: str = ""
    # v0.28.2 (D-2026-05-30-E): outcome valence for negative-case
    # (failure) visual distinction. "neutral" = happy-path default.
    polarity: Literal["positive", "negative", "neutral"] = "neutral"
    # D-2026-06-20-Q: the entities this action operates on (ids → the entities
    # registry), rendered as chips in the step inspector. AI-maintained derived
    # data map — NOT flow visualisation. The entity "어디서 쓰이나" back-ref scans
    # this field across all feature canvases.
    ref_entity_ids: list[str] = Field(default_factory=list)


class DecisionNode(BaseNodeFields):
    """v0.28.0 (D-2026-05-30-C): ``decision`` kind. A flowchart decision
    (diamond) branch point inside a feature flow — a user choice
    (방식 선택) or a system judgment (검증 성공/실패). The branches are
    user-drawn labelled outgoing edges; the node carries only the
    question (``label``) + optional notes (``body``)."""

    kind: Literal["decision"] = "decision"
    body: str = ""


class NoteNode(BaseNodeFields):
    """``note`` kind (D-2026-06-17-F). A canvas-global ambient memo on the
    Feature canvas ("모바일 우선·본문 500자") — a human-read guide AND context
    the AI always lays under its work (injected into the per-canvas framing).

    **Edgeless invariant:** a ``note`` NEVER participates in an edge (it is
    ambient, not a flow participant). Enforced both viewer-side (handleConnect)
    and server-side (``CanvasDoc._notes_are_edgeless``). Field: ``body`` (the
    memo text); ``label`` (BaseNodeFields) is its short title."""

    kind: Literal["note"] = "note"
    body: str = ""


class RuleNode(BaseNodeFields):
    """v0.15 Phase 1.2: ``rule`` kind. A composition element inside a
    service expressing an enforced policy (with per-actor permissions)."""

    kind: Literal["rule"] = "rule"
    policy: str = ""
    enforcement: str = ""
    actor_permissions: dict[str, str] = Field(default_factory=dict)
    body: str = ""


# content retired 2026-06-20 (D-2026-06-20-H): implementation artifacts are
# below action altitude (the external agent's job); user-facing artifacts are
# implied by the producing action / carried by the flow edge.
