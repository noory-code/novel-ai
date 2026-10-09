"""Grouped node lines for the coach's services canvas map."""

from __future__ import annotations

from collections.abc import Callable

from mashbill.models_canvas import CanvasDoc
from mashbill.models_union import SketchNode
from mashbill.service_features import service_feature_ids


def render_services_map_lines(
    canvas: CanvasDoc, cap: int, render_line: Callable[[SketchNode, bool], str]
) -> list[str]:
    """Render service children in canvas order and count distinct unseen nodes."""
    children = service_feature_ids(canvas)
    parented_feature_ids = {feature_id for ids in children.values() for feature_id in ids}
    by_id = {node.id: node for node in canvas.nodes}
    emitted_ids: set[str] = set()
    emitted_count = 0
    lines: list[str] = []

    def emit_node(node: SketchNode, nested: bool = False) -> bool:
        nonlocal emitted_count
        if emitted_count >= cap:
            return False
        lines.append(render_line(node, nested))
        emitted_ids.add(node.id)
        emitted_count += 1
        return True

    for node in canvas.nodes:
        if node.kind == "feature":
            continue
        if not emit_node(node):
            break
        if node.kind == "service":
            for feature_id in children[node.id]:
                if not emit_node(by_id[feature_id], nested=True):
                    break

    orphans = [
        node
        for node in canvas.nodes
        if node.kind == "feature" and node.id not in parented_feature_ids
    ]
    if orphans and emitted_count < cap:
        lines.append("서비스 없음:")
        for node in orphans:
            if not emit_node(node):
                break
    if omitted := len(canvas.nodes) - len(emitted_ids):
        lines.append(f"…and {omitted} more")
    return lines
