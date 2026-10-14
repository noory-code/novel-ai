"""Feature-flow proposals: the coach's draft held by the engine, then drawn as is.

The feature coach records a flow draft as nodes, lines, open items, and stated
omissions. Recording checks the draft's shape: every line names a target, notes
stay edgeless, every open item hangs on a known step, the branching has no
defect a machine can see (``flow_structure``), and every numbered item of the
feature's Services description is placed as a node or omitted with a reason.
The person reads the draft with its nodes numbered; the coach's keys stay
internal. When the person confirms, drawing writes exactly the proposed nodes
and lines in one canvas write. One proposal file per feature lives under
``flow_proposals/``; it is engine state, not part of the canvas wire contract.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, TypeAdapter

from mashbill.canvas_io import build_new_node, read_canvas, write_canvas
from mashbill.chat_feature_description import feature_description_items
from mashbill.design_check import feature_check, write_design_check
from mashbill.edge_io import _build_edge
from mashbill.flow_structure import check_structure
from mashbill.models import CanvasDoc
from mashbill.proposal_store import load_proposals, now_iso, proposed_since, save_proposals

_DIRNAME = "flow_proposals"

ProposedKind = Literal["step", "decision", "rule", "note"]


class ProposedNode(BaseModel):
    """A node the draft adds; ``key`` is draft-local and lines refer to it."""

    key: str = Field(min_length=1)
    kind: ProposedKind
    label: str = Field(min_length=1)
    outcome: str = ""
    body: str = ""
    covers: list[int] = Field(default_factory=list)


class ProposedEdge(BaseModel):
    """A directed line between two draft keys or existing canvas node ids."""

    source: str
    target: str
    label: str = ""


class OpenItem(BaseModel):
    """Something the draft leaves open, hung on the step where it arises."""

    at: str
    question: str = Field(min_length=1)


class Omission(BaseModel):
    """A description item the draft leaves out on purpose, with the reason."""

    item: int
    reason: str = Field(min_length=1)


class Relabel(BaseModel):
    """A drawn step the draft renames (and, for a step, gives a new outcome)."""

    node: str
    label: str = Field(min_length=1)
    outcome: str | None = None


class RemovedEdge(BaseModel):
    """A drawn line the draft deletes."""

    source: str
    target: str


class Placement(BaseModel):
    """A description item a drawn node already carries."""

    item: int
    at: str


class FlowProposal(BaseModel):
    nodes: list[ProposedNode]
    edges: list[ProposedEdge] = Field(default_factory=list)
    open_items: list[OpenItem] = Field(default_factory=list)
    omitted: list[Omission] = Field(default_factory=list)
    relabels: list[Relabel] = Field(default_factory=list)
    remove_edges: list[RemovedEdge] = Field(default_factory=list)
    placed: list[Placement] = Field(default_factory=list)
    proposed_at: str = ""
    drawn: bool = False


class FlowProposalFile(BaseModel):
    current: FlowProposal | None = None
    # Description items already accounted for by drawn proposals.
    drawn_items: list[int] = Field(default_factory=list)


def _load(plot_root: Path, project_id: str, feature_id: str) -> FlowProposalFile:
    return load_proposals(plot_root, project_id, _DIRNAME, feature_id, FlowProposalFile)


def _save(plot_root: Path, project_id: str, feature_id: str, doc: FlowProposalFile) -> None:
    save_proposals(plot_root, project_id, _DIRNAME, feature_id, doc)


def _check_shape(proposal: FlowProposal, canvas: CanvasDoc) -> None:
    existing = {str(node.id): node for node in canvas.nodes}
    keys: set[str] = set()
    for node in proposal.nodes:
        if node.key in existing:
            raise ValueError(f"key {node.key!r} is already a node id on this canvas")
        if node.key in keys:
            raise ValueError(f"key {node.key!r} is used twice")
        keys.add(node.key)
    notes = {node.key for node in proposal.nodes if node.kind == "note"}
    notes |= {node_id for node_id, node in existing.items() if node.kind == "note"}
    known = keys | set(existing)
    for edge in proposal.edges:
        for end in (edge.source, edge.target):
            if end not in known:
                raise ValueError(
                    f"line {edge.source!r} → {edge.target!r}: {end!r} is no key or node id; "
                    "a line without a clear target belongs in open_items"
                )
            if end in notes:
                raise ValueError(f"line {edge.source!r} → {edge.target!r} touches a note")
    for item in proposal.open_items:
        if item.at not in known:
            raise ValueError(f"open item {item.question!r} hangs on {item.at!r}, no key or node id")
    for relabel in proposal.relabels:
        if relabel.node not in existing:
            raise ValueError(f"rename {relabel.label!r}: no node {relabel.node!r} on this canvas")
    drawn = {(str(edge.source), str(edge.target)) for edge in canvas.edges}
    for removed in proposal.remove_edges:
        if (removed.source, removed.target) not in drawn:
            raise ValueError(f"no line {removed.source!r} → {removed.target!r} on this canvas")
    for placement in proposal.placed:
        if placement.at not in existing:
            raise ValueError(
                f"item {placement.item} is placed at {placement.at!r}, no node on this canvas"
            )


def _check_branching(proposal: FlowProposal, canvas: CanvasDoc) -> None:
    drawn = {str(node.id): node.kind for node in canvas.nodes}
    kinds = {**drawn, **{node.key: node.kind for node in proposal.nodes}}
    names = {str(node.id): f"{str(node.id)!r} ({node.label})" for node in canvas.nodes}
    names.update({node.key: f"{node.key!r} ({node.label})" for node in proposal.nodes})
    before = [(str(e.source), str(e.target), e.label) for e in canvas.edges]
    removed = {(r.source, r.target) for r in proposal.remove_edges}
    after = [line for line in before if line[:2] not in removed]
    after += [(e.source, e.target, e.label) for e in proposal.edges]
    open_at = {item.at for item in proposal.open_items}
    check_structure(drawn, kinds, names, before, after, open_at)


def _check_cover(proposal: FlowProposal, items: list[str], drawn_items: list[int]) -> None:
    numbers = range(1, len(items) + 1)
    covered = {n for node in proposal.nodes for n in node.covers}
    covered |= {omission.item for omission in proposal.omitted}
    covered |= {placement.item for placement in proposal.placed}
    unknown = sorted(covered - set(numbers))
    if unknown:
        raise ValueError(f"no description items numbered {unknown}; items run 1..{len(items)}")
    missing = [n for n in numbers if n not in covered and n not in drawn_items]
    if missing:
        lines = "\n".join(f"{n}. {items[n - 1]}" for n in missing)
        raise ValueError(
            "the feature description holds these items and the draft does not place them: "
            "put each in the covers of the node that carries it (ask in open_items where its "
            "ending or place is unknown), in placed when a drawn node already carries it, "
            "or in omitted with the reason\n" + lines
        )


def display_numbers(proposal: FlowProposal) -> dict[str, str]:
    """The number the person sees for each draft node (in draft order) → its key."""
    return {str(number): node.key for number, node in enumerate(proposal.nodes, start=1)}


def render(proposal: FlowProposal, canvas: CanvasDoc, items: list[str]) -> str:
    """The draft as the person reads it: nodes with their lines and open items."""
    labels = {str(node.id): node.label for node in canvas.nodes}
    labels.update({node.key: node.label for node in proposal.nodes})
    # The person reads numbers, never the coach's draft-local keys (O-00000137).
    keys = {key: number for number, key in display_numbers(proposal).items()}

    def name(ref: str) -> str:
        return f"[{keys[ref]}] {labels[ref]}" if ref in keys else labels.get(ref, ref)

    def under(ref: str) -> list[str]:
        lines = [
            f"  → {name(e.target)}" + (f" ({e.label})" if e.label else "")
            for e in proposal.edges
            if e.source == ref
        ]
        lines += [f"  … {item.question}" for item in proposal.open_items if item.at == ref]
        return lines

    out: list[str] = []
    for ref in dict.fromkeys(
        [e.source for e in proposal.edges if e.source not in keys]
        + [i.at for i in proposal.open_items if i.at not in keys]
    ):
        out += [labels.get(ref, ref), *under(ref)]
    marks = {"decision": "◇ ", "rule": "▣ ", "note": "✎ "}
    for node in proposal.nodes:
        head = f"[{keys[node.key]}] {marks.get(node.kind, '')}{node.label}"
        if node.outcome:
            head += f": {node.outcome}"
        out += [head, *under(node.key)]
    for relabel in proposal.relabels:
        line = f"~ {labels.get(relabel.node, relabel.node)} → {relabel.label}"
        out.append(line + (f": {relabel.outcome}" if relabel.outcome else ""))
    out += [
        f"⨯ {labels.get(r.source, r.source)} → {labels.get(r.target, r.target)}"
        for r in proposal.remove_edges
    ]
    renamed = {r.node: r.label for r in proposal.relabels}
    # One ✓ line per item, naming every drawn node that carries it.
    places: dict[int, list[str]] = {}
    for p in proposal.placed:
        place = renamed.get(p.at, labels.get(p.at, p.at))
        if place not in places.setdefault(p.item, []):
            places[p.item].append(place)
    out += [f"✓ {n}. {items[n - 1]} — {' · '.join(at)}" for n, at in places.items()]
    out += [f"✕ {o.item}. {items[o.item - 1]} — {o.reason}" for o in proposal.omitted]
    return "\n".join(out)


def propose_flow(
    plot_root: Path,
    project_id: str,
    feature_id: str,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    open_items: list[dict[str, Any]],
    omitted: list[dict[str, Any]],
    relabels: list[dict[str, Any]] | None = None,
    remove_edges: list[dict[str, Any]] | None = None,
    placed: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Check and keep a flow draft for ``feature_id``.

    Returns ``{"rendered", "numbers"}``: the rendering the person reads and the
    number shown for each node → its key. A new proposal replaces the feature's
    previous one. Raises ``ValueError`` naming what to fix when the draft's
    shape, branching, or description cover fails.
    """
    proposal = FlowProposal(
        nodes=TypeAdapter(list[ProposedNode]).validate_python(nodes),
        edges=TypeAdapter(list[ProposedEdge]).validate_python(edges),
        open_items=TypeAdapter(list[OpenItem]).validate_python(open_items),
        omitted=TypeAdapter(list[Omission]).validate_python(omitted),
        relabels=TypeAdapter(list[Relabel]).validate_python(relabels or []),
        remove_edges=TypeAdapter(list[RemovedEdge]).validate_python(remove_edges or []),
        placed=TypeAdapter(list[Placement]).validate_python(placed or []),
        proposed_at=now_iso(),
    )
    canvas = read_canvas(plot_root, project_id, "feature", feature_id)
    items = feature_description_items(plot_root, project_id, feature_id)
    doc = _load(plot_root, project_id, feature_id)
    _check_shape(proposal, canvas)
    _check_branching(proposal, canvas)
    _check_cover(proposal, items, doc.drawn_items)
    _save(plot_root, project_id, feature_id, doc.model_copy(update={"current": proposal}))
    return {"rendered": render(proposal, canvas, items), "numbers": display_numbers(proposal)}


