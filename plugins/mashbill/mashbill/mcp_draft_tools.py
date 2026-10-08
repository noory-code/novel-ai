"""MCP draft operations and matching for writes tied to kept proposals."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mashbill.blueprint_content import _canvas_design_content
from mashbill.chat_scope_env import effective_chat_scope
from mashbill.draft_store import read_draft
from mashbill.draft_store import record_draft as persist_draft
from mashbill.draft_store import resolve_draft as persist_resolution
from mashbill.draft_store import update_draft as persist_update
from mashbill.draft_write_split import WriteFragment, split_write_by_draft
from mashbill.field_policy import writable_node_fields
from mashbill.models_canvas import CanvasDoc, CanvasKind
from mashbill.models_draft import DraftCanvasKind, DraftDoc, ResolvedDraftStatus
from mashbill.tool_log import record_tool_call
from mashbill.workspace import resolve_plot_root

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
    """Keep a proposal after the person explicitly asks to save it as a draft.

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
    record_tool_call(
        "record_draft",
        project_id=project_id,
        canvas=canvas_kind,
        service_id=service_id,
        node_ids=target_node_ids or [],
        draft_id=draft.id,
    )
    return _draft_result(draft)


def update_draft(
    project_path: str,
    project_id: str,
    draft_id: str,
    proposed_text: str,
    rationale: str,
) -> dict[str, Any]:
    """Revise a kept proposal after the person agrees to the new wording.

    Only an unapplied ``proposed`` draft can be revised. Resolved drafts stay
    unchanged; record a new draft if the person wants to revisit one.
    """
    plot_root = resolve_plot_root(project_path)
    draft = persist_update(plot_root, project_id, draft_id, proposed_text, rationale)
    record_tool_call(
        "update_draft",
        project_id=project_id,
        canvas=draft.canvas_kind,
        service_id=draft.service_id,
        node_ids=draft.target_node_ids,
        draft_id=draft_id,
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
    draft = persist_resolution(plot_root, project_id, draft_id, status, node_ids)
    record_tool_call(
        "resolve_draft",
        project_id=project_id,
        canvas=draft.canvas_kind,
        service_id=draft.service_id,
        node_ids=node_ids or [],
        draft_id=draft_id,
    )
    return _draft_result(draft)


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
    if not written_texts:
        return False
    matching, _ = split_write_by_draft(
        plot_root,
        project_id,
        draft_id,
        canvas_kind,
        [
            WriteFragment(
                None,
                node_ids=tuple(touched_node_ids),
                written_texts=tuple(written_texts),
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
    target_node_ids: list[str],
    resolved_node_ids: list[str],
    service_id: str | None = None,
    written_texts: list[str] | None = None,
    design_content_changed: bool = True,
) -> str | None:
    """Confirm a matching supplied draft without creating implicit drafts."""
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
    service_id: str | None,
    additional_touched_node_ids: list[str] | None = None,
    before_node: dict[str, Any] | None = None,
) -> str | None:
    """Confirm matching fields of a supplied draft without implicit records."""
    node_id = str(write_result["node"]["id"])
    touched_node_ids = [node_id, *(additional_touched_node_ids or [])]
    node = write_result["node"]
    rejected = set(write_result["rejected_fields"])
    written_fields = [name for name in (fields or {}) if name not in rejected]
    if before_node is not None and all(
        before_node.get(name) == node.get(name) for name in written_fields
    ):
        return _no_design_content_warning(draft_id)
    if not written_fields:
        written_fields = ["label"]
    fragments = [
        WriteFragment(
            name,
            node_ids=tuple(touched_node_ids),
            written_texts=(value,) if isinstance((value := node.get(name)), str) and value else (),
            matching_node_ids=(node_id,),
            added_node=before_node is None,
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
        return partial_draft_mismatch_warning(draft_id)
    if draft_id is None:
        return None
    return draft_mismatch_warning(draft_id)


def finish_canvas_write_draft(
    plot_root: Path,
    project_id: str,
    draft_id: str | None,
    before: CanvasDoc,
    after: CanvasDoc,
) -> str | None:
    """Confirm matching parts of a whole-canvas write without implicit drafts."""
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
        return partial_draft_mismatch_warning(draft_id)
    if draft_id is None:
        return None
    return draft_mismatch_warning(draft_id)


def _edge_node_ids(edge: dict[str, Any]) -> tuple[str, str]:
    return str(edge["source"]), str(edge["target"])


def draft_mismatch_warning(draft_id: str) -> str:
    return (
        f"draft {draft_id} does not match this write and was not confirmed. "
        "If the person accepted this draft with edits, call resolve_draft with status='edited'."
    )


def partial_draft_mismatch_warning(draft_id: str) -> str:
    return f"draft {draft_id} was confirmed, but some written fields did not match it"


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
