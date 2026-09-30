"""MCP-callable draft operations and draft-aware node-write helpers."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from mashbill.blueprint_content import _canvas_design_content
from mashbill.chat_scope_env import effective_chat_scope
from mashbill.draft_store import read_draft
from mashbill.draft_store import record_applied_draft as persist_applied_draft
from mashbill.draft_store import record_draft as persist_draft
from mashbill.draft_store import resolve_draft as persist_resolution
from mashbill.draft_write_split import WriteFragment, normalize_draft_text, split_write_by_draft
from mashbill.field_policy import writable_node_fields
from mashbill.models_canvas import CanvasDoc, CanvasKind
from mashbill.models_draft import DraftCanvasKind, DraftDoc, ResolvedDraftStatus
from mashbill.workspace import resolve_plot_root

AUTO_DRAFT_RATIONALE = "Coach applied the change directly without recording a draft."
_CanvasFragmentValue = tuple[str, str, str | None]


def _draft_result(draft: DraftDoc) -> dict[str, Any]:
    return {"draft_id": draft.id, **draft.model_dump()}


def record_draft(
    project_path: str,
    project_id: str,
    canvas_kind: DraftCanvasKind,
    proposed_text: str,
    rationale: str,
    chat_scope: str = "",
    target_node_ids: list[str] | None = None,
    proposed_kind: str | None = None,
    service_id: str | None = None,
) -> dict[str, Any]:
    """Keep a concrete proposal shown to the person, separately from chat.

    Call for node text, a new node, or a new project name; ``rationale`` is one line on
    why, ``chat_scope`` comes from [Write target]. Project drafts have no nodes/kind/service.
    """
    plot_root = resolve_plot_root(project_path)
    draft = persist_draft(
        plot_root,
        project_id,
        canvas_kind,
        proposed_text,
        rationale,
        effective_chat_scope(chat_scope),
        target_node_ids,
        proposed_kind,
        service_id,
    )
    return _draft_result(draft)


def resolve_draft(
    project_path: str,
    project_id: str,
    draft_id: str,
    status: ResolvedDraftStatus,
    node_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Mark a proposal confirmed, edited, or rejected without deleting it.

    For ``confirmed`` or ``edited``, pass the ids of nodes that received the
    proposal. A later resolution is allowed and refreshes ``updated``.
    """
    plot_root = resolve_plot_root(project_path)
    return _draft_result(persist_resolution(plot_root, project_id, draft_id, status, node_ids))


def ensure_draft(plot_root: Path, project_id: str, draft_id: str) -> None:
    """Fail before a node write when the supplied draft does not exist."""
    read_draft(plot_root, project_id, draft_id)


def draft_matches_write(
    plot_root: Path,
    project_id: str,
    draft_id: str,
    canvas_kind: DraftCanvasKind,
    touched_node_ids: list[str],
    service_id: str | None = None,
    written_texts: list[str] | None = None,
) -> bool:
    """Return whether a supplied draft describes the successful write."""
    normalized_written_texts = [
        normalized for text in written_texts or [] if (normalized := normalize_draft_text(text))
    ]
    matching, _ = split_write_by_draft(
        plot_root,
        project_id,
        draft_id,
        canvas_kind,
        [
            WriteFragment(
                None,
                node_ids=tuple(touched_node_ids),
                written_texts=tuple(written_texts or ()),
                matches_without_text=not normalized_written_texts,
            )
        ],
        service_id,
    )
    return bool(matching)


def confirm_draft(plot_root: Path, project_id: str, draft_id: str, node_ids: list[str]) -> None:
    """Link a successful write back to its draft."""
    persist_resolution(plot_root, project_id, draft_id, "confirmed", node_ids)


