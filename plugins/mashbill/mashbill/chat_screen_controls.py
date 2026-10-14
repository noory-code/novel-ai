"""Render the controls the viewer has on screen for the coach's turn context.

A coach that does not know the screen guesses at it, and once told a person to
look at a display the canvas did not have (novel-workspace O-00000136). The
viewer reports the labels of the controls it renders with its live context
(``viewer_context``); this module turns them into one ``[Screen controls]``
line. The labels are the viewer's own wording; the engine adds none.
"""

from __future__ import annotations

import time
from pathlib import Path

from mashbill.viewer_context import read_viewer_context


def render_screen_controls(plot_root: Path) -> str:
    """The ``[Screen controls]`` line, or ``""`` without a live viewer that reported controls."""
    context = read_viewer_context(plot_root, now=time.time())
    controls = context.get("controls") or []
    if not context.get("has_viewer") or not controls:
        return ""
    return (
        f"[Screen controls] Buttons on the canvas: {', '.join(controls)}. When pointing to a "
        "canvas button or display, name only these; the canvas has no other."
    )
