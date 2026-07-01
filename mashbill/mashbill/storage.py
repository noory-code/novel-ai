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

    S2 (D-2026-06-21-AB): one project per ``.noory/plot`` root, stored **flat**
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