def finish_write_draft(
    plot_root: Path,
    project_id: str,
    draft_id: str | None,
    canvas_kind: CanvasKind,
    proposed_text: str,
    proposed_kind: str | None,
    target_node_ids: list[str],
    resolved_node_ids: list[str],
    chat_scope: str,
    service_id: str | None = None,
    written_texts: list[str] | None = None,
    design_content_changed: bool = True,
) -> str | None:
    """Confirm the supplied draft or record one successful MCP write."""
    if not design_content_changed:
        return _no_design_content_warning(draft_id)
    if draft_id is not None and draft_matches_write(
        plot_root,
        project_id,
        draft_id,
        canvas_kind,
        target_node_ids,
        service_id,
        written_texts,
    ):
        confirm_draft(plot_root, project_id, draft_id, resolved_node_ids)
        return None
    persist_applied_draft(
        plot_root,
        project_id,
        canvas_kind,
        proposed_text,
        AUTO_DRAFT_RATIONALE,
        effective_chat_scope(chat_scope),
        target_node_ids,
        proposed_kind,
        service_id,
        resolved_node_ids,
    )
    if draft_id is None:
        return None
    return draft_mismatch_warning(draft_id)


def finish_node_write_draft(
    plot_root: Path,
    project_id: str,
    draft_id: str | None,
    canvas_kind: CanvasKind,
    fields: dict[str, Any] | None,
    write_result: dict[str, Any],
    chat_scope: str,
    service_id: str | None,
    additional_touched_node_ids: list[str] | None = None,
    before_node: dict[str, Any] | None = None,
) -> str | None:
    """Confirm the supplied draft or create the fallback for a successful write."""
    node_id = str(write_result["node"]["id"])
    touched_node_ids = [node_id, *(additional_touched_node_ids or [])]
    node = write_result["node"]
    rejected = set(write_result["rejected_fields"])
    written_fields = [name for name in (fields or {}) if name not in rejected]
    if before_node is not None and all(
        before_node.get(name) == node.get(name) for name in written_fields
    ):
        return _no_design_content_warning(draft_id)
    has_written_fields = bool(written_fields)
    if not written_fields:
        written_fields = ["label"]
    fragments = [
        WriteFragment(
            name,
            node_ids=tuple(touched_node_ids),
            written_texts=(value,)
            if has_written_fields and isinstance((value := node.get(name)), str)
            else (),
            matching_node_ids=(node_id,),
            added_node=before_node is None,
            matches_without_text=not has_written_fields,
        )
        for name in written_fields
    ]
    matching, remainder = split_write_by_draft(
        plot_root,
        project_id,
        draft_id,
        canvas_kind,
        fragments,
        service_id,
    )
    if matching:
        assert draft_id is not None
        confirm_draft(plot_root, project_id, draft_id, [node_id])
        if not remainder:
            return None
        unmatched_fields = {fragment.value: node.get(fragment.value) for fragment in remainder}
        record_applied_draft(
            plot_root,
            project_id,
            canvas_kind,
            unmatched_fields,
            write_result,
            chat_scope,
            service_id,
        )
        return partial_draft_mismatch_warning(draft_id)
    fallback_fields = {fragment.value: node.get(fragment.value) for fragment in remainder}
    record_applied_draft(
        plot_root,
        project_id,
        canvas_kind,
        fallback_fields,
        write_result,
        chat_scope,
        service_id,
    )
    if draft_id is None:
        return None
    return draft_mismatch_warning(draft_id)


def record_applied_draft(
    plot_root: Path,
    project_id: str,
    canvas_kind: CanvasKind,
    fields: dict[str, Any] | None,
    write_result: dict[str, Any],
    chat_scope: str,
    service_id: str | None = None,
) -> None:
    """Record one successful MCP node write that arrived without a draft id."""
    node = write_result["node"]
    rejected = set(write_result["rejected_fields"])
    written_fields = [name for name in (fields or {}) if name not in rejected]
    if not written_fields:
        written_fields = ["label"]
    proposed_text = "\n".join(
        f"{name}: {_display_value(node.get(name))}" for name in written_fields
    )
    persist_applied_draft(
        plot_root,
        project_id,
        canvas_kind,
        proposed_text,
        AUTO_DRAFT_RATIONALE,
        effective_chat_scope(chat_scope),
        [str(node["id"])],
        str(node["kind"]),
        service_id,
        [str(node["id"])],
    )


