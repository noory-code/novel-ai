"""Path layout + atomic JSON read/write for the .plot store.

Split out of the folder_io god-module (D-2026-06-10-D). folder_io.py re-exports
everything, so import sites and tests are unchanged.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from mashbill.models import (
    CanvasKind,
    ProjectDoc,
)

# ---------------------------------------------------------------------------
# path helpers
# ---------------------------------------------------------------------------


def _project_dir(plot_root: Path, project_id: str) -> Path:
    """Directory holding ``project_id``'s files.

    S2 (D-2026-06-21-AB): one project per ``.noory/novel`` root, stored **flat**
    — its files live directly under ``plot_root``. A legacy nested
    ``{project_id}/`` folder is honoured only while it still physically holds a
    ``project.json`` (un-migrated ``.plot`` read by discovery, or a multi-project
    root the user hasn't reconciled). ``resolve_plot_root`` migrates a single
    nested project up to the root lazily on open.
    """
    nested = plot_root / project_id
    if (nested / "project.json").exists():
        return nested
    return plot_root


def _project_file(plot_root: Path, project_id: str) -> Path:
    return _project_dir(plot_root, project_id) / "project.json"


def _canvas_file(
    plot_root: Path,
    project_id: str,
    canvas_kind: CanvasKind,
    service_id: str | None = None,
) -> Path:
    folder = _project_dir(plot_root, project_id)
    if canvas_kind == "feature":
        if not service_id:
            raise ValueError("feature requires service_id")
        return folder / "services" / service_id / "detail.json"
    return folder / canvas_kind / "canvas.json"


def _ensure_project(plot_root: Path, project_id: str) -> Path:
    folder = _project_dir(plot_root, project_id)
    pf = folder / "project.json"
    if not pf.exists():
        raise FileNotFoundError(f"project not found: {project_id}")
    # Flat layout (folder == plot_root) addresses the lone project by the
    # root, so a mismatched id would otherwise silently address it. Verify
    # the stored id. Nested layout encodes the id in the folder name, so it
    # is already unambiguous (no extra read).
    if folder == plot_root and _read_json(pf).get("id") != project_id:
        raise FileNotFoundError(f"project not found: {project_id}")
    return folder


# ---------------------------------------------------------------------------
# atomic JSON helpers
# ---------------------------------------------------------------------------


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    """Atomic write — tmp file then rename, so readers never see half a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    tmp.replace(path)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"file not found: {path}")
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def read_project(plot_root: Path, project_id: str) -> ProjectDoc:
    _ensure_project(plot_root, project_id)
    raw = _read_json(_project_file(plot_root, project_id))
    return ProjectDoc.model_validate(raw)


def write_project(plot_root: Path, project: ProjectDoc) -> None:
    """Persist metadata, refreshing ``updated`` to now."""
    _ensure_project(plot_root, project.id)
    refreshed = project.model_copy(update={"updated": datetime.now(UTC).isoformat()})
    _write_json(
        _project_file(plot_root, project.id),
        refreshed.model_dump(),
    )


# The largest the viewer renders the round project anchor (W-00000451).
_ANCHOR_RENDER_CAP = 200.0
# Past the cap's width a long name wraps and the card grows taller (measured:
# 100 chars 200×200, 200 chars 200×316). Counted at 11 characters a line,
# 16 px a line, plus 44 px of padding — on the safe side of the measurement.
_ANCHOR_CHARS_PER_LINE = 11
_ANCHOR_LINE_HEIGHT = 16.0
_ANCHOR_PADDING = 44.0
# A rectangular card's width cap and title characters per line (same as placement).
_RECT_RENDER_CAP = 340.0
_RECT_CHARS_PER_LINE = 18


def anchor_obstacles(
    plot_root: Path, project_id: str, canvas_kind: CanvasKind
) -> tuple[tuple[float, float, float, float], ...]:
    """The project anchor's card on ``canvas_kind`` as a placement obstacle.

    The viewer draws the anchor from ``ProjectDoc.anchors``; it is not a canvas
    node, so placement would otherwise put a new card on top of it
    (W-00000451). Canvases without an anchor (feature detail) have none."""
    project = read_project(plot_root, project_id)
    anchor = project.anchors.get(canvas_kind)
    if anchor is None:
        return ()
    # A round card grows with the project name up to the viewer's 200 px width
    # cap (``max-w-[200px]`` + square), then grows taller as the name wraps; the
    # stored size is the 150 default until the viewer measures it.
    # A non-round anchor (the patch endpoint accepts a shape) renders like any
    # rectangular card: up to 340 px wide, so more characters fit a line.
    round_card = anchor.shape in ("circle", "ellipse")
    width_cap = _ANCHOR_RENDER_CAP if round_card else _RECT_RENDER_CAP
    per_line = _ANCHOR_CHARS_PER_LINE if round_card else _RECT_CHARS_PER_LINE
    lines = -(-len(project.name or "") // per_line)
    height = _ANCHOR_PADDING + _ANCHOR_LINE_HEIGHT * lines
    if round_card:
        height = max(_ANCHOR_RENDER_CAP, height)
    return ((anchor.x, anchor.y, max(anchor.width, width_cap), max(anchor.height, height)),)
