"""Render the Services-owned description for a feature chat turn."""

from __future__ import annotations

import re
from pathlib import Path

from mashbill.canvas_io import read_canvas
from mashbill.models_actors import FeatureNode
from mashbill.workspace import enumerate_projects

# One item per sentence or line: a sentence ends at . ! ? (or their full-width
# forms) followed by whitespace, so "1.5" stays inside its item.
_ITEM_BREAK_RE = re.compile(r"(?<=[.!?。！？])\s+|\s*[\r\n]+\s*")

_ITEM_GUIDE = (
    "Each numbered item is a step a canvas holds: draft it in the flow where its "
    "wording places it, and keep an ending it does not state open on that step."
)


def _description_items(proposed: str) -> list[str]:
    """Split a description into sentence items with internal whitespace collapsed."""
    items = (" ".join(part.split()) for part in _ITEM_BREAK_RE.split(proposed.strip()))
    return [item for item in items if item]


def _services_feature(plot_root: Path, project_id: str, feature_id: str) -> FeatureNode | None:
    try:
        canvas = read_canvas(plot_root, project_id, "services")
    except Exception:  # noqa: BLE001 — absent or invalid Services canvas gives no context
        return None
    for node in canvas.nodes:
        if isinstance(node, FeatureNode) and node.id == feature_id:
            return node
    return None


def feature_description_items(plot_root: Path, project_id: str, feature_id: str) -> list[str]:
    """The numbered items of a feature's Services description, in order (1-based)."""
    node = _services_feature(plot_root, project_id, feature_id)
    return _description_items(node.proposed) if node is not None else []


def render_feature_description(plot_root: Path, scope: str) -> str:
    """Return the matching Services node's description for a feature scope."""
    base, separator, feature_id = scope.partition(":")
    if base != "feature" or not separator or not feature_id:
        return ""
    projects = enumerate_projects(plot_root)
    if not projects:
        return ""
    node = _services_feature(plot_root, projects[0].id, feature_id)
    if node is None:
        return ""
    items = _description_items(node.proposed)
    if not items:
        return ""
    numbered = "\n".join(f"{index}. {item}" for index, item in enumerate(items, start=1))
    return f'[Feature description] "{node.label}" ({feature_id}). {_ITEM_GUIDE}\n{numbered}'
