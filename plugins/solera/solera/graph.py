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


def items_by_slugs(items: dict[str, WorkItem], slugs: list[str]) -> dict[str, list[str]]:
    """Index item ids by each requested slug, including slugs with no matches."""
    by_slug: dict[str, list[str]] = {slug: [] for slug in slugs}
    for slug in by_slug:
        by_slug[slug] = [item_id for item_id, item in items.items() if slug in item.realizes]
    return by_slug


def parents(items: dict[str, WorkItem]) -> dict[str, str]:
    """Return each declared child id's parent id."""
    return {child_id: parent_id for parent_id, item in items.items() for child_id in item.children}


def cancelled_ancestor(items: dict[str, WorkItem], item_id: str) -> str | None:
    """Return the item or nearest ancestor that freezes this branch by cancellation."""
    parent_of = parents(items)
    visited: set[str] = set()
    current: str | None = item_id
    while current is not None and current not in visited:
        visited.add(current)
        item = items.get(current)
        if item is None:
            return None
        if item.status == "cancelled":
            return current
        current = parent_of.get(current)
    return None


def reaches_design_node(items: dict[str, WorkItem], item_id: str) -> bool:
    """Return whether an item or any ancestor names a format F design slug."""
    parent_of = parents(items)
    visited: set[str] = set()
    current: str | None = item_id
    while current is not None and current not in visited:
        visited.add(current)
        if items[current].realizes:
            return True
        current = parent_of.get(current)
    return False


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
        (phase, item_id): [] for item_id in items for phase in ("start", "done")
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
                rotations = [tuple(body[index:] + body[:index]) for index in range(len(body))]
                cycles.setdefault(min(rotations), cycle)
        stack.pop()
        positions.pop(item_id)
        state[item_id] = 2

    for item_id in edges:
        if state.get(item_id, 0) == 0:
            visit(item_id)
    return list(cycles.values())


def has_direct_order_cycle(items: dict[str, WorkItem]) -> bool:
    """Return whether the explicit ``after`` links alone form a cycle."""
    return bool(_after_cycles(items))


def _ancestor_sets(items: dict[str, WorkItem]) -> dict[str, set[str]]:
    parent_of = parents(items)
    result: dict[str, set[str]] = {}
    for item_id in items:
        ancestors: set[str] = set()
        current = parent_of.get(item_id)
        while current is not None and current != item_id and current not in ancestors:
            ancestors.add(current)
            current = parent_of.get(current)
        result[item_id] = ancestors
    return result


def _tree_order_problems(
    items: dict[str, WorkItem],
) -> tuple[list[tuple[str, str]], set[tuple[str, str]]]:
    """Return effective order links that point within an item's own tree chain."""
    ancestors = _ancestor_sets(items)
    problems: list[tuple[str, str]] = []
    invalid_links: set[tuple[str, str]] = set()
    for item_id in items:
        for predecessor in effective_after(items, item_id):
            if predecessor == item_id:
                kind = "order_waits_on_descendant"
                detail = f"order link can never be satisfied: {item_id} waits for itself"
            elif predecessor in ancestors[item_id]:
                kind = "order_waits_on_ancestor"
                detail = (
                    f"order link can never be satisfied: {item_id} waits for "
                    f"its ancestor {predecessor}"
                )
            elif item_id in ancestors.get(predecessor, set()):
                kind = "order_waits_on_descendant"
                detail = (
                    f"order link can never be satisfied: {item_id} waits for "
                    f"its descendant {predecessor}"
                )
            else:
                continue
            problems.append((kind, detail))
            invalid_links.add((item_id, predecessor))
    return problems, invalid_links


def order_problems(items: dict[str, WorkItem]) -> list[tuple[str, str]]:
    """Return missing targets and every unsatisfiable order relationship."""
    problems = [
        ("after-missing", f"{item_id} waits for {predecessor} which does not exist")
        for item_id, item in items.items()
        for predecessor in item.after
        if predecessor not in items
    ]
    after_cycles = _after_cycles(items)
    for after_cycle in after_cycles:
        problems.append(("after-cycle", f"order links form a cycle: {' -> '.join(after_cycle)}"))
    after_cycle_ids = [set(after_cycle[:-1]) for after_cycle in after_cycles]

    tree_problems, invalid_tree_links = _tree_order_problems(items)
    problems.extend(tree_problems)

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
        if any(
            item_id in cycle_ids and predecessor in cycle_ids
            for item_id, predecessor in invalid_tree_links
        ):
            continue
        route = " -> ".join(_node_label(node) for node in phase_cycle)
        problems.append(("after-cycle", f"order links can never be satisfied: {route}"))
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
        if not item.children or item.status == "cancelled":
            continue
        visited = {item_id}
        leaves: list[WorkItem] = []

        def collect(descendant_id: str) -> None:
            if descendant_id in visited or descendant_id not in items:
                return
            visited.add(descendant_id)
            descendant = items[descendant_id]
            if descendant.status == "cancelled":
                return
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
