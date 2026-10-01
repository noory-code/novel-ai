"""Serialized public operations for retrospective and feedback notes."""

from __future__ import annotations

from .formats import Feedback, Retrospective
from .workspace import Workspace, workspace_locked


@workspace_locked
def record_retrospective(ws: Workspace, note: Retrospective) -> Retrospective:
    """Write one retrospective under the workspace lock."""
    ws.write_retrospective(note)
    return note


@workspace_locked
def record_feedback(ws: Workspace, note: Feedback) -> Feedback:
    """Write one feedback note under the workspace lock."""
    ws.write_feedback(note)
    return note
