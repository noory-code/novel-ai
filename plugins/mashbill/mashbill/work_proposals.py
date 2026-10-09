"""Read published format-F design and validate one proposed PlanNode."""

from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from typing import Any

from mashbill.ai_reply import first_json_object

WORK_PROPOSAL_TIMEOUT_SECONDS = 120.0
SPLIT_PROPOSAL_TIMEOUT_SECONDS = 180.0
NODE_PROPOSAL_TIMEOUT_SECONDS = 60.0
MAX_NODE_PROMPT_ITEMS = 200

NODE_PROPOSAL_PROMPT = (
    "Find published design nodes that could realize this blocked work item. "
    "Choose only slugs from the published nodes below. Return only JSON with "
    '{"candidates": [{"slug": "...", "reason": "..."}]}. '
    "Suggest at most three nodes, each with a short reason in the person's language. "
    "Use plain words and do not invent nodes.\n\n"
)

_PROMPT = (
    "Propose ONE work item from the published design and the person's desired outcome. "
    "Reply in the person's language (Korean for Korean input), using plain words and no code. "
    "Return only one JSON PlanNode object with key, goal, accept, conditions, "
    "pass_examples, fail_examples, and risks. accept must be person or children. "
    "Conditions are plain-word pass conditions. If accept is children, include at least "
    "one child; children and after_keys are optional only for accept children. "
    "Each child is a PlanNode. after_keys name keys in this reply. "
    "Never include a check command or a gate key anywhere. "
    "Do not include realizes or basis; Mashbill supplies those.\n\n"
)

_SPLIT_PROMPT = (
    "Split the confirmed big work item into child RESULTS. Each child is part of the big "
    "result that a person or its children finish. Return only a JSON object with "
    '{"items": [PlanNode...]}, with at least one item. Each PlanNode needs key, goal, '
    "accept (person or children), conditions, pass_examples, fail_examples, and risks. "
    "Use children only for parts of the big result; work that only has to finish first "
    "goes in after_keys, not as a child. Several results may wait for one release item, "
    "and a finished release item does not finish them. after_keys must name keys in this reply. "
    "Never repeat a goal already in existing_children. Use plain words in the person's "
    "language, never a check command, and never a gate key anywhere. Do not include "
    "realizes or basis on children; they reach the design through the parent.\n\n"
)

_SERVICE_RELEASE = re.compile(r"vS([1-9][0-9]*)\Z")
_PROJECT_RELEASE = re.compile(r"vP([1-9][0-9]*)\Z")
_FIELDS = frozenset(
    {
        "key",
        "goal",
        "accept",
        "realizes",
        "basis",
        "conditions",
        "pass_examples",
        "fail_examples",
        "risks",
        "children",
        "after_keys",
        "after",
    }
)


class UnknownSlugError(ValueError):
    """A requested slug does not occur in any published manifest."""


def _release_dirs(published: Path) -> list[tuple[int, Path, dict[str, Any]]]:
    releases: list[tuple[int, Path, dict[str, Any]]] = []
    if not published.is_dir():
        return releases
    for scope in published.iterdir():
        if not scope.is_dir() or scope.is_symlink():
            continue
        pattern = _PROJECT_RELEASE if scope.name == "_project" else _SERVICE_RELEASE
        for release_dir in scope.iterdir():
            match = pattern.fullmatch(release_dir.name)
            if not match or not release_dir.is_dir() or release_dir.is_symlink():
                continue
            manifest_path = release_dir / "manifest.json"
            if not manifest_path.is_file() or manifest_path.is_symlink():
                continue
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError):
                continue
            if (
                isinstance(manifest, dict)
                and manifest.get("release") == release_dir.name
                and manifest.get("scope") == ("project" if scope.name == "_project" else "service")
                and isinstance(manifest.get("elements"), list)
            ):
                releases.append((int(match.group(1)), release_dir, manifest))
    return releases


