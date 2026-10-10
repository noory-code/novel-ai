"""Canonical blueprint canvas normalization and content fingerprinting."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any

from mashbill.canvas_view import is_view_file, split

_PUBLISHED_DIRNAME = "published"

# Canvas presentation is not blueprint content. Keep these deny-lists explicit:
# an unknown future field is content by default, which may cause an extra publish
# rather than silently omitting a design change.
_INVALID_CANVAS = object()


def blueprint_content_fingerprint(workspace_root: Path, project_dir: Path) -> str | None:
    """Return the normalized on-disk blueprint canvas SHA-256, if readable."""
    from mashbill.project_io import _PRIMARY_CANVASES

    data_root = workspace_root / ".noory" / "novel"
    design_by_path: dict[str, Any] = {}
    try:
        for canvas_kind in _PRIMARY_CANVASES:
            canvas_root = project_dir / canvas_kind
            if not canvas_root.is_dir():
                continue
            for path in canvas_root.rglob("*.json"):
                relative_canvas_path = path.relative_to(canvas_root)
                if (
                    _PUBLISHED_DIRNAME in relative_canvas_path.parts
                    or is_view_file(path)
                    or not path.is_file()
                ):
                    continue
                canvas = _read_canvas_json(path)
                if canvas is _INVALID_CANVAS:
                    return None
                design = _canvas_design_content(canvas)
                if design is _INVALID_CANVAS:
                    return None
                relative_data_path = path.resolve().relative_to(data_root.resolve())
                design_by_path[PurePosixPath(relative_data_path.as_posix()).as_posix()] = design
        serialized = json.dumps(
            design_by_path,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (OSError, UnicodeError, ValueError, TypeError):
        return None
    return hashlib.sha256(serialized).hexdigest()


def _read_canvas_json(path: Path) -> Any:
    try:
        return _load_canvas_json(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return _INVALID_CANVAS


def _load_canvas_json(raw: str) -> Any:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return _INVALID_CANVAS


def _canvas_design_content(canvas: Any) -> Any:
    """Return JSON content with presentation-only graph fields removed."""
    if not isinstance(canvas, dict):
        return canvas
    content, presentation = split(canvas)
    for collection_name in presentation:
        collection = content.get(collection_name)
        if not isinstance(collection, list):
            continue
        by_id: dict[str, dict[str, Any]] = {}
        for item in collection:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                return _INVALID_CANVAS
            item_id = item["id"]
            if item_id in by_id:
                return _INVALID_CANVAS
            by_id[item_id] = item
        content[collection_name] = by_id
    return content
