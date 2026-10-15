"""Render the controls the viewer has on screen for the coach's turn context.

A coach that does not know the screen guesses at it: it once told a person to
look at a display the canvas did not have (novel-workspace O-00000136), and it
asked a person where a feature's flow canvas was (O-00000146). The viewer
reports the labels of what it renders with its live context
(``viewer_context``) in three groups: the canvas tabs, the buttons on the
canvas, and the buttons outside the canvas (beside the tabs, in an open panel).
This module turns them into one ``[Screen controls]`` line. The labels are the
viewer's own wording; the engine adds none.

A button that shows only an icon reaches the engine with its accessible name
marked " (icon)" (the viewer's ``ICON_ONLY_MARK``): the person sees no words,
so the line tells the coach to point to it by its place and look.

The tabs and the canvas buttons are always rendered, so the line tells the
coach to name only those. The buttons outside the canvas come and go with the
selection (a service's publish button shows only while that service's panel is
open), so the line lists them as on screen now without forbidding the others.
"""

from __future__ import annotations

import time
from pathlib import Path

from mashbill.viewer_context import read_viewer_context

ICON_ONLY_MARK = " (icon)"
_ICON_NOTE = (
    "A label marked (icon) is a button that shows only an icon; its name appears "
    "when the pointer rests on it. Point to it by where it is and what it looks like, "
    "and do not say the word (icon)."
)


def _guard(has_tabs: bool, has_canvas: bool) -> str:
    if has_tabs and has_canvas:
        return (
            "When pointing to a tab or to a canvas button or display, name only these; "
            "there are no other tabs, and the canvas has no other."
        )
    if has_tabs:
        return "When pointing to a tab, name only these; there are no other tabs."
    return "When pointing to a canvas button or display, name only these; the canvas has no other."


def render_screen_controls(plot_root: Path) -> str:
    """The ``[Screen controls]`` line, or ``""`` without a live viewer that reported controls."""
    context = read_viewer_context(plot_root, now=time.time())
    if not context.get("has_viewer"):
        return ""
    tabs = context.get("tabs") or []
    controls = context.get("controls") or []
    page = context.get("page_controls") or []
    if not tabs and not controls and not page:
        return ""
    parts = ["[Screen controls]"]
    if tabs:
        parts.append(f"Canvas tabs: {', '.join(tabs)}.")
    if controls:
        parts.append(f"Buttons on the canvas: {', '.join(controls)}.")
    if tabs or controls:
        parts.append(_guard(bool(tabs), bool(controls)))
    if page:
        parts.append(f"Buttons beside the tabs or in an open panel right now: {', '.join(page)}.")
    if any(str(label).endswith(ICON_ONLY_MARK) for label in (*controls, *page)):
        parts.append(_ICON_NOTE)
    return " ".join(parts)