def finish_canvas_write_draft(
    plot_root: Path,
    project_id: str,
    draft_id: str | None,
    before: CanvasDoc,
    after: CanvasDoc,
    chat_scope: str,
) -> str | None:
    """Confirm or record a whole-canvas write from its normalized content diff."""
    before_content = _canvas_design_content(before.model_dump(by_alias=True))
    after_content = _canvas_design_content(after.model_dump(by_alias=True))
    if before_content == after_content:
        return _no_design_content_warning(draft_id)

    before_nodes: dict[str, dict[str, Any]] = before_content["nodes"]
    after_nodes: dict[str, dict[str, Any]] = after_content["nodes"]
    added = [node_id for node_id in after_nodes if node_id not in before_nodes]
    removed = [node_id for node_id in before_nodes if node_id not in after_nodes]
    before_edges: dict[str, dict[str, Any]] = before_content["edges"]
    after_edges: dict[str, dict[str, Any]] = after_content["edges"]
    edges_added = [edge_id for edge_id in after_edges if edge_id not in before_edges]
    edges_changed = [
        edge_id
        for edge_id in after_edges
        if edge_id in before_edges and after_edges[edge_id] != before_edges[edge_id]
    ]
    edges_removed = [edge_id for edge_id in before_edges if edge_id not in after_edges]
    changed_fields = [
        (node_id, field_name)
        for node_id in after_nodes
        if node_id in before_nodes
        for field_name in dict.fromkeys((*before_nodes[node_id], *after_nodes[node_id]))
        if before_nodes[node_id].get(field_name) != after_nodes[node_id].get(field_name)
    ]
    fragments: list[WriteFragment[_CanvasFragmentValue]] = [
        *(
            WriteFragment[_CanvasFragmentValue](
                ("node_added", node_id, None),
                node_ids=(node_id,),
                written_texts=tuple(_canvas_written_texts(after, [node_id])),
                matching_node_ids=(node_id,),
                added_node=True,
            )
            for node_id in added
        ),
        *(
            WriteFragment[_CanvasFragmentValue](
                ("node_changed", node_id, field_name),
                node_ids=(node_id,),
                written_texts=(value,)
                if isinstance((value := after_nodes[node_id].get(field_name)), str)
                else (),
                matching_node_ids=(node_id,),
            )
            for node_id, field_name in changed_fields
        ),
        *(
            WriteFragment[_CanvasFragmentValue](
                ("node_removed", node_id, None), node_ids=(node_id,)
            )
            for node_id in removed
        ),
        *(
            WriteFragment[_CanvasFragmentValue](
                ("edge_added", edge_id, None),
                node_ids=_edge_node_ids(after_edges[edge_id]),
                follows_matching_node=True,
            )
            for edge_id in edges_added
        ),
        *(
            WriteFragment[_CanvasFragmentValue](
                ("edge_changed", edge_id, None),
                node_ids=tuple(
                    dict.fromkeys(
                        (
                            *_edge_node_ids(before_edges[edge_id]),
                            *_edge_node_ids(after_edges[edge_id]),
                        )
                    )
                ),
                follows_matching_node=True,
            )
            for edge_id in edges_changed
        ),
        *(
            WriteFragment[_CanvasFragmentValue](
                ("edge_removed", edge_id, None),
                node_ids=_edge_node_ids(before_edges[edge_id]),
                follows_matching_node=True,
            )
            for edge_id in edges_removed
        ),
    ]
    service_id = after.feature_ref if after.canvas_kind == "feature" else None
    matching, remainder = split_write_by_draft(
        plot_root,
        project_id,
        draft_id,
        after.canvas_kind,
        fragments,
        service_id,
    )
    if matching:
        assert draft_id is not None
        resolved_node_ids = list(
            dict.fromkeys(
                item_id
                for fragment in matching
                for category, item_id, _ in [fragment.value]
                if category in ("node_added", "node_changed")
            )
        )
        confirm_draft(plot_root, project_id, draft_id, resolved_node_ids)
        if not remainder:
            return None
        _record_canvas_auto_draft(
            plot_root,
            project_id,
            after,
            before_nodes,
            after_nodes,
            remainder,
            chat_scope,
        )
        return partial_draft_mismatch_warning(draft_id)

    _record_canvas_auto_draft(
        plot_root,
        project_id,
        after,
        before_nodes,
        after_nodes,
        remainder,
        chat_scope,
    )
    if draft_id is None:
        return None
    return draft_mismatch_warning(draft_id)