def latest_service_releases(project_dir: Path) -> list[tuple[str, Path, dict[str, Any]]]:
    """Return each service's latest valid published vS release in slug order."""
    latest: dict[str, tuple[int, Path, dict[str, Any]]] = {}
    for number, folder, manifest in _release_dirs(project_dir / "published"):
        service = folder.parent.name
        if service == "_project" or manifest.get("service") != f"service/{service}":
            continue
        prior = latest.get(service)
        if prior is None or number > prior[0]:
            latest[service] = (number, folder, manifest)
    return [(service, latest[service][1], latest[service][2]) for service in sorted(latest)]


def _design_line(slug: str, folder: Path) -> str:
    try:
        paths = _design_paths(slug, folder)
        content = paths[-1].read_text(encoding="utf-8")
    except (ValueError, OSError, UnicodeError):
        return ""
    in_frontmatter = False
    heading = ""
    for line in content.splitlines():
        clean = line.strip()
        if clean == "---":
            in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter or not clean:
            continue
        if clean.startswith("#"):
            if not heading:
                heading = clean[:160]
            continue
        return clean[:160]
    return heading


def published_service_nodes(
    releases: list[tuple[str, Path, dict[str, Any]]],
) -> dict[str, tuple[str, str]]:
    """Collect slug, label, and a short design line from latest service releases."""
    nodes: dict[str, tuple[str, str]] = {}
    for _, folder, manifest in releases:
        for element in manifest["elements"]:
            if not isinstance(element, dict):
                continue
            slug, label = element.get("id"), element.get("label")
            if isinstance(slug, str) and slug.strip() and isinstance(label, str):
                nodes[slug] = (label, _design_line(slug, folder))
    return nodes


def build_node_prompt(
    goal: str, conditions: list[str], ancestors: list[str], nodes: dict[str, tuple[str, str]]
) -> str:
    listed = [
        {"slug": slug, "label": label, "design": line}
        for slug, (label, line) in list(nodes.items())[:MAX_NODE_PROMPT_ITEMS]
    ]
    item = {"goal": goal, "conditions": conditions, "ancestors": ancestors}
    return (
        NODE_PROPOSAL_PROMPT
        + "Blocked item:\n"
        + json.dumps(item, ensure_ascii=False)
        + "\nPublished nodes:\n"
        + json.dumps(listed, ensure_ascii=False)
    )


async def propose_nodes(
    goal: str,
    conditions: list[str],
    ancestors: list[str],
    nodes: dict[str, tuple[str, str]],
    provider: Any,
    model: str | None,
) -> list[dict[str, str]]:
    prompt = build_node_prompt(goal, conditions, ancestors, nodes)
    raw = await asyncio.wait_for(
        provider.complete_once(prompt, model=model), timeout=NODE_PROPOSAL_TIMEOUT_SECONDS
    )
    reply = first_json_object(raw) if isinstance(raw, str) else None
    if not isinstance(reply, dict) or not isinstance(reply.get("candidates"), list):
        raise ValueError("reply must contain candidates")
    candidates: list[dict[str, str]] = []
    seen: set[str] = set()
    for candidate in reply["candidates"]:
        if not isinstance(candidate, dict):
            continue
        slug, reason = candidate.get("slug"), candidate.get("reason")
        if (
            not isinstance(slug, str)
            or slug not in nodes
            or slug in seen
            or not isinstance(reason, str)
            or not reason.strip()
        ):
            continue
        candidates.append({"slug": slug, "label": nodes[slug][0], "reason": reason})
        seen.add(slug)
        if len(candidates) == 3:
            break
    if not candidates:
        raise ValueError("reply contains no published node candidates")
    return candidates


def published_basis(project_dir: Path, slugs: list[str]) -> list[tuple[str, Path, dict[str, Any]]]:
    """Resolve each slug to the latest release that lists it, in request order."""
    releases = _release_dirs(project_dir / "published")
    result: list[tuple[str, Path, dict[str, Any]]] = []
    for slug in slugs:
        candidates = [
            (number, folder, manifest)
            for number, folder, manifest in releases
            if any(
                isinstance(element, dict) and element.get("id") == slug
                for element in manifest["elements"]
            )
        ]
        if not candidates:
            raise UnknownSlugError(slug)
        _, folder, manifest = max(candidates, key=lambda row: row[0])
        result.append((f"{slug}@{manifest['release']}", folder, manifest))
    return result


