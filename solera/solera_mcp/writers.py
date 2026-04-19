"""Filesystem writers for the Solera workspace.

Keeps file-mutating code isolated from the pure readers so tests can run
read-only paths without touching the writer surface.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import yaml

from solera_mcp.parsing import parse_frontmatter

_log = logging.getLogger(__name__)


def update_concept_frontmatter(path: Path, updates: dict[str, Any]) -> None:
    """Merge ``updates`` into the Concept file's frontmatter and rewrite.

    - Keys with value ``None`` are **removed** from frontmatter.
    - Keys with any other value **overwrite**.
    - Frontmatter ordering is preserved for keys that already existed; new
      keys append to the end.
    - The body (everything after the second ``---``) is left untouched.
    - If the file has no frontmatter, a new block is inserted at the top.
    """
    text = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    for key, value in updates.items():
        if value is None:
            fm.pop(key, None)
        else:
            fm[key] = value
    dumped = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False).strip()
    new_text = f"---\n{dumped}\n---\n{body}" if dumped else body
    path.write_text(new_text, encoding="utf-8")


def read_layout(workspace: Path) -> dict[str, Any]:
    """Read ``_views/map-layout.json`` or return an empty layout.

    Kept alongside :func:`write_layout` rather than in :mod:`readers` because
    layout I/O is an opaque blob of canvas state, not a typed model like the
    other readers produce.
    """
    path = workspace / "_views" / "map-layout.json"
    if not path.exists():
        return {"nodes": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        _log.warning("malformed map-layout.json at %s; ignoring", path)
        return {"nodes": {}}
    if not isinstance(data, dict):
        return {"nodes": {}}
    nodes = data.get("nodes") or {}
    return {"nodes": nodes if isinstance(nodes, dict) else {}}


def write_layout(workspace: Path, layout: dict[str, Any]) -> None:
    """Persist a layout dict to ``_views/map-layout.json`` (pretty JSON).

    The schema is ``{"nodes": {"<node_id>": {"x": float, "y": float}, ...}}``.
    Arbitrary extra keys are allowed and preserved.
    """
    views_dir = workspace / "_views"
    views_dir.mkdir(parents=True, exist_ok=True)
    path = views_dir / "map-layout.json"
    path.write_text(
        json.dumps(layout, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
