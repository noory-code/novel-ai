"""Storage and helpers shared by coach proposals the engine holds until the person confirms them.

A proposal file lives under ``<project>/<dirname>/<name>.json``. It is engine state, not part of the
canvas wire contract. Each proposal records when it was proposed so the chat layer can show the
one a turn recorded (D-2026-10-11-B).
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from mashbill.storage import _ensure_project, _project_dir, _read_json, _write_json

M = TypeVar("M", bound=BaseModel)


def now_iso() -> str:
    """The proposal timestamp format: timezone-aware ISO 8601 in UTC."""
    return datetime.now(UTC).isoformat()


def name_key(label: str) -> str:
    """A proposed name or label compared by its words, ignoring spacing."""
    return " ".join(label.split())


def proposed_since(proposed_at: str, since: datetime) -> bool:
    """Whether a proposal stamped ``proposed_at`` was recorded at or after ``since``."""
    return bool(proposed_at) and datetime.fromisoformat(proposed_at) >= since


def _path(plot_root: Path, project_id: str, dirname: str, name: str) -> Path:
    if not name or not name.replace("-", "").replace("_", "").isalnum():
        raise ValueError(f"unsafe proposal name: {name!r}")
    return _project_dir(plot_root, project_id) / dirname / f"{name}.json"


def load_proposals(plot_root: Path, project_id: str, dirname: str, name: str, model: type[M]) -> M:
    """Read one proposal file, or the model's empty default when none exists."""
    _ensure_project(plot_root, project_id)
    path = _path(plot_root, project_id, dirname, name)
    if not path.exists():
        return model()
    return model.model_validate(_read_json(path))


def save_proposals(
    plot_root: Path, project_id: str, dirname: str, name: str, doc: BaseModel
) -> None:
    """Write one proposal file."""
    _write_json(_path(plot_root, project_id, dirname, name), doc.model_dump())
