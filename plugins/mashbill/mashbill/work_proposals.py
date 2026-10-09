"""Read published format-F design and validate one proposed PlanNode."""

from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from typing import Any

from mashbill.ai_reply import first_json_object

WORK_PROPOSAL_TIMEOUT_SECONDS = 120.0

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
    for slug, (pin, folder, _) in zip(slugs, basis, strict=True):
        for path in _design_paths(slug, folder):
            content = path.read_text(encoding="utf-8")
            sections.append(f"Published design for {pin}, {path.relative_to(folder)}:\n{content}\n")
    return _PROMPT + "\n".join(sections)


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
