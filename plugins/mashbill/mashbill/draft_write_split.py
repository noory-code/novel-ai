"""Attribute independently written fragments to a supplied coach draft."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Generic, TypeVar

from mashbill.draft_store import read_draft
from mashbill.models_draft import DraftCanvasKind

DRAFT_TEXT_WORD_OVERLAP_THRESHOLD = 0.6
DRAFT_FIELD_NAME_MAX_LENGTH = 12

_DRAFT_FIELD_PREFIX_RE = re.compile(rf"(?m)^[^\s:]{{1,{DRAFT_FIELD_NAME_MAX_LENGTH}}}:[^\S\r\n]+")
_DRAFT_REMOVED_QUOTES = str.maketrans("", "", "'\"‘’“”「」")

T = TypeVar("T")


@dataclass(frozen=True)
class WriteFragment(Generic[T]):
    """One independently attributable piece of a successful write."""

    value: T
    node_ids: tuple[str, ...] = ()
    written_texts: tuple[str, ...] = ()
    matching_node_ids: tuple[str, ...] = ()
    added_node: bool = False
    follows_matching_node: bool = False


def split_write_by_draft(
    plot_root: Path,
    project_id: str,
    draft_id: str | None,
    canvas_kind: DraftCanvasKind,
    fragments: Sequence[WriteFragment[T]],
    service_id: str | None = None,
) -> tuple[list[WriteFragment[T]], list[WriteFragment[T]]]:
    """Split write fragments into the supplied draft's share and the remainder."""
    if draft_id is None:
        return [], list(fragments)
    draft = read_draft(plot_root, project_id, draft_id)
    if draft.status == "rejected" or draft.canvas_kind != canvas_kind:
        return [], list(fragments)
    if canvas_kind == "feature" and draft.service_id != service_id:
        return [], list(fragments)

    draft_targets = set(draft.target_node_ids)
    normalized_draft_text = normalize_draft_text(draft.proposed_text)
    matching: list[WriteFragment[T]] = []
    remainder: list[WriteFragment[T]] = []
    deferred: list[WriteFragment[T]] = []
    matched_node_ids: set[str] = set()
    for fragment in fragments:
        if fragment.follows_matching_node:
            deferred.append(fragment)
            continue
        target_matches = (
            not draft_targets
            or (fragment.added_node and draft.proposed_kind is not None)
            or bool(draft_targets.intersection(fragment.node_ids))
        )
        normalized_texts = [
            normalized
            for text in fragment.written_texts
            if (normalized := normalize_draft_text(text))
        ]
        text_matches = _draft_text_matches(normalized_draft_text, normalized_texts)
        kind_matches = draft.proposed_kind is None or fragment.added_node
        if target_matches and text_matches and kind_matches:
            matching.append(fragment)
            matched_node_ids.update(fragment.matching_node_ids)
        else:
            remainder.append(fragment)

    for fragment in deferred:
        if matched_node_ids.intersection(fragment.node_ids):
            matching.append(fragment)
        else:
            remainder.append(fragment)
    return matching, remainder


def normalize_draft_text(text: str) -> str:
    """Normalize draft and written text for semantic matching."""
    normalized = text.casefold()
    normalized = normalized.replace("**", "").replace("__", "").replace("`", "")
    normalized = normalized.translate(_DRAFT_REMOVED_QUOTES)
    normalized = _DRAFT_FIELD_PREFIX_RE.sub("", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized.rstrip(".")


def _draft_text_matches(draft_text: str, written_texts: list[str]) -> bool:
    if not draft_text:
        return False
    draft_words = set(draft_text.split())
    for written_text in written_texts:
        if draft_text in written_text or written_text in draft_text:
            return True
        written_words = set(written_text.split())
        smaller_word_count = min(len(draft_words), len(written_words))
        if smaller_word_count and (
            len(draft_words.intersection(written_words)) / smaller_word_count
            >= DRAFT_TEXT_WORD_OVERLAP_THRESHOLD
        ):
            return True
    return False