def rendering_proposed_since(
    plot_root: Path, project_id: str, feature_id: str, since: datetime
) -> str | None:
    """The rendering of the feature's undrawn proposal if it was recorded at or after ``since``."""
    proposal = _load(plot_root, project_id, feature_id).current
    if proposal is None or proposal.drawn or not proposed_since(proposal.proposed_at, since):
        return None
    canvas = read_canvas(plot_root, project_id, "feature", feature_id)
    return render(proposal, canvas, feature_description_items(plot_root, project_id, feature_id))


def draw_proposed_flow(plot_root: Path, project_id: str, feature_id: str) -> dict[str, Any]:
    """Write exactly the kept proposal's nodes and lines in one canvas write.

    Open items stay unjoined. Returns the key → node id map and the open items
    by step label. Raises when there is no proposal or it is already drawn.
    """
    doc = _load(plot_root, project_id, feature_id)
    proposal = doc.current
    if proposal is None:
        raise ValueError("no flow proposal for this feature; record one with propose_flow")
    if proposal.drawn:
        raise ValueError("this flow proposal is already drawn; propose_flow again for new parts")
    # W-00000430 — a check the coach recorded after this draft examined what
    # is about to be drawn; drawing it unchanged must not reopen that check.
    kept_check = feature_check(plot_root, project_id, feature_id)
    if not (
        kept_check is not None
        and kept_check.state in ("checking", "checked")
        and proposal.proposed_at
        and datetime.fromisoformat(kept_check.updated_at)
        >= datetime.fromisoformat(proposal.proposed_at)
    ):
        kept_check = None
    canvas = read_canvas(plot_root, project_id, "feature", feature_id)
    renames = {r.node: r for r in proposal.relabels}
    nodes_now = []
    for existing in canvas.nodes:
        relabel = renames.get(str(existing.id))
        if relabel is not None:
            update: dict[str, Any] = {"label": relabel.label}
            if relabel.outcome is not None and existing.kind == "step":
                update["outcome"] = relabel.outcome
            existing = existing.model_copy(update=update)
        nodes_now.append(existing)
    removed = {(r.source, r.target) for r in proposal.remove_edges}
    edges_now = [e for e in canvas.edges if (str(e.source), str(e.target)) not in removed]
    canvas = canvas.model_copy(update={"nodes": nodes_now, "edges": edges_now})
    ids: dict[str, str] = {}
    for node in proposal.nodes:
        source = next((e.source for e in proposal.edges if e.target == node.key), None)
        near = ids.get(source, source) if source is not None else None
        if near is not None and near not in {str(n.id) for n in canvas.nodes}:
            near = None
        fields = {"label": node.label, "body": node.body}
        if node.kind == "step":
            fields["outcome"] = node.outcome
        built, _ = build_new_node(canvas, node.kind, fields, near)
        ids[node.key] = str(built.id)
        canvas = canvas.model_copy(update={"nodes": [*canvas.nodes, built]})
    for edge in proposal.edges:
        line = _build_edge(
            canvas, ids.get(edge.source, edge.source), ids.get(edge.target, edge.target), edge.label
        )
        canvas = canvas.model_copy(update={"edges": [*canvas.edges, line]})
    write_canvas(plot_root, project_id, CanvasDoc.model_validate(canvas.model_dump(by_alias=True)))
    if kept_check is not None:
        write_design_check(plot_root, project_id, feature_id, kept_check)
    accounted = {n for node in proposal.nodes for n in node.covers}
    accounted |= {omission.item for omission in proposal.omitted}
    accounted |= {placement.item for placement in proposal.placed}
    _save(
        plot_root,
        project_id,
        feature_id,
        FlowProposalFile(
            current=proposal.model_copy(update={"drawn": True}),
            drawn_items=sorted(set(doc.drawn_items) | accounted),
        ),
    )
    labels = {str(node.id): node.label for node in canvas.nodes}
    return {
        "node_ids": ids,
        "open_items": [
            {"at": labels[ids.get(item.at, item.at)], "question": item.question}
            for item in proposal.open_items
        ],
    }
