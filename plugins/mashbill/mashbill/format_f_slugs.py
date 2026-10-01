"""Stable format-F slug planning and registry persistence."""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, TypedDict

from mashbill.storage import _project_dir, _read_json, _write_json

SLUG_TAIL_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SLUG_TAIL_MAX = 60

_SLUG_RE = re.compile(r"[^a-z0-9]+")
_SINGLETON_KINDS = frozenset({"mission"})


def _slugify(text: str) -> str:
    return _SLUG_RE.sub("-", text.lower()).strip("-")


def needs_english_slug(label: str) -> bool:
    return any(ch.isalpha() and not ch.isascii() for ch in label) or _slugify(label) == ""


def slug_store_path(plot_root: Path, project_id: str) -> Path:
    return _project_dir(plot_root, project_id) / "_slugs.json"


def read_slug_store(plot_root: Path, project_id: str) -> dict[str, str]:
    path = slug_store_path(plot_root, project_id)
    if not path.is_file():
        return {}
    return _read_json(path)


def read_slug_store_bytes(plot_root: Path, project_id: str) -> bytes | None:
    path = slug_store_path(plot_root, project_id)
    return path.read_bytes() if path.is_file() else None


def restore_slug_store(plot_root: Path, project_id: str, previous: bytes | None) -> None:
    path = slug_store_path(plot_root, project_id)
    if previous is None:
        path.unlink(missing_ok=True)
    else:
        path.write_bytes(previous)


class NeededNode(TypedDict):
    node_id: str
    kind: str
    label: str


SlugProblemReason = Literal["format", "taken", "duplicate", "not_needed"]


class SlugProblem(TypedDict):
    node_id: str
    slug: str
    reason: SlugProblemReason


class SlugNamesNeededError(ValueError):
    """Raised when first publication needs person-confirmed English ids."""

    def __init__(self, nodes: list[NeededNode]) -> None:
        self.nodes = nodes
        rendered = ", ".join(
            f'{node["node_id"]} ({node["kind"]}) "{node["label"]}"' for node in nodes
        )
        super().__init__(
            "These nodes need an English id before publishing. Ask the person to confirm one "
            "for each, then pass slugs={node_id: id} (lowercase letters, digits and single "
            f"hyphens): {rendered}"
        )


_PROBLEM_MESSAGES: dict[SlugProblemReason, str] = {
    "format": "use lowercase letters, digits and single hyphens only (at most 60 characters)",
    "taken": "already used by another node",
    "duplicate": "given to more than one node",
    "not_needed": "this node already has an id or takes it from its English name",
}


class InvalidSlugNamesError(ValueError):
    """Raised when supplied English ids cannot be accepted."""

    def __init__(self, problems: list[SlugProblem]) -> None:
        self.problems = problems
        rendered = ", ".join(
            f"{problem['node_id']} -> '{problem['slug']}': {_PROBLEM_MESSAGES[problem['reason']]}"
            for problem in problems
        )
        super().__init__(f"These English ids were rejected: {rendered}")


@dataclass(frozen=True)
class SlugPlan:
    slugs: dict[str, str]
    new: dict[str, str]


def _automatic_candidate(node: Any) -> str:
    if node.kind in _SINGLETON_KINDS:
        return str(node.kind)
    return f"{node.kind}/{_slugify(str(node.label or node.id))}"


def _dedupe(candidate: str, taken: set[str]) -> str:
    slug = candidate
    suffix = 2
    while slug in taken:
        slug = f"{candidate}-{suffix}"
        suffix += 1
    return slug


def _prepare(
    store: Mapping[str, str], nodes: Sequence[Any]
) -> tuple[dict[str, str], dict[str, str], list[Any], list[str]]:
    slugs: dict[str, str] = {}
    new: dict[str, str] = {}
    needed: list[Any] = []
    taken_ordered = list(dict.fromkeys(store.values()))
    taken = set(taken_ordered)

    for node in nodes:
        existing = store.get(node.id)
        if existing is not None:
            slugs[node.id] = existing
        elif node.kind != "mission" and needs_english_slug(str(node.label or "")):
            needed.append(node)

    needed_ids = {node.id for node in needed}
    for node in nodes:
        if node.id in store or node.id in needed_ids:
            continue
        slug = _dedupe(_automatic_candidate(node), taken)
        slugs[node.id] = slug
        new[node.id] = slug
        taken.add(slug)
        taken_ordered.append(slug)

    return slugs, new, needed, taken_ordered


def plan_slugs(
    store: Mapping[str, str],
    nodes: Sequence[Any],
    provided: Mapping[str, str] | None,
) -> SlugPlan:
    """Plan every stable id without mutating the registry or filesystem."""
    slugs, new, needed, taken_ordered = _prepare(store, nodes)
    supplied = provided or {}
    needed_by_id = {node.id: node for node in needed}
    taken = set(taken_ordered)

    full_ids: dict[str, str] = {}
    valid_ids: set[str] = set()
    for node_id, tail in supplied.items():
        node = needed_by_id.get(node_id)
        if node is None:
            continue
        if len(tail) <= SLUG_TAIL_MAX and SLUG_TAIL_RE.fullmatch(tail):
            full_ids[node_id] = f"{node.kind}/{tail}"
            valid_ids.add(node_id)
    duplicate_counts = Counter(full_ids.values())

    problems: list[SlugProblem] = []
    for node_id, tail in supplied.items():
        if node_id not in needed_by_id:
            problems.append({"node_id": node_id, "slug": tail, "reason": "not_needed"})
            continue
        if node_id not in valid_ids:
            problems.append({"node_id": node_id, "slug": tail, "reason": "format"})
            continue
        full_id = full_ids[node_id]
        if duplicate_counts[full_id] > 1:
            problems.append({"node_id": node_id, "slug": tail, "reason": "duplicate"})
        elif full_id in taken:
            problems.append({"node_id": node_id, "slug": tail, "reason": "taken"})
    if problems:
        raise InvalidSlugNamesError(problems)

    missing = [node for node in needed if node.id not in supplied]
    if missing:
        raise SlugNamesNeededError(
            [
                {"node_id": node.id, "kind": node.kind, "label": str(node.label or "")}
                for node in missing
            ]
        )

    for node in needed:
        slug = full_ids[node.id]
        slugs[node.id] = slug
        new[node.id] = slug
    return SlugPlan(slugs=slugs, new=new)


def pending_slug_names(
    store: Mapping[str, str], nodes: Sequence[Any]
) -> tuple[list[Any], list[str]]:
    """Return nodes needing names and ids already reserved by automatic planning."""
    _, _, needed, taken = _prepare(store, nodes)
    return needed, taken


def write_slug_store(plot_root: Path, project_id: str, store: Mapping[str, str]) -> None:
    """Persist one fully planned registry update."""
    _write_json(slug_store_path(plot_root, project_id), dict(store))
