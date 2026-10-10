"""Shared test guards for stored canvas files."""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from mashbill.canvas_view import _PRESENTATION_FIELDS_BY_COLLECTION


def _inline_canvas_fields(root: Path) -> list[str]:
    """Find presentation fields left in semantic canvas files below root."""
    offenders: list[str] = []
    candidates = [root] if root.is_file() else []
    if not candidates:
        for directory, subdirs, files in os.walk(root):
            subdirs[:] = [name for name in subdirs if name != ".git"]
            candidates.extend(Path(directory) / name for name in files if name.endswith(".json"))
    for path in candidates:
        if path.name not in {"canvas.json", "detail.json"} or "published" in path.parts:
            continue
        try:
            document: Any = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        if not isinstance(document, dict):
            continue
        for collection, fields in _PRESENTATION_FIELDS_BY_COLLECTION.items():
            items = document.get(collection)
            if not isinstance(items, list):
                continue
            for index, item in enumerate(items):
                if isinstance(item, dict):
                    offenders.extend(
                        f"{path}:{collection}[{index}].{field}"
                        for field in sorted(fields & item.keys())
                    )
    return offenders


@pytest.fixture(autouse=True)
def _no_inline_canvas_at_teardown(
    request: pytest.FixtureRequest, tmp_path: Path, tmp_path_factory: pytest.TempPathFactory
) -> Iterator[None]:
    """Reject presentation left in a test's temporary semantic canvas files."""
    base = tmp_path_factory.getbasetemp()
    existing = set(base.iterdir())
    yield
    marker = request.node.get_closest_marker("allows_inline_canvas")
    if marker is not None:
        assert len(marker.args) == 1 and isinstance(marker.args[0], str) and marker.args[0]
        return
    roots = {tmp_path, *(path for path in base.iterdir() if path not in existing)}
    offenders = sorted({offender for root in roots for offender in _inline_canvas_fields(root)})
    assert not offenders, "inline canvas presentation left on disk:\n" + "\n".join(offenders)
