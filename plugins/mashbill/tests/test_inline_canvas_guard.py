"""Tests for the temporary canvas teardown guard."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest

from tests.conftest import _inline_canvas_fields


@pytest.mark.allows_inline_canvas("compare git internals with ordinary canvas files")
def test_inline_canvas_guard_skips_git_directories(tmp_path: Path) -> None:
    git_path = tmp_path / ".git" / "nested" / "canvas.json"
    normal_path = tmp_path / "normal" / "canvas.json"
    for path in (git_path, normal_path):
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({"nodes": [{"id": "a", "x": 1}]}), encoding="utf-8")

    assert _inline_canvas_fields(tmp_path) == [f"{normal_path}:nodes[0].x"]


def test_inline_canvas_guard_ignores_directory_vanishing_mid_walk(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vanishing = tmp_path / "vanishing"
    vanishing.mkdir()
    (vanishing / "canvas.json").write_text("{}", encoding="utf-8")
    original_scandir = os.scandir
    scanned = False

    def scandir(path: Any) -> Any:
        nonlocal scanned
        if not isinstance(path, int) and Path(path) == vanishing:
            scanned = True
            (vanishing / "canvas.json").unlink()
            vanishing.rmdir()
        return original_scandir(path)

    monkeypatch.setattr(os, "scandir", scandir)

    assert _inline_canvas_fields(tmp_path) == []
    assert scanned
