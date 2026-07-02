"""Reference-slot wiring — assign a node's ``ref_*`` ids (D-2026-07-02-N).

Reference fields are deliberately NOT writable through ``update_node``'s
free-text allow-list (a coach could repoint them with prose, D-2026-06-26-D
red-team) — but the benchmark showed the opposite hole: NO tool could set them
at all, so every service's who-takes-part / what-values / what-tone slots
stayed empty in every run. ``set_node_references`` assigns them explicitly:
only allow-listed ref fields per kind, and every referenced id must exist on
its home canvas (Fail Fast) — same read → merge → re-validate whole doc →
atomic write shape as ``update_node``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mashbill.canvas_io import read_canvas, write_canvas
from mashbill.models import CanvasDoc, CanvasKind
from mashbill.models_union import SketchNodeAdapter

# Which ref fields a kind carries, and each field's (home canvas, expected kind).
_REF_FIELDS: dict[str, dict[str, tuple[str, str]]] = {
    "service": {
        "ref_actor_ids": ("actors", "actor"),
        "ref_value_ids": ("foundation", "core_value"),
        "ref_identity_ids": ("foundation", "identity"),
    },
    "step": {"ref_entity_ids": ("entities", "entity")},
    "feature": {"ref_entity_ids": ("entities", "entity")},
}


def set_node_references(
    plot_root: Path,
    project_id: str,
    canvas_kind: CanvasKind,
    node_id: str,
    refs: dict[str, list[str]],
    service_id: str | None = None,
) -> dict[str, Any]:
    """Assign ``refs`` (e.g. ``{"ref_actor_ids": ["a1"]}``) on ``node_id``."""
    canvas = read_canvas(plot_root, project_id, canvas_kind, service_id)
    node = next((n for n in canvas.nodes if n.id == node_id), None)
    if node is None:
        raise ValueError(f"node not on the {canvas_kind!r} canvas: {node_id!r}")
    allowed = _REF_FIELDS.get(node.kind, {})
    for field in refs:
        if field not in allowed:
            raise ValueError(f"{field!r} is not a reference field of kind {node.kind!r}")
    for field, ids in refs.items():
        home_canvas, expected_kind = allowed[field]
        home = read_canvas(plot_root, project_id, home_canvas)  # type: ignore[arg-type]
        valid = {n.id for n in home.nodes if n.kind == expected_kind}
        for ref_id in ids:
            if ref_id not in valid:
                raise ValueError(
                    f"{field}: {ref_id!r} is not a {expected_kind!r} on the "
                    f"{home_canvas!r} canvas"
                )
    merged = {**node.model_dump(), **refs}
    new_node = SketchNodeAdapter.validate_python(merged)
    updated = CanvasDoc.model_validate(
        canvas.model_copy(
            update={"nodes": [new_node if n.id == node_id else n for n in canvas.nodes]}
        ).model_dump(by_alias=True)
    )
    write_canvas(plot_root, project_id, updated)
    return {"node": new_node.model_dump(by_alias=True)}
