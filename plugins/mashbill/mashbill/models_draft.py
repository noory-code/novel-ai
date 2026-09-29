"""Coach-proposed design drafts kept separately from chat transcripts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from mashbill.models_canvas import CanvasKind

DraftStatus = Literal["proposed", "confirmed", "edited", "rejected"]
ResolvedDraftStatus = Literal["confirmed", "edited", "rejected"]
DraftOrigin = Literal["recorded", "auto", "extracted"]
DraftCanvasKind = CanvasKind | Literal["project"]


class DraftDoc(BaseModel):
    """One durable proposal shown by the coach during a design conversation."""

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
    resolved_node_ids: list[str] = Field(default_factory=list)
