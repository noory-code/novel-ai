"""Service-to-feature membership on the services canvas."""

from __future__ import annotations

from mashbill.models_canvas import CanvasDoc


def service_feature_ids(canvas: CanvasDoc) -> dict[str, list[str]]:
    """Map each service to feature targets of its outgoing edges, in canvas order."""
    service_ids = {node.id for node in canvas.nodes if node.kind == "service"}
    feature_ids = {node.id for node in canvas.nodes if node.kind == "feature"}
    targets: dict[str, set[str]] = {service_id: set() for service_id in service_ids}
    for edge in canvas.edges:
        if edge.source in service_ids and edge.target in feature_ids:
            targets[edge.source].add(edge.target)
    return {
        node.id: [feature.id for feature in canvas.nodes if feature.id in targets[node.id]]
        for node in canvas.nodes
        if node.kind == "service"
    }
