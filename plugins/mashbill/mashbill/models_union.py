"""Full 15-way node union + edge model (D-2026-06-11-B).

Extracted from the models.py god module. ``SketchNode`` is the discriminated
union ``CanvasDoc.nodes`` uses; ``SketchEdge`` is the freeform edge model.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field, TypeAdapter

from mashbill.models_actors import (
    ActorNode,
    ActorRefNode,
    CategoryNode,
    FeatureNode,
    ServiceNode,
)
from mashbill.models_composition import (
    DecisionNode,
    NoteNode,
    RuleNode,
    StepNode,
)
from mashbill.models_entity import (
    EntityNode,
)
from mashbill.models_foundation import (
    CoreValueNode,
    IdentityNode,
    MissionNode,
    ProjectNode,
)
from mashbill.models_kinds import ValueForm

# ---------------------------------------------------------------------------
# v0.15 Phase 1.2 — 15-way discriminated union (replaces god ``SketchNode``)
# ---------------------------------------------------------------------------
#
# Pydantic dispatches construction / validation on the ``kind`` literal.
# ``CanvasDoc.nodes: list[SketchNode]`` automatically narrows each node to
# its correct kind subclass. Use ``SketchNode`` for type annotations and
# the per-kind classes for direct construction.

SketchNode = Annotated[
    ProjectNode
    | MissionNode
    | CoreValueNode
    | IdentityNode
    | ActorNode
    | ActorRefNode
    | ServiceNode
    | FeatureNode
    | CategoryNode
    | StepNode
    | DecisionNode
    | NoteNode
    | RuleNode
    | EntityNode,
    Field(discriminator="kind"),
]

# Validate raw dicts against the discriminated union without going through
# a ``CanvasDoc`` wrapper. Equivalent to ``BaseModel.model_validate`` on
# the legacy god class — call sites that need per-kind dispatch on a
# standalone dict use ``SketchNodeAdapter.validate_python(raw)``.
SketchNodeAdapter: TypeAdapter[
    ProjectNode
    | MissionNode
    | CoreValueNode
    | IdentityNode
    | ActorNode
    | ActorRefNode
    | ServiceNode
    | FeatureNode
    | CategoryNode
    | StepNode
    | DecisionNode
    | NoteNode
    | RuleNode
    | EntityNode
] = TypeAdapter(SketchNode)


class SketchEdge(BaseModel):
    """A freeform edge between two nodes."""

    id: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1)
    target: str = Field(..., min_length=1)
    source_handle: str | None = Field(default=None, alias="sourceHandle")
    target_handle: str | None = Field(default=None, alias="targetHandle")
    label: str = ""
    style: Literal["solid", "dashed"] = "solid"

    # v0.26.0 (D-2026-05-25-A) — directed edges carry parent→child
    # semantics. When True, the renderer draws an arrowhead at the
    # target end and the fold / hierarchy logic treats source as
    # parent. New edges default to True; the v0.26 read-time migration
    # converts pre-v0.26 nodes' parent_id into directed=True edges.
    directed: bool = True

    # v0.30.0 (D-2026-05-31-C) — stored edge semantic. The SSOT read by
    # both the viewer (fold / layout / styling) and the server
    # (propagation.py publish MINOR-bump): "flow" (sequence / hierarchy,
    # source = parent), "injection" (essence flows into the target —
    # excluded from fold), "inheritance" (actors-canvas tree, target =
    # superclass = parent). Default-assigned by edge_semantics.classify_edge
    # on creation/migration; authoritative once set. Defaults to "flow"
    # for back-compat with pre-v0.30 edges (a read-time migration assigns
    # the correct value).
    relation: Literal["flow", "injection", "inheritance"] = "flow"

    # v0.2 additions
    action_verb: str | None = None
    value_form: list[ValueForm] = Field(default_factory=list)

    model_config = {"populate_by_name": True}