def _design_paths(slug: str, folder: Path) -> list[Path]:
    design = folder / "design"
    kind, _, tail = slug.partition("/")
    if kind == "feature" and tail:
        names = ["service.md", f"features/{tail}.md"]
    elif kind == "service" and tail:
        names = ["service.md"]
    elif kind == "entity" and tail:
        names = [f"entities/{tail}.md"]
    elif kind == "actor" and tail:
        names = ["actors.md"]
    elif slug == "mission" or (kind in {"core_value", "identity"} and tail):
        names = ["foundation.md"]
    else:
        raise ValueError(f"unsupported published slug: {slug}")
    paths = [design / name for name in names]
    if any(not path.resolve().is_relative_to(design.resolve()) for path in paths):
        raise ValueError(f"unsafe published slug: {slug}")
    return paths


def build_work_prompt(
    slugs: list[str], outcome: str, basis: list[tuple[str, Path, dict[str, Any]]]
) -> str:
    sections = [f"Person's desired outcome:\n{outcome}\n"]
    sections.extend(_published_design_sections(slugs, basis))
    return _PROMPT + "\n".join(sections)


def _published_design_sections(
    slugs: list[str], basis: list[tuple[str, Path, dict[str, Any]]]
) -> list[str]:
    sections: list[str] = []
    for slug, (pin, folder, _) in zip(slugs, basis, strict=True):
        for path in _design_paths(slug, folder):
            content = path.read_text(encoding="utf-8")
            sections.append(f"Published design for {pin}, {path.relative_to(folder)}:\n{content}\n")
    return sections


def build_split_prompt(
    item: dict[str, Any],
    existing_children: list[str],
    basis: list[tuple[str, Path, dict[str, Any]]],
) -> str:
    sections = [
        "Confirmed parent item:\n" + json.dumps(item, ensure_ascii=False) + "\n",
        "existing_children:\n" + json.dumps(existing_children, ensure_ascii=False) + "\n",
    ]
    slugs = [pin.rsplit("@", 1)[0] for pin, _, _ in basis]
    sections.extend(_published_design_sections(slugs, basis))
    return _SPLIT_PROMPT + "\n".join(sections)


def _has_gate(value: Any) -> bool:
    if isinstance(value, dict):
        return "gate" in value or any(_has_gate(child) for child in value.values())
    return isinstance(value, list) and any(_has_gate(child) for child in value)


def _string_list(node: dict[str, Any], field: str) -> list[str]:
    value = node.get(field, [])
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise ValueError(f"{field} must be a list of non-blank strings")
    return value


def validate_plan_node(node: Any, *, known_keys: set[str] | None = None) -> dict[str, Any]:
    """Validate the shared PlanNode tree and its key references."""
    if not isinstance(node, dict):
        raise ValueError("proposal must be a JSON object")
    if _has_gate(node):
        raise ValueError("gate is forbidden")
    keys: set[str] = set()
    waiting: list[str] = []

    def visit(current: Any) -> None:
        if not isinstance(current, dict) or set(current) - _FIELDS:
            raise ValueError("invalid PlanNode fields")
        key = current.get("key")
        goal = current.get("goal")
        accept = current.get("accept")
        if not isinstance(key, str) or not key.strip() or key in keys:
            raise ValueError("key must be non-blank and unique")
        if not isinstance(goal, str) or not goal.strip():
            raise ValueError("goal must be non-blank")
        if accept not in ("person", "children"):
            raise ValueError("accept must be person or children")
        keys.add(key)
        for field in (
            "realizes",
            "basis",
            "conditions",
            "pass_examples",
            "fail_examples",
            "risks",
            "after_keys",
            "after",
        ):
            _string_list(current, field)
        waiting.extend(current.get("after_keys", []))
        children = current.get("children", [])
        if not isinstance(children, list):
            raise ValueError("children must be a list")
        if accept == "children" and not children:
            raise ValueError("children acceptance needs at least one child")
        if accept == "person" and "children" in current:
            raise ValueError("person acceptance cannot have children")
        for child in children:
            visit(child)

    visit(node)
    if any(key not in keys | (known_keys or set()) for key in waiting):
        raise ValueError("after_keys must name keys in the proposal")
    return node


