"""MCP tools for feature-flow proposals (novel-workspace W-00000423)."""

from __future__ import annotations

from typing import Any

from mashbill.flow_proposal import draw_proposed_flow as draw_flow
from mashbill.flow_proposal import propose_flow as keep_flow
from mashbill.tool_log import record_tool_call
from mashbill.workspace import resolve_plot_root


def propose_flow(
    project_path: str,
    project_id: str,
    service_id: str,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]] | None = None,
    open_items: list[dict[str, Any]] | None = None,
    omitted: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Record a feature-flow draft before showing it; returns ``{"rendered": text}``.

    Show the person ``rendered`` as the draft. Nothing is drawn until
    ``draw_proposed_flow``. ``service_id`` is the feature id.
    - ``nodes``: ``{"key", "kind": step|decision|rule|note, "label", "outcome"?,
      "body"?, "covers"?: [item numbers of the [Feature description] it carries]}``.
    - ``edges``: ``{"source", "target", "label"?}``; each end is a node key or an
      existing node id on the feature canvas (the actor_ref, the feature root, an
      earlier step). Notes take no lines.
    - ``open_items``: ``{"at": key or node id, "question", "covers"?}`` — a branch
      end nobody stated or a line whose target is unclear.
    - ``omitted``: ``{"item", "reason"}`` — a description item the person chose
      to leave out.
    Every description item not yet drawn must appear in some ``covers`` or
    ``omitted``. A new call replaces the feature's undrawn proposal. Errors name
    what to fix.
    """
    plot_root = resolve_plot_root(project_path)
    rendered = keep_flow(
        plot_root,
        project_id,
        service_id,
        nodes,
        edges or [],
        open_items or [],
        omitted or [],
    )
    record_tool_call("propose_flow", project_id=project_id, canvas="feature", service_id=service_id)
    return {"rendered": rendered}


def draw_proposed_flow(project_path: str, project_id: str, service_id: str) -> dict[str, Any]:
    """Draw the feature's confirmed ``propose_flow`` draft exactly, in one write.

    Call after the person confirms the draft. Adds only the proposed nodes and
    lines; open items stay unjoined. Returns ``{"node_ids": {key: id},
    "open_items": [{"at": step label, "question"}]}``. Fails when there is no
    proposal or it was already drawn.
    """
    plot_root = resolve_plot_root(project_path)
    result = draw_flow(plot_root, project_id, service_id)
    record_tool_call(
        "draw_proposed_flow",
        project_id=project_id,
        canvas="feature",
        service_id=service_id,
        node_ids=list(result["node_ids"].values()),
    )
    return result
