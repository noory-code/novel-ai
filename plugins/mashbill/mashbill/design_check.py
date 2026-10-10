"""Coach design-check writes and automatic recheck transitions."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from mashbill.canvas_view import read_canvas_files, write_canvas_files
from mashbill.models_actors import DesignCheck, DesignCheckState, FeatureNode, ServiceNode
from mashbill.models_canvas import CanvasDoc
from mashbill.models_union import SketchNode
from mashbill.service_features import service_feature_ids
from mashbill.storage import _canvas_file

_SERVICE_CONTENT_FIELDS = (
    "label",
    "problem",
    "value_created",
    "ref_actor_ids",
    "ref_value_ids",
    "ref_identity_ids",
)
_FEATURE_CONTENT_FIELDS = ("label", "proposed", "ref_actor_ids")


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _rechecked(check: DesignCheck | None, updated_at: str) -> DesignCheck | None:
    if check is None or check.state in ("unchecked", "recheck"):
        return check
    return check.model_copy(update={"state": "recheck", "updated_at": updated_at})


def _content(node: ServiceNode | FeatureNode, fields: tuple[str, ...]) -> tuple[Any, ...]:
    return tuple(getattr(node, field) for field in fields)


def _nodes(canvas: CanvasDoc, kind: str) -> dict[str, ServiceNode | FeatureNode]:
    return {
        node.id: node
        for node in canvas.nodes
        if isinstance(node, (ServiceNode, FeatureNode)) and node.kind == kind
    }


def _service_feature_pairs(canvas: CanvasDoc) -> set[tuple[str, str]]:
    return {
        (service_id, feature_id)
        for service_id, feature_ids in service_feature_ids(canvas).items()
        for feature_id in feature_ids
    }


def _mark_nodes(
    canvas: CanvasDoc,
    service_ids: set[str],
    feature_ids: set[str],
    updated_at: str,
) -> tuple[CanvasDoc, set[str]]:
    changed_features: set[str] = set()
    changed = False
    nodes: list[SketchNode] = []
    for node in canvas.nodes:
        should_mark = (node.kind == "service" and node.id in service_ids) or (
            node.kind == "feature" and node.id in feature_ids
        )
        if not should_mark or not isinstance(node, (ServiceNode, FeatureNode)):
            nodes.append(node)
            continue
        design_check = _rechecked(node.design_check, updated_at)
        if design_check == node.design_check:
            nodes.append(node)
            continue
        changed = True
        if node.kind == "feature":
            changed_features.add(node.id)
        nodes.append(node.model_copy(update={"design_check": design_check}))
    if not changed:
        return canvas, changed_features
    return CanvasDoc.model_validate(
        canvas.model_copy(update={"nodes": nodes}).model_dump(by_alias=True)
    ), changed_features


def _without_design_check(canvas: CanvasDoc) -> dict[str, Any]:
    raw = canvas.model_dump(by_alias=True)
    for node in raw["nodes"]:
        if node.get("kind") == "feature":
            node.pop("design_check", None)
    return raw


def _preserve_omitted_checks(before: CanvasDoc, incoming: CanvasDoc) -> CanvasDoc:
    """Keep checks when an older client writes no ``design_check`` field."""
    previous = {
        node.id: node.design_check
        for node in before.nodes
        if isinstance(node, (ServiceNode, FeatureNode)) and node.design_check is not None
    }
    if not previous:
        return incoming
    changed = False
    nodes: list[SketchNode] = []
    for node in incoming.nodes:
        if (
            isinstance(node, (ServiceNode, FeatureNode))
            and node.design_check is None
            and node.id in previous
        ):
            nodes.append(node.model_copy(update={"design_check": previous[node.id]}))
            changed = True
        else:
            nodes.append(node)
    if not changed:
        return incoming
    return CanvasDoc.model_validate(
        incoming.model_copy(update={"nodes": nodes}).model_dump(by_alias=True)
    )


def _load_canvas(path: Path) -> CanvasDoc | None:
    try:
        return CanvasDoc.model_validate(read_canvas_files(path))
    except (FileNotFoundError, ValueError, ValidationError):
        return None


def _detail_update(
    plot_root: Path, project_id: str, feature_id: str, updated_at: str
) -> tuple[Path, dict[str, Any]] | None:
    path = _canvas_file(plot_root, project_id, "feature", feature_id)
    detail = _load_canvas(path)
    if detail is None:
        return None
    marked, _ = _mark_nodes(detail, set(), {feature_id}, updated_at)
    if marked == detail:
        return None
    return path, marked.model_dump(by_alias=True)


def prepare_rechecks(
    plot_root: Path,
    project_id: str,
    before: CanvasDoc | None,
    incoming: CanvasDoc,
) -> tuple[CanvasDoc, list[tuple[Path, dict[str, Any]]]]:
    """Apply all automatic recheck rules before one central canvas write."""
    if before is None:
        return incoming, []
    incoming = _preserve_omitted_checks(before, incoming)
    stamp = _now()
    related: list[tuple[Path, dict[str, Any]]] = []

    if incoming.canvas_kind == "services":
        old_services = _nodes(before, "service")
        new_services = _nodes(incoming, "service")
        old_features = _nodes(before, "feature")
        new_features = _nodes(incoming, "feature")
        old_pairs = _service_feature_pairs(before)
        new_pairs = _service_feature_pairs(incoming)

        service_ids = {
            node_id
            for node_id in old_services.keys() & new_services.keys()
            if _content(old_services[node_id], _SERVICE_CONTENT_FIELDS)
            != _content(new_services[node_id], _SERVICE_CONTENT_FIELDS)
        }
        feature_ids = {
            node_id
            for node_id in old_features.keys() & new_features.keys()
            if _content(old_features[node_id], _FEATURE_CONTENT_FIELDS)
            != _content(new_features[node_id], _FEATURE_CONTENT_FIELDS)
        }
        changed_feature_set = old_features.keys() ^ new_features.keys()
        affected_pairs = {
            pair
            for pair in old_pairs | new_pairs
            if pair in old_pairs ^ new_pairs
            or pair[1] in feature_ids
            or pair[1] in changed_feature_set
        }
        service_ids.update(service_id for service_id, _ in affected_pairs)
        incoming, changed_features = _mark_nodes(incoming, service_ids, feature_ids, stamp)
        for changed_feature_id in changed_features:
            update = _detail_update(plot_root, project_id, changed_feature_id, stamp)
            if update is not None:
                related.append(update)
        return incoming, related

    if incoming.canvas_kind != "feature" or _without_design_check(before) == _without_design_check(
        incoming
    ):
        return incoming, []

    feature_id = incoming.feature_ref
    assert feature_id is not None
    incoming, _ = _mark_nodes(incoming, set(), {feature_id}, stamp)
    overview_path = _canvas_file(plot_root, project_id, "services")
    overview = _load_canvas(overview_path)
    if overview is None:
        return incoming, []
    parent_services = {
        service_id
        for service_id, child_id in _service_feature_pairs(overview)
        if child_id == feature_id
    }
    overview, _ = _mark_nodes(overview, parent_services, {feature_id}, stamp)
    related.append((overview_path, overview.model_dump(by_alias=True)))
    return incoming, related


def set_design_check(
    project_path: str,
    project_id: str,
    node_id: str,
    state: DesignCheckState,
    found: int | None = None,
    remaining: int | None = None,
) -> dict[str, Any]:
    """Record a coach check on a service or feature.

    Call with ``checking`` when the coach starts a check and ``checked`` with
    ``found`` / ``remaining`` when it finishes. Never set ``checked`` for a
    check the coach did not run.
    """
    from mashbill.canvas_io import read_canvas, write_canvas
    from mashbill.tool_log import record_tool_call
    from mashbill.workspace import resolve_plot_root

    plot_root = resolve_plot_root(project_path)
    overview = read_canvas(plot_root, project_id, "services")
    target = next((node for node in overview.nodes if node.id == node_id), None)
    if target is None:
        raise ValueError(f"design-check node not found on services canvas: {node_id!r}")
    if not isinstance(target, (ServiceNode, FeatureNode)):
        raise ValueError(
            "set_design_check only supports service and feature nodes; "
            f"got {target.kind!r} for {node_id!r}"
        )
    check = DesignCheck(
        state=state,
        found=found,
        remaining=remaining,
        updated_at=_now(),
    )
    changed = target.model_copy(update={"design_check": check})
    nodes = [changed if node.id == node_id else node for node in overview.nodes]
    saved = write_canvas(
        plot_root,
        project_id,
        CanvasDoc.model_validate(
            overview.model_copy(update={"nodes": nodes}).model_dump(by_alias=True)
        ),
    )
    saved_node = next(node for node in saved.nodes if node.id == node_id)

    if isinstance(target, FeatureNode):
        detail_path = _canvas_file(plot_root, project_id, "feature", node_id)
        detail = _load_canvas(detail_path)
        if detail is not None:
            detail_nodes = [
                node.model_copy(update={"design_check": check})
                if node.id == node_id and isinstance(node, FeatureNode)
                else node
                for node in detail.nodes
            ]
            write_canvas(
                plot_root,
                project_id,
                CanvasDoc.model_validate(
                    detail.model_copy(update={"nodes": detail_nodes}).model_dump(by_alias=True)
                ),
            )
    record_tool_call("set_design_check", project_id=project_id, canvas="services", node_id=node_id)
    return {"node": saved_node.model_dump(by_alias=True)}


def write_related(updates: list[tuple[Path, dict[str, Any]]]) -> None:
    """Persist related-canvas recheck updates after the primary write succeeds."""
    for path, payload in updates:
        write_canvas_files(path, payload)
