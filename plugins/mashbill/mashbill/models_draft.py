"""Coach-proposed design drafts kept separately from chat transcripts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from mashbill.models_canvas import CanvasKind

DraftStatus = Literal["proposed", "confirmed", "edited", "rejected"]
ResolvedDraftStatus = Literal["confirmed", "edited", "rejected"]
DraftOrigin = Literal["recorded", "auto", "extracted"]
DraftCanvasKind = CanvasKind | Literal["project"]


class DraftRevision(BaseModel):
    """The proposal text and rationale immediately before one agreed edit."""

    proposed_text: str
    rationale: str
    updated: str


class DraftDoc(BaseModel):
    """One proposal the person explicitly chose to keep."""

    id: str
    created: str
    updated: str
    canvas_kind: DraftCanvasKind
    service_id: str | None = None
    target_node_ids: list[str] = Field(default_factory=list)
    proposed_kind: str | None = None
    proposed_text: str
    rationale: str
    status: DraftStatus = "proposed"
    origin: DraftOrigin = "recorded"
    chat_scope: str
    chat_conversation_id: str | None = None
    resolved_node_ids: list[str] = Field(default_factory=list)
    revisions: list[DraftRevision] = Field(default_factory=list)
