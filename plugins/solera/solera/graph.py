"""Pure graph queries over a complete in-memory WorkItem mapping."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .formats import WorkItem

if TYPE_CHECKING:
    from .workspace import Workspace

_Node = tuple[str, str]


def load_items(ws: Workspace) -> dict[str, WorkItem]:
    """Load every item in a workspace exactly once."""
    return {item_id: ws.load_item(item_id) for item_id in ws.list_items()}


def parents(items: dict[str, WorkItem]) -> dict[str, str]:
    """Return each declared child id's parent id."""
    return {
        child_id: parent_id
        for parent_id, item in items.items()
        for child_id in item.children
    }


def effective_after(items: dict[str, WorkItem], item_id: str) -> list[str]:
    """Collect an item's own and inherited order links without duplicates."""
    parent_of = parents(items)
    result: list[str] = []
    added: set[str] = set()
    visited: set[str] = set()
    current: str | None = item_id
    while current is not None and current not in visited:
        visited.add(current)
        item = items[current]
        for predecessor in item.after:
            if predecessor not in added:
                added.add(predecessor)
                result.append(predecessor)
        current = parent_of.get(current)
    return result


def waiting_on(items: dict[str, WorkItem], item_id: str) -> list[str]:
    """Return effective predecessors that are absent or not done."""
    return [
        predecessor
        for predecessor in effective_after(items, item_id)
        if predecessor not in items or items[predecessor].status != "done"
    ]


def can_start(items: dict[str, WorkItem], item_id: str) -> bool:
    """Return whether the item's complete effective order gate is satisfied."""
    return not waiting_on(items, item_id)


def _order_edges(items: dict[str, WorkItem]) -> dict[_Node, list[_Node]]:
    edges: dict[_Node, list[_Node]] = {
        (phase, item_id): []
        for item_id in items
        for phase in ("start", "done")
    }
    for item_id, item in items.items():
        for predecessor in item.after:
            if predecessor in items:
                edges[("start", item_id)].append(("done", predecessor))
        for child_id in item.children:
            if child_id not in items:
                continue
            edges[("start", child_id)].append(("start", item_id))
            edges[("done", item_id)].append(("done", child_id))
        if item.gate and not item.children:
            edges[("done", item_id)].append(("start", item_id))
    return edges


def _canonical_cycle(nodes: list[_Node]) -> tuple[_Node, ...]:
    body = nodes[:-1]
    rotations = [tuple(body[index:] + body[:index]) for index in range(len(body))]
    return min(rotations)


def _node_label(node: _Node) -> str:
    phase, item_id = node
    return f"{phase}({item_id})"


def _after_cycles(items: dict[str, WorkItem]) -> list[list[str]]:
    edges = {
        item_id: [predecessor for predecessor in item.after if predecessor in items]
        for item_id, item in items.items()
    }
    state: dict[str, int] = {}
    stack: list[str] = []
    positions: dict[str, int] = {}
    cycles: dict[tuple[str, ...], list[str]] = {}

    def visit(item_id: str) -> None:
        state[item_id] = 1
        positions[item_id] = len(stack)
        stack.append(item_id)
        for predecessor in edges[item_id]:
            if state.get(predecessor, 0) == 0:
                visit(predecessor)
            elif state.get(predecessor) == 1:
                cycle = [*stack[positions[predecessor] :], predecessor]
                body = cycle[:-1]
                rotations = [
                    tuple(body[index:] + body[:index]) for index in range(len(body))
                ]
                cycles.setdefault(min(rotations), cycle)
        stack.pop()
        positions.pop(item_id)
        state[item_id] = 2

    for item_id in edges:
        if state.get(item_id, 0) == 0:
            visit(item_id)
    return list(cycles.values())


def order_problems(items: dict[str, WorkItem]) -> list[tuple[str, str]]:
    """Return missing order targets and unsatisfiable cycles."""
    problems = [
        ("after-missing", f"{item_id} waits for {predecessor} which does not exist")
        for item_id, item in items.items()
        for predecessor in item.after
        if predecessor not in items
    ]
    after_cycles = _after_cycles(items)
    for after_cycle in after_cycles:
        problems.append(
            ("after-cycle", f"order links form a cycle: {' -> '.join(after_cycle)}")
        )
    after_cycle_ids = [set(after_cycle[:-1]) for after_cycle in after_cycles]

    edges = _order_edges(items)
    state: dict[_Node, int] = {}
    stack: list[_Node] = []
    positions: dict[_Node, int] = {}
    cycles: dict[tuple[_Node, ...], list[_Node]] = {}

    def visit(node: _Node) -> None:
        state[node] = 1
        positions[node] = len(stack)
        stack.append(node)
        for dependency in edges[node]:
            if state.get(dependency, 0) == 0:
                visit(dependency)
            elif state.get(dependency) == 1:
                cycle = [*stack[positions[dependency] :], dependency]
                cycles.setdefault(_canonical_cycle(cycle), cycle)
        stack.pop()
        positions.pop(node)
        state[node] = 2

    for node in edges:
        if state.get(node, 0) == 0:
            visit(node)

    for phase_cycle in cycles.values():
        cycle_ids = {item_id for _phase, item_id in phase_cycle[:-1]}
        if any(cycle_ids <= direct_ids for direct_ids in after_cycle_ids):
            continue
        route = " -> ".join(_node_label(node) for node in phase_cycle)
        problems.append(
            ("after-cycle", f"order links can never be satisfied: {route}")
        )
    return problems


@dataclass(frozen=True)
class Completion:
    done: int
    total: int
    percent: int | None


def completion(items: dict[str, WorkItem]) -> dict[str, Completion]:
    """Calculate leaf-descendant completion for every item with children."""
    result: dict[str, Completion] = {}
    for item_id, item in items.items():
        if not item.children:
            continue
        visited = {item_id}
        leaves: list[WorkItem] = []

        def collect(descendant_id: str) -> None:
            if descendant_id in visited or descendant_id not in items:
                return
            visited.add(descendant_id)
            descendant = items[descendant_id]
            if not descendant.children:
                leaves.append(descendant)
                return
            for child_id in descendant.children:
                collect(child_id)

        for child_id in item.children:
            collect(child_id)
        total = len(leaves)
        done = sum(leaf.status == "done" for leaf in leaves)
        result[item_id] = Completion(
            done=done,
            total=total,
            percent=done * 100 // total if total else None,
        )
    return result
