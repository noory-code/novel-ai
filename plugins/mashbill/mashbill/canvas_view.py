"""Split canvas meaning and presentation across adjacent JSON files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mashbill.storage import _read_json, _write_json

_PRESENTATION_FIELDS_BY_COLLECTION = {
    "nodes": frozenset({"x", "y", "width", "height", "color", "shape", "icon", "collapsed"}),
    "edges": frozenset({"sourceHandle", "targetHandle", "style"}),
}


def view_file(path: Path) -> Path:
    """Return the presentation file beside a canvas or detail file."""
    return path.with_name(f"{path.stem}.view.json")


def split(doc_dict: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Extract stored presentation fields, keyed by graph item id."""
    semantic = dict(doc_dict)
    view: dict[str, Any] = {"nodes": {}, "edges": {}}
    for collection, fields in _PRESENTATION_FIELDS_BY_COLLECTION.items():
        items = doc_dict.get(collection)
        if not isinstance(items, list):
            continue
        semantic_items: list[Any] = []
        for item in items:
            if not isinstance(item, dict):
                semantic_items.append(item)
                continue
            item_id = item.get("id")
            presentation = {key: value for key, value in item.items() if key in fields}
            if isinstance(item_id, str) and presentation:
                view[collection][item_id] = presentation
            semantic_items.append({key: value for key, value in item.items() if key not in fields})
        semantic[collection] = semantic_items
    return semantic, view


def merge(semantic_dict: dict[str, Any], view_dict: dict[str, Any]) -> dict[str, Any]:
    """Overlay presentation only for ids present in the semantic document."""
    merged = dict(semantic_dict)
    for collection, fields in _PRESENTATION_FIELDS_BY_COLLECTION.items():
        items = semantic_dict.get(collection)
        entries = view_dict.get(collection)
        if not isinstance(items, list) or not isinstance(entries, dict):
            continue
        merged_items: list[Any] = []
        for item in items:
            if not isinstance(item, dict):
                merged_items.append(item)
                continue
            entry = entries.get(item.get("id"))
            if isinstance(entry, dict):
                presentation = {key: value for key, value in entry.items() if key in fields}
                merged_items.append({**item, **presentation})
            else:
                merged_items.append(item)
        merged[collection] = merged_items
    return merged


def _has_inline_presentation(doc: dict[str, Any]) -> bool:
    for collection, fields in _PRESENTATION_FIELDS_BY_COLLECTION.items():
        items = doc.get(collection)
        if isinstance(items, list) and any(
            isinstance(item, dict) and not fields.isdisjoint(item) for item in items
        ):
            return True
    return False


def read_canvas_files(path: Path) -> dict[str, Any] | None:
    """Read both files, upgrading an older inline canvas on first read."""
    if not path.is_file():
        return None
    semantic = _read_json(path)
    presentation = _read_json(view_file(path)) if view_file(path).is_file() else {}
    doc = merge(semantic, presentation)
    if _has_inline_presentation(semantic):
        write_canvas_files(path, doc)
    return doc


def _write_if_changed(path: Path, payload: dict[str, Any]) -> None:
    serialized = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
    if path.is_file() and path.read_bytes() == serialized:
        return
    _write_json(path, payload)


def write_canvas_files(path: Path, doc_dict: dict[str, Any]) -> None:
    """Write meaning first and presentation second, skipping unchanged bytes."""
    semantic, presentation = split(doc_dict)
    _write_if_changed(path, semantic)
    _write_if_changed(view_file(path), presentation)
