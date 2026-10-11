"""Feature-flow proposals: the coach's draft held by the engine, then drawn as is.

The feature coach records a flow draft as nodes, lines, open items, and stated
omissions. Recording checks the draft's shape: every line names a target, notes
stay edgeless, every open item hangs on a known step, and every numbered item of
the feature's Services description is placed, left open, or omitted with a
reason. When the person confirms, drawing writes exactly the proposed nodes and
lines in one canvas write. One proposal file per feature lives under
``flow_proposals/``; it is engine state, not part of the canvas wire contract.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, TypeAdapter

from mashbill.canvas_io import build_new_node, read_canvas, write_canvas
from mashbill.chat_feature_description import feature_description_items
from mashbill.edge_io import _build_edge
from mashbill.models import CanvasDoc
from mashbill.storage import _ensure_project, _project_dir, _read_json, _write_json

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
    covers: list[int] = Field(default_factory=list)


class Omission(BaseModel):
    """A description item the draft leaves out on purpose, with the reason."""

    item: int
    reason: str = Field(min_length=1)


class FlowProposal(BaseModel):
    nodes: list[ProposedNode]
    edges: list[ProposedEdge] = Field(default_factory=list)
    open_items: list[OpenItem] = Field(default_factory=list)
    omitted: list[Omission] = Field(default_factory=list)
    drawn: bool = False


class FlowProposalFile(BaseModel):
    current: FlowProposal | None = None
    # Description items already accounted for by drawn proposals.
    drawn_items: list[int] = Field(default_factory=list)


def _path(plot_root: Path, project_id: str, feature_id: str) -> Path:
    if not feature_id or not feature_id.replace("-", "").replace("_", "").isalnum():
        raise ValueError(f"unsafe feature id: {feature_id!r}")
    return _project_dir(plot_root, project_id) / _DIRNAME / f"{feature_id}.json"


def _load(plot_root: Path, project_id: str, feature_id: str) -> FlowProposalFile:
    _ensure_project(plot_root, project_id)
    path = _path(plot_root, project_id, feature_id)
    if not path.exists():
        return FlowProposalFile()
    return FlowProposalFile.model_validate(_read_json(path))


def _save(plot_root: Path, project_id: str, feature_id: str, doc: FlowProposalFile) -> None:
    _write_json(_path(plot_root, project_id, feature_id), doc.model_dump())


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


def _check_cover(proposal: FlowProposal, items: list[str], drawn_items: list[int]) -> None:
    numbers = range(1, len(items) + 1)
    covered = {n for node in proposal.nodes for n in node.covers}
    covered |= {n for item in proposal.open_items for n in item.covers}
    covered |= {omission.item for omission in proposal.omitted}
    unknown = sorted(covered - set(numbers))
    if unknown:
        raise ValueError(f"no description items numbered {unknown}; items run 1..{len(items)}")
    missing = [n for n in numbers if n not in covered and n not in drawn_items]
    if missing:
        lines = "\n".join(f"{n}. {items[n - 1]}" for n in missing)
        raise ValueError(
            "the feature description holds these items and the draft does not place them: "
            "put each in a node's covers, an open item's covers, or omitted with the reason\n"
            + lines
        )


def render(proposal: FlowProposal, canvas: CanvasDoc, items: list[str]) -> str:
    """The draft as the person reads it: nodes with their lines and open items."""
    labels = {str(node.id): node.label for node in canvas.nodes}
    labels.update({node.key: node.label for node in proposal.nodes})
    keys = {node.key for node in proposal.nodes}

    def name(ref: str) -> str:
        return f"[{ref}] {labels[ref]}" if ref in keys else labels.get(ref, ref)

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
        head = f"[{node.key}] {marks.get(node.kind, '')}{node.label}"
        if node.outcome:
            head += f": {node.outcome}"
        out += [head, *under(node.key)]
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
) -> str:
    """Check and keep a flow draft for ``feature_id``; return its rendering.

    A new proposal replaces the feature's previous one. Raises ``ValueError``
    naming what to fix when the draft's shape or description cover fails.
    """
    proposal = FlowProposal(
        nodes=TypeAdapter(list[ProposedNode]).validate_python(nodes),
        edges=TypeAdapter(list[ProposedEdge]).validate_python(edges),
        open_items=TypeAdapter(list[OpenItem]).validate_python(open_items),
        omitted=TypeAdapter(list[Omission]).validate_python(omitted),
    )
    canvas = read_canvas(plot_root, project_id, "feature", feature_id)
    items = feature_description_items(plot_root, project_id, feature_id)
    doc = _load(plot_root, project_id, feature_id)
    _check_shape(proposal, canvas)
    _check_cover(proposal, items, doc.drawn_items)
    _save(plot_root, project_id, feature_id, doc.model_copy(update={"current": proposal}))
    return render(proposal, canvas, items)


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
    canvas = read_canvas(plot_root, project_id, "feature", feature_id)
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
    accounted = {n for node in proposal.nodes for n in node.covers}
    accounted |= {n for item in proposal.open_items for n in item.covers}
    accounted |= {omission.item for omission in proposal.omitted}
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
