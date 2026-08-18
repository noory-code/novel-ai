"""Tests for the self-contained Mashbill SessionStart documentation anchor."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK_PATH = ROOT / "hooks" / "session_start.py"
SPEC = importlib.util.spec_from_file_location("mashbill_session_start", HOOK_PATH)
assert SPEC is not None and SPEC.loader is not None
session_start = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(session_start)


def test_installed_plugin_finds_vision_mirror() -> None:
    vision = session_start.find_vision()

    assert vision == ROOT / "docs" / "VISION.md"
    assert "never lose sight of the essence" in session_start.read_vision_essence(vision)


def test_public_next_session_queue_has_no_private_tasks() -> None:
    assert session_start.read_next_session_queue(ROOT) == []
