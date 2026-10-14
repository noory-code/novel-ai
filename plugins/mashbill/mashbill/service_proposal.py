"""Service-set proposals: the agreed set of services held by the engine, then added at once.

The services coach records the whole set of services it and the person agreed on. Recording
renders the set; a service whose name is already on the Services canvas is marked as present
instead of proposed again. When the person confirms, adding writes every proposed service the
canvas lacks in one canvas write, so no agreed service is left behind when the coach goes on to
describe one of them (D-2026-10-12-A).
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, TypeAdapter

from mashbill.canvas_io import build_new_node, read_canvas, write_canvas
from mashbill.models import CanvasDoc
from mashbill.proposal_store import (
    load_proposals,
    name_key,
    now_iso,
    proposed_since,
    save_proposals,
)
from mashbill.storage import anchor_obstacles

_DIRNAME = "service_proposals"
_NAME = "services"


class ProposedService(BaseModel):
    """One service of the set; ``key`` is proposal-local."""

    key: str = Field(min_length=1)
    label: str = Field(min_length=1)
    problem: str = ""
    value_created: str = ""


class ServiceProposal(BaseModel):
    services: list[ProposedService]
    proposed_at: str = ""
    added: bool = False


class ServiceProposalFile(BaseModel):
    current: ServiceProposal | None = None


def _existing_names(canvas: CanvasDoc) -> set[str]:
    return {name_key(node.label) for node in canvas.nodes if node.kind == "service"}


def _check(proposal: ServiceProposal) -> None:
    if not proposal.services:
        raise ValueError("a service set needs at least one service")
    keys: set[str] = set()
    names: set[str] = set()
    for service in proposal.services:
        name = name_key(service.label)
        if not name:
            raise ValueError(f"service {service.key!r} has an empty name")
        if service.key in keys:
            raise ValueError(f"key {service.key!r} is used twice")
        if name in names:
            raise ValueError(f"service name {name!r} appears twice")
        keys.add(service.key)
        names.add(name)


def render(proposal: ServiceProposal, canvas: CanvasDoc) -> str:
    """The set as the person reads it: services to add, and ✓ for those already on the canvas."""
    present = _existing_names(canvas)
    lines: list[str] = []
    for service in proposal.services:
        name = name_key(service.label)
        if name in present:
            lines.append(f"✓ {name}")
            continue
        head = f"[{service.key}] {name}"
        if service.value_created:
            head += f": {service.value_created}"
        lines.append(head)
        if service.problem:
            lines.append(f"  ↳ {service.problem}")
    return "\n".join(lines)


def _load(plot_root: Path, project_id: str) -> ServiceProposalFile:
    return load_proposals(plot_root, project_id, _DIRNAME, _NAME, ServiceProposalFile)


def propose_services(plot_root: Path, project_id: str, services: list[dict[str, Any]]) -> str:
    """Check and keep the agreed service set; return its rendering. Replaces an unadded set."""
    proposal = ServiceProposal(
        services=TypeAdapter(list[ProposedService]).validate_python(services),
        proposed_at=now_iso(),
    )
    _check(proposal)
    canvas = read_canvas(plot_root, project_id, "services")
    present = _existing_names(canvas)
    if all(name_key(service.label) in present for service in proposal.services):
        raise ValueError(
            "every service of this set is already on the Services canvas; nothing to add — "
            "propose a set only when it adds a service"
        )
    save_proposals(plot_root, project_id, _DIRNAME, _NAME, ServiceProposalFile(current=proposal))
    return render(proposal, canvas)


def rendering_proposed_since(plot_root: Path, project_id: str, since: datetime) -> str | None:
    """The rendering of the unadded service set if it was recorded at or after ``since``."""
    proposal = _load(plot_root, project_id).current
    if proposal is None or proposal.added or not proposed_since(proposal.proposed_at, since):
        return None
    return render(proposal, read_canvas(plot_root, project_id, "services"))


def add_proposed_services(plot_root: Path, project_id: str) -> dict[str, Any]:
    """Write every service of the kept set that the canvas lacks, in one canvas write.

    Returns the key → node id map of the services added. Raises when there is no set or it was
    already added.
    """
    doc = _load(plot_root, project_id)
    proposal = doc.current
    if proposal is None:
        raise ValueError("no service set is kept; record one with propose_services")
    if proposal.added:
        raise ValueError("this service set was already added; propose_services again for changes")
    canvas = read_canvas(plot_root, project_id, "services")
    present = _existing_names(canvas)
    ids: dict[str, str] = {}
    for service in proposal.services:
        name = name_key(service.label)
        if name in present:
            continue
        fields = {"label": name, "problem": service.problem, "value_created": service.value_created}
        node, _ = build_new_node(
            canvas,
            "service",
            fields,
            None,
            obstacles=anchor_obstacles(plot_root, project_id, "services"),
        )
        ids[service.key] = str(node.id)
        canvas = canvas.model_copy(update={"nodes": [*canvas.nodes, node]})
    write_canvas(plot_root, project_id, CanvasDoc.model_validate(canvas.model_dump(by_alias=True)))
    save_proposals(
        plot_root,
        project_id,
        _DIRNAME,
        _NAME,
        ServiceProposalFile(current=proposal.model_copy(update={"added": True})),
    )
    return {"service_ids": ids}
