"""Render a feature detail canvas into the format F ``## UX 흐름`` body (spec §4)."""

from __future__ import annotations

from typing import Any

from mashbill.models import CanvasDoc


def _render_feature_flow(detail: CanvasDoc) -> str:
    """Render a feature's UX flow as one numbered graph followed by its rules.
    Numbers follow a depth-first walk in edge order, including loops. Rules name
    linked numbers; unreached flow nodes and unlinked rules follow by node id.
    """
    by_id = {n.id: n for n in detail.nodes}
    lines: list[str] = []

    subjects = [
        (n.label or "").removeprefix("→ ").strip() for n in detail.nodes if n.kind == "actor_ref"
    ]
    subjects = [s for s in subjects if s]
    if subjects:
        lines.append(f"참여자: {', '.join(subjects)}")
        lines.append("")

    flow = {n.id for n in detail.nodes if n.kind in {"step", "decision"}}
    outgoing: dict[str, list[Any]] = {node_id: [] for node_id in flow}
    for edge in detail.edges:
        if edge.source in flow and edge.target in flow:
            outgoing[edge.source].append(edge)

    ordered_ids: list[str] = []
    visited: set[str] = set()

    def visit(start: str) -> None:
        stack = [start]
        while stack:
            node_id = stack.pop()
            if node_id not in visited:
                visited.add(node_id)
                ordered_ids.append(node_id)
                stack.extend(edge.target for edge in reversed(outgoing[node_id]))

    actors = {n.id for n in detail.nodes if n.kind == "actor_ref"}
    starts = [e.target for e in detail.edges if e.source in actors and e.target in flow]
    if not starts:
        incoming = {e.target for e in detail.edges if e.source in flow and e.target in flow}
        starts = sorted(flow - incoming)
    for node_id in starts:
        visit(node_id)
    ordered_ids.extend(sorted(flow - visited))
    number_by_id = {node_id: number for number, node_id in enumerate(ordered_ids, 1)}

    def node_text(node: Any, include_outcome: bool = False) -> str:
        prefix = "(분기) " if node.kind == "decision" else ""
        if node.kind == "step" and getattr(node, "polarity", "neutral") == "negative":
            prefix = "(실패) "
        outcome = getattr(node, "outcome", "") if include_outcome else ""
        return f"{prefix}{node.label}{f' → {outcome}' if outcome else ''}"

    if ordered_ids:
        lines.append("### 흐름")
        for node_id in ordered_ids:
            node = by_id[node_id]
            lines.append(f"{number_by_id[node_id]}. {node_text(node, include_outcome=True)}")
            for edge in outgoing[node_id]:
                target = by_id[edge.target]
                lines.append(
                    f"   - {edge.label or '다음'} → {number_by_id[edge.target]}. "
                    f"{node_text(target)}"
                )
        lines.append("")
    else:
        lines.append("_아직 흐름이 그려지지 않음._")
        lines.append("")

    links: dict[str, set[int]] = {n.id: set() for n in detail.nodes if n.kind == "rule"}
    for edge in detail.edges:
        if edge.source in links and edge.target in number_by_id:
            links[edge.source].add(number_by_id[edge.target])
        if edge.target in links and edge.source in number_by_id:
            links[edge.target].add(number_by_id[edge.source])

    rule_ids = sorted(
        links, key=lambda rule_id: (not links[rule_id], min(links[rule_id] or {0}), rule_id)
    )
    if rule_ids:
        lines.append("### 규칙")
        for rule_id in rule_ids:
            rule = by_id[rule_id]
            detail_text = getattr(rule, "policy", "") or getattr(rule, "body", "")
            text = f"- {rule.label}"
            if detail_text:
                text += f": {detail_text}"
            if links[rule_id]:
                linked_numbers = ", ".join(str(number) for number in sorted(links[rule_id]))
                text += f" (걸린 단계: {linked_numbers})"
            lines.append(text)
        lines.append("")

    notes = sorted((n for n in detail.nodes if n.kind == "note"), key=lambda n: n.id)
    if notes:
        lines.append("### 참고 (ambient)")
        for n in notes:
            body = getattr(n, "body", "") or ""
            lines.append(f"- {n.label}{f': {body}' if body else ''}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
