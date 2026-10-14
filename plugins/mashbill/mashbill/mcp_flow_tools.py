"""MCP tools for feature-flow proposals (novel-workspace W-00000423)."""

from __future__ import annotations

from typing import Any

from mashbill.flow_proposal import draw_proposed_flow as draw_flow
from mashbill.flow_proposal import propose_flow as keep_flow
from mashbill.proposal_show import show_instruction
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
    relabels: list[dict[str, Any]] | None = None,
    remove_edges: list[dict[str, Any]] | None = None,
    placed: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Record a feature-flow draft before showing it; returns ``{"rendered", "show", "numbers"}``.

    ``show`` says who shows ``rendered`` to the person: inside the Novel app the
    app shows it under your reply; elsewhere you show it. ``rendered`` numbers
    the nodes [1], [2], … in your nodes' order and never shows your keys;
    ``numbers`` maps each shown number to your key, so "3번" from the person is
    ``numbers["3"]``. Nothing is drawn until ``draw_proposed_flow``.
    ``service_id`` is the feature id.
    - ``nodes``: ``{"key", "kind": step|decision|rule|note, "label", "outcome"?,
      "body"?, "covers"?: [item numbers of the [Feature description] it carries]}``.
      Put in outcome only a result the person said or a canvas holds, in their words;
      otherwise leave it empty and ask in open_items.
    - ``edges``: ``{"source", "target", "label"?}``; each end is a node key or an
      existing node id on the feature canvas (the actor_ref, the feature root, an
      earlier step). Notes take no lines.
    - ``open_items``: ``{"at": key or node id, "question"}`` — a branch
      end nobody stated or a line whose target is unclear;
      ask it plainly, with no ending of your own as an example.
    - ``omitted``: ``{"item", "reason"}`` — a description item the person chose
      to leave out.
    - Changing a drawn flow: ``relabels`` ``{"node": id, "label", "outcome"?}``
      renames drawn steps; ``remove_edges`` ``{"source": id, "target": id}``
      deletes drawn lines; ``placed`` ``{"item", "at": id}`` marks a description
      item a drawn node already carries. Put every such change here so the
      person sees it; do not change the flow outside the draft.
    Every description item not yet drawn must appear in a node's ``covers`` (an
    open item alone does not place it) or in ``omitted``. A decision needs two or
    more labeled lines with different labels, and a loop needs a line leaving
    it; an open item on the decision or on a step in the loop stands for what is
    still unknown. A step with no outgoing line is an end. A new call replaces
    the feature's undrawn proposal. Errors name what to fix.
    """
    plot_root = resolve_plot_root(project_path)
    kept = keep_flow(
        plot_root,
        project_id,
        service_id,
        nodes,
        edges or [],
        open_items or [],
        omitted or [],
        relabels,
        remove_edges,
        placed,
    )
    record_tool_call("propose_flow", project_id=project_id, canvas="feature", service_id=service_id)
    return {
        "rendered": kept["rendered"],
        "show": show_instruction("draft"),
        "numbers": kept["numbers"],
    }


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
