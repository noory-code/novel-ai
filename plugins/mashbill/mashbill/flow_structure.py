"""Branching defects a machine can see in a feature flow (novel-workspace W-00000448).

A decision needs at least two branches, each branch names its case, no two
branches of one decision name the same case, and every loop has a line leaving
it. An open item on a decision stands for its missing branch, and an open item
on a step inside a loop stands for its way out, so the coach asks instead of
guessing. A step with no outgoing line is a valid end. Every step and decision
also needs a way in: a draft may not take the last line into a drawn one, nor
add one nothing leads into once the canvas has lines, and an open item does not
stand for a way in (W-00000489). Whether branches overlap in meaning or miss a
case is not visible here; the coach asks about that.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from mashbill.proposal_store import name_key

# (source, target, label) — one line of the flow.
Line = tuple[str, str, str]
Defect = tuple[str, ...]


def _decision_defects(
    kinds: Mapping[str, str], lines: list[Line], open_at: set[str]
) -> list[Defect]:
    found: list[Defect] = []
    for node, kind in kinds.items():
        if kind != "decision":
            continue
        branches = [line for line in lines if line[0] == node]
        if len(branches) < 2 and node not in open_at:
            found.append(("few", node, str(len(branches))))
        seen: set[str] = set()
        for _, target, label in branches:
            words = name_key(label)
            if not words:
                found.append(("unlabeled", node, target))
            elif words in seen:
                found.append(("same", node, words))
            seen.add(words)
    return found


def _reach(start: str, follow: Mapping[str, list[str]]) -> set[str]:
    seen: set[str] = set()
    stack = list(follow.get(start, []))
    while stack:
        node = stack.pop()
        if node not in seen:
            seen.add(node)
            stack.extend(follow.get(node, []))
    return seen


def _trapped_loops(lines: list[Line], open_at: set[str]) -> list[Defect]:
    follow: dict[str, list[str]] = {}
    for source, target, _ in lines:
        follow.setdefault(source, []).append(target)
    reach = {node: _reach(node, follow) for node in follow}
    found: list[Defect] = []
    for node in follow:
        if node not in reach[node]:
            continue
        loop = [m for m in follow if m in reach[node] and node in reach[m]]
        leaves = any(t not in loop for m in loop for t in follow[m])
        defect: Defect = ("loop", *sorted(loop))
        if not leaves and not open_at & set(loop) and defect not in found:
            found.append(defect)
    return found


def _flow(kinds: Mapping[str, str], lines: Iterable[Line]) -> list[Line]:
    return [line for line in lines if "note" not in (kinds.get(line[0]), kinds.get(line[1]))]


def _defects(kinds: Mapping[str, str], lines: list[Line], open_at: set[str]) -> list[Defect]:
    flow = _flow(kinds, lines)
    return _decision_defects(kinds, flow, open_at) + _trapped_loops(flow, open_at)


def _unreached(
    drawn_kinds: Mapping[str, str],
    kinds: Mapping[str, str],
    before: list[Line],
    after: list[Line],
) -> list[Defect]:
    """Steps and decisions the draft leaves with no way in.

    A drawn one loses its last incoming line; a new one gets none although the
    canvas already has a line to or from a step or decision (before that, a
    draft's first node is the flow's entry; a feature-root-to-actor line is not
    a flow). A drawn entry never had an incoming line, so it is not named.
    """
    old = _flow(drawn_kinds, before)
    into_before = {target for _, target, _ in old}
    sequenced = any(
        drawn_kinds.get(end) in ("step", "decision") for line in old for end in line[:2]
    )
    into_after = {target for _, target, _ in _flow(kinds, after)}
    found: list[Defect] = []
    for node, kind in kinds.items():
        if kind not in ("step", "decision") or node in into_after:
            continue
        if node in drawn_kinds:
            if node in into_before:
                found.append(("cut", node))
        elif sequenced:
            found.append(("unreached", node))
    return found


def _message(defect: Defect, name: Mapping[str, str]) -> str:
    code, node, *rest = defect
    if code == "few":
        count = int(rest[0])
        return (
            f"decision {name[node]} has {count} branch{'' if count == 1 else 'es'}: draw a "
            "labeled line for each case, or ask in open_items where a missing case goes"
        )
    if code == "unlabeled":
        return (
            f"line {name[node]} → {name[rest[0]]} leaves a decision with no label: "
            "name the case it takes"
        )
    if code == "cut":
        return (
            f"the draft removes the last line into {name[node]}: keep it, or draw the "
            "line that reaches it now"
        )
    if code == "unreached":
        return (
            f"nothing leads into {name[node]}: draw the line that reaches it, or leave it "
            "out of this draft and ask in open_items where it happens"
        )
    if code == "same":
        return (
            f"decision {name[node]} has two branches labeled {rest[0]!r}: "
            "each branch names a different case"
        )
    steps = ", ".join(name[step] for step in (node, *rest))
    return (
        f"steps {steps} form a loop with no line leaving it: draw the way to stop or give up, "
        "or ask in open_items where it goes"
    )


def check_structure(
    drawn_kinds: Mapping[str, str],
    kinds: Mapping[str, str],
    names: Mapping[str, str],
    before: Iterable[Line],
    after: Iterable[Line],
    open_at: set[str],
) -> None:
    """Raise ``ValueError`` naming each defect the draft creates.

    ``drawn_kinds`` and ``before`` are the canvas's nodes and lines; ``kinds``
    and ``after`` add the draft's; ``open_at`` is where the draft's open items
    hang. A defect already
    in ``before`` (for example a person's half-drawn decision) is not the
    draft's and does not refuse it.
    """
    before, after = list(before), list(after)
    old = set(_defects(drawn_kinds, before, set()))
    new = [d for d in _defects(kinds, after, open_at) if d not in old]
    new += _unreached(drawn_kinds, kinds, before, after)
    if new:
        raise ValueError(
            "fix the flow's lines and branches:\n"
            + "\n".join(f"- {_message(d, names)}" for d in new)
        )
