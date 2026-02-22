"""Shared pytest fixtures for Distill tests."""

from __future__ import annotations

import pytest
from pathlib import Path


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    """Create a temporary project root with .distill and .claude directories."""
    (tmp_path / ".distill" / "knowledge").mkdir(parents=True)
    (tmp_path / ".claude" / "rules").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def global_root(tmp_path: Path) -> Path:
    """Create a temporary global home with .distill directory."""
    (tmp_path / ".distill" / "knowledge").mkdir(parents=True)
    return tmp_path
