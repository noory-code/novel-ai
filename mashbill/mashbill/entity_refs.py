"""Entity reverse-index — the "어디서 쓰이나" back-reference (D-2026-06-20-Q).

The entities canvas is an AI-maintained derived data map; its value is letting
the user see *where each data object is used* without ERD work. The forward
reference is ``step.ref_entity_ids`` (chips on the action). This module derives
the reverse: which features (and which of their steps) reference an entity.

Read-only projection — nothing is authored here. It must scan **all** feature
detail canvases on disk (the viewer's canvas cache holds only loaded canvases,
so a complete back-ref can't be computed client-side).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mashbill.canvas_io import list_feature_details, read_canvas


def entity_usage(plot_root: Path, project_id: str, entity_id: str) -> list[dict[str, Any]]:
    """Features whose ``step`` nodes reference ``entity_id``.

    Returns one entry per referencing feature::

        {"feature_id": str, "feature_label": str, "steps": [step_label, ...]}

    Features with no referencing step are omitted; the list is ordered by
    ``list_feature_details`` (stable / sorted)."""
    usages: list[dict[str, Any]] = []
    for feature_id in list_feature_details(plot_root, project_id):
        canvas = read_canvas(plot_root, project_id, "feature", service_id=feature_id)
        steps = [
            (n.label or n.id)
            for n in canvas.nodes
            if n.kind == "step" and entity_id in getattr(n, "ref_entity_ids", [])
        ]
        if not steps:
            continue
        # The feature root node carries id == feature_id (is_root marks the
        # canvas anchor, not the feature — detail_sync seeds it is_root=False).
        feature_label = next(
            (n.label for n in canvas.nodes if n.id == feature_id and n.label), feature_id
        )
        usages.append({"feature_id": feature_id, "feature_label": feature_label, "steps": steps})
    return usages
