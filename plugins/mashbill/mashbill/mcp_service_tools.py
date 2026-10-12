"""MCP tools for service-set proposals (novel-workspace W-00000425)."""

from __future__ import annotations

from typing import Any

from mashbill.proposal_show import show_instruction
from mashbill.service_proposal import add_proposed_services as add_services
from mashbill.service_proposal import propose_services as keep_services
from mashbill.tool_log import record_tool_call
from mashbill.workspace import resolve_plot_root


def propose_services(
    project_path: str, project_id: str, services: list[dict[str, Any]]
) -> dict[str, Any]:
    """Record the full service set agreed for the Services canvas.

    Returns ``{"rendered", "show"}``; ``show`` says who shows ``rendered`` to the person.
    Pass every service of the set, including ones already on the canvas (they show as ✓ and
    are not added again). ``services``: ``{"key", "label", "value_created"?, "problem"?}``.
    Nothing is added until ``add_proposed_services``. A new call replaces a set not yet added.
    Errors name what to fix.
    """
    plot_root = resolve_plot_root(project_path)
    rendered = keep_services(plot_root, project_id, services)
    record_tool_call("propose_services", project_id=project_id, canvas="services")
    return {"rendered": rendered, "show": show_instruction("service set")}


def add_proposed_services(project_path: str, project_id: str) -> dict[str, Any]:
    """Add every service of the confirmed ``propose_services`` set the canvas lacks, in one write.

    Call after the person confirms the set. Returns ``{"service_ids": {key: id}}``; then set
    each service's participants with set_node_references. Fails when there is no set or it
    was already added.
    """
    plot_root = resolve_plot_root(project_path)
    result = add_services(plot_root, project_id)
    record_tool_call(
        "add_proposed_services",
        project_id=project_id,
        canvas="services",
        node_ids=list(result["service_ids"].values()),
    )
    return result
