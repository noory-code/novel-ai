"""Coach design-check writes and automatic recheck transitions."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from mashbill.canvas_view import read_canvas_files, write_canvas_files
from mashbill.models_actors import (
    CoachDesignCheckState,
    DesignCheck,
    FeatureNode,
    ServiceNode,
)
from mashbill.models_canvas import CanvasDoc
from mashbill.models_composition import DecisionNode, StepNode
from mashbill.models_union import SketchNode
from mashbill.service_features import service_feature_ids
from mashbill.storage import _canvas_file

_SERVICE_CONTENT_FIELDS = ("problem", "value_created")
_FEATURE_CONTENT_FIELDS = ("label", "proposed")


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _rechecked(
    check: DesignCheck | None, updated_at: str, changed: list[str]
) -> DesignCheck | None:
    # Only a finished check reopens; a check in progress covers the edits made
    # during it (W-00000489, newcomer walk 5).
    if check is None or check.state == "unchecked":
        return check
    merged = list(dict.fromkeys([*check.changed, *changed]))
    if check.state == "checking":
        # The check in progress keeps its state; the new change joins its list.
        if merged == check.changed:
            return check
        return check.model_copy(update={"updated_at": updated_at, "changed": merged})
    return check.model_copy(
        update={"state": "recheck", "updated_at": updated_at, "changed": merged}
    )


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


def _name(node: SketchNode) -> str:
    return node.label or node.id


def _flow_changes(before: CanvasDoc, incoming: CanvasDoc) -> list[str]:
    old_nodes = {n.id: n for n in before.nodes if isinstance(n, (StepNode, DecisionNode))}
    new_nodes = {n.id: n for n in incoming.nodes if isinstance(n, (StepNode, DecisionNode))}
    changed = [
        _name(new_nodes[node_id] if node_id in new_nodes else old_nodes[node_id])
        for node_id in sorted(old_nodes.keys() ^ new_nodes.keys())
    ]
    fields = ("label", "body", "outcome", "polarity")
    for node_id in sorted(old_nodes.keys() & new_nodes.keys()):
        old, new = old_nodes[node_id], new_nodes[node_id]
        if old.kind != new.kind or any(
            getattr(old, f, None) != getattr(new, f, None) for f in fields
        ):
            changed.append(_name(new))
    old_edges = {e.id: e for e in before.edges}
    new_edges = {e.id: e for e in incoming.edges}
    for edge_id in sorted(old_edges.keys() | new_edges.keys()):
        old_edge, new_edge = old_edges.get(edge_id), new_edges.get(edge_id)
        if (
            old_edge is None
            or new_edge is None
            or (old_edge.source, old_edge.target, old_edge.label)
            != (new_edge.source, new_edge.target, new_edge.label)
        ):
            edge = new_edge or old_edge
            assert edge is not None
            changed.append(edge.label or edge.id)
    return list(dict.fromkeys(changed))


def _mark_nodes(
    canvas: CanvasDoc,
    service_changes: dict[str, list[str]],
    feature_changes: dict[str, list[str]],
    updated_at: str,
) -> tuple[CanvasDoc, set[str]]:
    changed_features: set[str] = set()
    changed = False
    nodes: list[SketchNode] = []
    for node in canvas.nodes:
        should_mark = (node.kind == "service" and node.id in service_changes) or (
            node.kind == "feature" and node.id in feature_changes
        )
        if not should_mark or not isinstance(node, (ServiceNode, FeatureNode)):
            nodes.append(node)
            continue
        names = (
            service_changes.get(node.id, [])
            if node.kind == "service"
            else feature_changes.get(node.id, [])
        )
        design_check = _rechecked(node.design_check, updated_at, names)
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


def sent_check_changes(before: CanvasDoc | None, incoming: CanvasDoc) -> list[str]:
    """Ids of nodes whose sent ``design_check`` differs from the stored one.

    An omitted check (``None``) is not a change; it is carried (W-00000430).
    """
    previous = {
        node.id: node.design_check
        for node in (before.nodes if before is not None else [])
        if isinstance(node, (ServiceNode, FeatureNode))
    }
    return [
        str(node.id)
        for node in incoming.nodes
        if isinstance(node, (ServiceNode, FeatureNode))
        and node.design_check is not None
        and node.design_check != previous.get(node.id)
    ]


def _carry_stored_checks(before: CanvasDoc | None, incoming: CanvasDoc) -> CanvasDoc:
    """Replace every incoming ``design_check`` with the stored one (W-00000430).

    A check is written only by ``set_design_check`` and the engine's recheck
    rules. A whole-canvas write — the coach's ``update_canvas``, a viewer
    echoing a stale copy, an older client that omits the field — keeps what is
    stored; a node the store has no check for gets none.
    """
    previous = {
        node.id: node.design_check
        for node in (before.nodes if before is not None else [])
        if isinstance(node, (ServiceNode, FeatureNode))
    }
    changed = False
    nodes: list[SketchNode] = []
    for node in incoming.nodes:
        if isinstance(node, (ServiceNode, FeatureNode)):
            stored = previous.get(node.id)
            if node.design_check != stored:
                node = node.model_copy(update={"design_check": stored})
                changed = True
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
    plot_root: Path, project_id: str, feature_id: str, updated_at: str, changed: list[str]
) -> tuple[Path, dict[str, Any]] | None:
    path = _canvas_file(plot_root, project_id, "feature", feature_id)
    detail = _load_canvas(path)
    if detail is None:
        return None
    marked, _ = _mark_nodes(detail, {}, {feature_id: changed}, updated_at)
    if marked == detail:
        return None
    return path, marked.model_dump(by_alias=True)


def prepare_rechecks(
    plot_root: Path,
    project_id: str,
    before: CanvasDoc | None,
    incoming: CanvasDoc,
    *,
    keep_incoming_checks: bool = False,
) -> tuple[CanvasDoc, list[tuple[Path, dict[str, Any]]]]:
    """Apply all automatic recheck rules before one central canvas write.

    ``keep_incoming_checks`` is for ``write_design_check`` alone; every other
    write carries the stored checks.
    """
    if not keep_incoming_checks:
        incoming = _carry_stored_checks(before, incoming)
    if before is None:
        return incoming, []
    stamp = _now()
    related: list[tuple[Path, dict[str, Any]]] = []

    if incoming.canvas_kind == "services":
        old_services = _nodes(before, "service")
        new_services = _nodes(incoming, "service")
        old_features = _nodes(before, "feature")
        new_features = _nodes(incoming, "feature")
        old_pairs = _service_feature_pairs(before)
        new_pairs = _service_feature_pairs(incoming)

        service_changes: dict[str, list[str]] = {}
        feature_changes: dict[str, list[str]] = {}
        for node_id in sorted(old_services.keys() & new_services.keys()):
            if _content(old_services[node_id], _SERVICE_CONTENT_FIELDS) != _content(
                new_services[node_id], _SERVICE_CONTENT_FIELDS
            ):
                service_changes[node_id] = [_name(new_services[node_id])]
        for node_id in sorted(old_features.keys() & new_features.keys()):
            if _content(old_features[node_id], _FEATURE_CONTENT_FIELDS) != _content(
                new_features[node_id], _FEATURE_CONTENT_FIELDS
            ):
                feature_changes[node_id] = [_name(new_features[node_id])]
        for service_id, feature_id in sorted(old_pairs | new_pairs):
            if (service_id, feature_id) in old_pairs ^ new_pairs or feature_id in feature_changes:
                feature = new_features.get(feature_id) or old_features.get(feature_id)
                if feature is not None:
                    service_changes.setdefault(service_id, []).append(_name(feature))
        incoming, changed_features = _mark_nodes(incoming, service_changes, feature_changes, stamp)
        for changed_feature_id in changed_features:
            update = _detail_update(
                plot_root,
                project_id,
                changed_feature_id,
                stamp,
                feature_changes[changed_feature_id],
            )
            if update is not None:
                related.append(update)
        return incoming, related

    if incoming.canvas_kind != "feature":
        return incoming, []

    changes = _flow_changes(before, incoming)
    if not changes:
        return incoming, []

    detail_feature_id = incoming.feature_ref
    assert detail_feature_id is not None
    incoming, _ = _mark_nodes(incoming, {}, {detail_feature_id: changes}, stamp)
    overview_path = _canvas_file(plot_root, project_id, "services")
    overview = _load_canvas(overview_path)
    if overview is None:
        return incoming, []
    overview, _ = _mark_nodes(overview, {}, {detail_feature_id: changes}, stamp)
    related.append((overview_path, overview.model_dump(by_alias=True)))
    return incoming, related


def set_design_check(
    project_path: str,
    project_id: str,
    node_id: str,
    state: CoachDesignCheckState,
    found: int | None = None,
    remaining: int | None = None,
) -> dict[str, Any]:
    """Record a coach check on a service or feature.

    Call with ``checking`` when the coach starts a check and ``checked`` with
    ``found`` / ``remaining`` when it finishes. Never set ``checked`` for a
    check the coach did not run. ``recheck`` and ``unchecked`` belong to the
    engine and are refused.
    """
    from mashbill.canvas_io import read_canvas
    from mashbill.chat_scope_env import refuse_foreign_check
    from mashbill.tool_log import record_tool_call
    from mashbill.workspace import resolve_plot_root

    if state not in ("checking", "checked"):
        raise ValueError(
            f"a coach records only checking or checked; got {state!r} "
            "(the engine sets recheck and unchecked)"
        )
    plot_root = resolve_plot_root(project_path)
    overview = read_canvas(plot_root, project_id, "services")
    target = next((node for node in overview.nodes if node.id == node_id), None)
    if target is not None:
        # W-00000489 — a check belongs to the conversation that runs it.
        refuse_foreign_check(node_id, target.kind)
    # A re-check in progress keeps the list of what changed; a finished check clears it.
    carried = (
        list(target.design_check.changed)
        if state == "checking"
        and isinstance(target, (ServiceNode, FeatureNode))
        and target.design_check is not None
        else []
    )
    check = DesignCheck(
        state=state, found=found, remaining=remaining, changed=carried, updated_at=_now()
    )
    saved_node = write_design_check(plot_root, project_id, node_id, check)
    record_tool_call("set_design_check", project_id=project_id, canvas="services", node_id=node_id)
    return {"node": saved_node.model_dump(by_alias=True)}


def write_design_check(
    plot_root: Path, project_id: str, node_id: str, check: DesignCheck
) -> ServiceNode | FeatureNode:
    """Store ``check`` on a service or feature, mirroring a feature's onto its flow canvas."""
    from mashbill.canvas_io import read_canvas, write_canvas

    overview = read_canvas(plot_root, project_id, "services")
    target = next((node for node in overview.nodes if node.id == node_id), None)
    if target is None:
        raise ValueError(f"design-check node not found on services canvas: {node_id!r}")
    if not isinstance(target, (ServiceNode, FeatureNode)):
        raise ValueError(
            "set_design_check only supports service and feature nodes; "
            f"got {target.kind!r} for {node_id!r}"
        )
    changed = target.model_copy(update={"design_check": check})
    nodes = [changed if node.id == node_id else node for node in overview.nodes]
    saved = write_canvas(
        plot_root,
        project_id,
        CanvasDoc.model_validate(
            overview.model_copy(update={"nodes": nodes}).model_dump(by_alias=True)
        ),
        design_checks_from_engine=True,
    )
    saved_node = next(node for node in saved.nodes if node.id == node_id)
    assert isinstance(saved_node, (ServiceNode, FeatureNode))

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
                design_checks_from_engine=True,
            )
    return saved_node


def feature_check(plot_root: Path, project_id: str, feature_id: str) -> DesignCheck | None:
    """The feature's current check as stored on the services canvas."""
    from mashbill.canvas_io import read_canvas

    overview = read_canvas(plot_root, project_id, "services")
    node = next((n for n in overview.nodes if n.id == feature_id), None)
    return node.design_check if isinstance(node, FeatureNode) else None


def write_related(updates: list[tuple[Path, dict[str, Any]]]) -> None:
    """Persist related-canvas recheck updates after the primary write succeeds."""
    for path, payload in updates:
        write_canvas_files(path, payload)