def _record_canvas_auto_draft(
    plot_root: Path,
    project_id: str,
    canvas: CanvasDoc,
    before_nodes: dict[str, dict[str, Any]],
    after_nodes: dict[str, dict[str, Any]],
    fragments: Sequence[WriteFragment[_CanvasFragmentValue]],
    chat_scope: str,
) -> None:
    """Record only the canvas-diff fragments not claimed by a supplied draft."""

    def fragment_items(category: str) -> list[tuple[str, str | None]]:
        return [(item.value[1], item.value[2]) for item in fragments if item.value[0] == category]

    def names(items: list[tuple[str, str | None]], nodes: dict[str, dict[str, Any]]) -> str:
        labels = (
            f"{nodes[node_id].get('label') or node_id}.{field_name}"
            if field_name is not None
            else str(nodes[node_id].get("label") or node_id)
            for node_id, field_name in items
        )
        return ", ".join(labels) or "없음"

    added = fragment_items("node_added")
    changed = fragment_items("node_changed")
    removed = fragment_items("node_removed")
    edges_added = fragment_items("edge_added")
    edges_changed = fragment_items("edge_changed")
    edges_removed = fragment_items("edge_removed")
    proposed_text = (
        f"더함: {names(added, after_nodes)} / "
        f"바꿈: {names(changed, after_nodes)} / "
        f"뺌: {names(removed, before_nodes)}"
    )
    if edges_added or edges_changed or edges_removed:
        proposed_text += (
            f"\n선: 더함 {len(edges_added)} / 바꿈 {len(edges_changed)} / 뺌 {len(edges_removed)}"
        )
    persist_applied_draft(
        plot_root,
        project_id,
        canvas.canvas_kind,
        proposed_text,
        AUTO_DRAFT_RATIONALE,
        effective_chat_scope(chat_scope),
        list(dict.fromkeys(item_id for item_id, _ in [*added, *changed, *removed])),
        "canvas",
        canvas.feature_ref if canvas.canvas_kind == "feature" else None,
        list(dict.fromkeys(item_id for item_id, _ in [*added, *changed])),
    )


def _edge_node_ids(edge: dict[str, Any]) -> tuple[str, str]:
    return str(edge["source"]), str(edge["target"])


def draft_mismatch_warning(draft_id: str) -> str:
    return (
        f"draft {draft_id} does not match this write; recorded an auto draft instead. "
        "If the person accepted this draft with edits, call resolve_draft with status='edited'."
    )


def partial_draft_mismatch_warning(draft_id: str) -> str:
    return f"some fields did not match draft {draft_id}; recorded an auto draft for them"


def _no_design_content_warning(draft_id: str | None) -> str | None:
    if draft_id is None:
        return None
    return f"draft {draft_id} was not confirmed: this write changed no design content (layout only)"


def _canvas_written_texts(canvas: CanvasDoc, node_ids: list[str]) -> list[str]:
    nodes = {str(node.id): node for node in canvas.nodes}
    return [
        value
        for node_id in node_ids
        for node in (nodes[node_id],)
        for name in writable_node_fields(node)
        if isinstance((value := getattr(node, name, None)), str)
    ]


def _display_value(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True)
