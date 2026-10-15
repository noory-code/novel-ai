"""Assign AI-declared feature coverage to work proposal nodes."""

from __future__ import annotations

from typing import Any


def assign_coverage(
    nodes: list[dict[str, Any]], chosen: list[str], reported: Any
) -> list[dict[str, str]]:
    """Set realizes from declared coverage and verify reasons for every gap."""
    allowed = set(chosen)
    covered_union: set[str] = set()

    def visit(node: dict[str, Any]) -> set[str]:
        covered = node.pop("covered", None)
        if not isinstance(covered, list) or any(
            not isinstance(slug, str) or not slug.strip() for slug in covered
        ):
            raise ValueError("each PlanNode needs covered as a list of slugs")
        if len(covered) != len(set(covered)):
            raise ValueError("covered must not contain duplicates")
        unknown = set(covered) - allowed
        if unknown:
            raise ValueError(f"covered slug was not chosen: {sorted(unknown)[0]}")
        node["realizes"] = [slug for slug in chosen if slug in covered]
        covered_union.update(covered)
        for child in node.get("children", []):
            child_covered = visit(child)
            if not child_covered <= set(covered):
                raise ValueError("a child covers a feature its parent does not cover")
        return set(covered)

    for node in nodes:
        visit(node)

    missing = [slug for slug in chosen if slug not in covered_union]
    if reported is None:
        reported = []
    if not isinstance(reported, list):
        raise ValueError("uncovered must be a list of slug and reason objects")
    reasons: dict[str, str] = {}
    for entry in reported:
        if not isinstance(entry, dict) or set(entry) != {"slug", "reason"}:
            raise ValueError("uncovered needs slug and reason")
        slug, reason = entry["slug"], entry["reason"]
        if not isinstance(slug, str) or slug not in allowed:
            raise ValueError(f"uncovered slug was not chosen: {slug}")
        if slug in reasons or not isinstance(reason, str) or not reason.strip():
            raise ValueError(f"uncovered needs one non-blank reason for {slug}")
        reasons[slug] = reason.strip()
    if set(reasons) != set(missing):
        raise ValueError("uncovered must name exactly the chosen features no item covers")
    return [{"slug": slug, "reason": reasons[slug]} for slug in missing]
