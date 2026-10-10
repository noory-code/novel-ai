"""Render the Services-owned description for a feature chat turn."""

from __future__ import annotations

from pathlib import Path

from mashbill.canvas_io import read_canvas
from mashbill.workspace import enumerate_projects


def render_feature_description(plot_root: Path, scope: str) -> str:
    """Return the matching Services node's description for a feature scope."""
    base, separator, feature_id = scope.partition(":")
    if base != "feature" or not separator or not feature_id:
        return ""
    projects = enumerate_projects(plot_root)
    if not projects:
        return ""
    try:
        canvas = read_canvas(plot_root, projects[0].id, "services")
    except Exception:  # noqa: BLE001 — absent or invalid Services canvas gives no context
        return ""
    for node in canvas.nodes:
        if node.kind == "feature" and node.id == feature_id and node.proposed.strip():
            proposed = " ".join(node.proposed.split())
            return f'[Feature description] "{node.label}" ({feature_id}): {proposed}'
    return ""
