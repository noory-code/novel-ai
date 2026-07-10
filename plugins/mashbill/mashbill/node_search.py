"""Project-wide node name search — the "이름" context entry point (D-2026-06-20-P).

The context entry-point chain is selection → map → **name** → (last) semantic
search. Selection + map are injected per turn; this lets the agent jump to a node
it knows by name but isn't on the active canvas. It is a title/id index over node
labels — a plain substring scan, NOT vector search: the data is already a graph,
so similarity search is unnecessary until text drifts outside it (D-2026-06-20-P
§1.2; vector is a later option behind the same context-provider seam).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mashbill.canvas_io import list_feature_details, read_canvas
from mashbill.models_canvas import CanvasDoc, CanvasKind

# How many label matches to return before truncating, so a broad query on a
# large project can't blow the context window.
SEARCH_LIMIT = 20

_SINGLETON_CANVASES: tuple[CanvasKind, ...] = ("foundation", "actors", "services", "entities")


def search_nodes(
    plot_root: Path, project_id: str, query: str, *, limit: int = SEARCH_LIMIT
) -> list[dict[str, Any]]:
    """Find nodes whose label contains ``query`` (case-insensitive) across every
    canvas of the project. Returns ``{id, kind, label, canvas}`` dicts (``canvas``
    is the scope string — ``foundation`` … or ``feature:<id>``), capped at
    ``limit``. A blank query returns ``[]``.
    """
    needle = query.strip().lower()
    if not needle:
        return []
    hits: list[dict[str, Any]] = []
    for kind in _SINGLETON_CANVASES:
        _collect(hits, _safe_read(plot_root, project_id, kind), kind, needle)
    for feature_id in list_feature_details(plot_root, project_id):
        canvas = _safe_read(plot_root, project_id, "feature", feature_id)
        _collect(hits, canvas, f"feature:{feature_id}", needle)
    return hits[:limit]


def _collect(hits: list[dict[str, Any]], canvas: CanvasDoc | None, scope: str, needle: str) -> None:
    if canvas is None:
        return
    for node in canvas.nodes:
        if needle in node.label.lower():
            hits.append({"id": node.id, "kind": node.kind, "label": node.label, "canvas": scope})


def _safe_read(
    plot_root: Path, project_id: str, kind: CanvasKind, service_id: str | None = None
) -> CanvasDoc | None:
    """``read_canvas`` that swallows every error to ``None`` — a missing / corrupt
    canvas must not break a search."""
    try:
        return read_canvas(plot_root, project_id, kind, service_id)
    except Exception:  # noqa: BLE001 — graceful: a bad canvas just yields no hits
        return None