def validate_split_request(body: Any) -> tuple[dict[str, Any], list[str]]:
    if not isinstance(body, dict) or not isinstance(body.get("item"), dict):
        raise ValueError("'item' must be an object")
    item = body["item"]
    if not isinstance(item.get("goal"), str) or not item["goal"].strip():
        raise ValueError("'item.goal' must be a non-blank string")
    for field in ("conditions", "pass_examples", "fail_examples", "risks", "realizes", "basis"):
        _string_list(item, field)
    existing = body.get("existing_children", [])
    if not isinstance(existing, list) or any(not isinstance(goal, str) for goal in existing):
        raise ValueError("'existing_children' must be a list of strings")
    return item, existing


def validate_split_proposal(reply: Any, existing_children: list[str]) -> dict[str, Any]:
    if not isinstance(reply, dict) or set(reply) != {"items"}:
        raise ValueError("proposal must be an object with items")
    items = reply["items"]
    if not isinstance(items, list) or not items:
        raise ValueError("items must be a non-empty list")
    if _has_gate(reply):
        raise ValueError("gate is forbidden")

    nodes: list[dict[str, Any]] = []

    def collect(node: Any) -> None:
        if not isinstance(node, dict):
            raise ValueError("proposal must contain PlanNodes")
        nodes.append(node)
        children = node.get("children", [])
        if isinstance(children, list):
            for child in children:
                collect(child)

    for item in items:
        collect(item)
    keys = [node.get("key") for node in nodes]
    if any(not isinstance(key, str) for key in keys):
        raise ValueError("key must be a non-blank string")
    if len(keys) != len(set(keys)):
        raise ValueError("key must be unique across the proposal")
    known_keys = {key for key in keys if isinstance(key, str)}
    for item in items:
        validate_plan_node(item, known_keys=known_keys)
    prior_goals = {goal.strip() for goal in existing_children}
    for node in nodes:
        if node["goal"].strip() in prior_goals:
            raise ValueError("goal repeats an existing child")
        node.pop("realizes", None)
        node.pop("basis", None)
    return reply


async def propose_work_item(
    slugs: list[str],
    outcome: str,
    basis: list[tuple[str, Path, dict[str, Any]]],
    provider: Any,
    model: str | None,
) -> dict[str, Any]:
    prompt = build_work_prompt(slugs, outcome, basis)
    raw = await asyncio.wait_for(
        provider.complete_once(prompt, model=model), timeout=WORK_PROPOSAL_TIMEOUT_SECONDS
    )
    node = first_json_object(raw) if isinstance(raw, str) else None
    if node is None:
        raise ValueError("reply is not valid JSON")
    if _has_gate(node):
        raise ValueError("gate is forbidden")
    node["realizes"] = slugs
    node["basis"] = [pin for pin, _, _ in basis]
    return validate_plan_node(node)


async def propose_work_split(
    item: dict[str, Any],
    existing_children: list[str],
    basis: list[tuple[str, Path, dict[str, Any]]],
    provider: Any,
    model: str | None,
) -> dict[str, Any]:
    prompt = build_split_prompt(item, existing_children, basis)
    raw = await asyncio.wait_for(
        provider.complete_once(prompt, model=model), timeout=SPLIT_PROPOSAL_TIMEOUT_SECONDS
    )
    reply = first_json_object(raw) if isinstance(raw, str) else None
    if reply is None:
        raise ValueError("reply is not valid JSON")
    return validate_split_proposal(reply, existing_children)
