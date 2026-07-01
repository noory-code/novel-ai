"""file_io — safe read/write for project-relative text files (v0.7)."""

from __future__ import annotations

from pathlib import Path

import pytest

from mashbill.file_io import (
    ExtensionNotAllowedError,
    UnsafePathError,
    ensure_folder,
    read_text_file,
    resolve_safe_path,
    uniquify_folder,
    write_text_file,
)


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    return tmp_path


# ---------------------------------------------------------------------------
# Security — path escape rejection
# ---------------------------------------------------------------------------


def test_rejects_traversal(project_root: Path) -> None:
    with pytest.raises(UnsafePathError):
        resolve_safe_path(project_root, "../etc/passwd")


def test_rejects_absolute_path(project_root: Path) -> None:
    with pytest.raises(UnsafePathError):
        resolve_safe_path(project_root, "/etc/passwd")


def test_rejects_empty_segments(project_root: Path) -> None:
    with pytest.raises(UnsafePathError):
        resolve_safe_path(project_root, "workspace//leaked")


def test_rejects_blank_path(project_root: Path) -> None:
    with pytest.raises(UnsafePathError):
        resolve_safe_path(project_root, "")


def test_rejects_escaping_symlink(project_root: Path, tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside"
    outside.mkdir(exist_ok=True)
    (outside / "secret.md").write_text("leak", encoding="utf-8")
    link = project_root / "evil"
    link.symlink_to(outside)
    with pytest.raises(UnsafePathError):
        resolve_safe_path(project_root, "evil/secret.md")


# ---------------------------------------------------------------------------
# Extension allow-list
# ---------------------------------------------------------------------------


def test_write_rejects_disallowed_extension(project_root: Path) -> None:
    with pytest.raises(ExtensionNotAllowedError):
        write_text_file(project_root, "workspace/test.py", "print('hi')")


def test_read_rejects_disallowed_extension(project_root: Path) -> None:
    (project_root / "workspace").mkdir()
    (project_root / "workspace" / "test.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ExtensionNotAllowedError):
        read_text_file(project_root, "workspace/test.json")


# ---------------------------------------------------------------------------
# Round-trip
# ---------------------------------------------------------------------------


def test_write_then_read(project_root: Path) -> None:
    write_text_file(project_root, "workspace/core/mission/index.md", "# Mission\n일상 속...")
    assert read_text_file(project_root, "workspace/core/mission/index.md") == (
        "# Mission\n일상 속..."
    )


def test_read_missing_returns_empty_string(project_root: Path) -> None:
    """Useful for Inspector open-on-missing-file flows."""
    assert read_text_file(project_root, "workspace/not-yet/index.md") == ""


def test_atomic_write_via_tmp(project_root: Path) -> None:
    """Writes go through a ``.tmp`` sibling before rename; no leftover file."""
    write_text_file(project_root, "workspace/test.md", "hello")
    target_dir = project_root / "workspace"
    assert not any(p.suffix == ".tmp" for p in target_dir.iterdir())


# ---------------------------------------------------------------------------
# Folder creation + uniquify
# ---------------------------------------------------------------------------


def test_ensure_folder_creates_index_md(project_root: Path) -> None:
    ensure_folder(project_root, "workspace/core/mission-mission")
    assert (project_root / "workspace/core/mission-mission/index.md").is_file()


def test_ensure_folder_is_idempotent(project_root: Path) -> None:
    """Second call leaves existing index.md contents untouched."""
    ensure_folder(project_root, "workspace/core/mission-mission")
    (project_root / "workspace/core/mission-mission/index.md").write_text(
        "existing content", encoding="utf-8"
    )
    ensure_folder(project_root, "workspace/core/mission-mission")
    assert (project_root / "workspace/core/mission-mission/index.md").read_text(
        encoding="utf-8"
    ) == "existing content"


def test_uniquify_returns_desired_when_free(project_root: Path) -> None:
    assert uniquify_folder(project_root, "workspace/core/a") == "workspace/core/a"


def test_uniquify_adds_suffix_on_collision(project_root: Path) -> None:
    (project_root / "workspace/core").mkdir(parents=True)
    (project_root / "workspace/core/a").mkdir()
    assert uniquify_folder(project_root, "workspace/core/a") == "workspace/core/a-2"
    (project_root / "workspace/core/a-2").mkdir()
    assert uniquify_folder(project_root, "workspace/core/a") == "workspace/core/a-3"


# ---------------------------------------------------------------------------
# Size cap
# ---------------------------------------------------------------------------


def test_write_rejects_oversized_payload(project_root: Path) -> None:
    huge = "x" * (1 * 1024 * 1024 + 1)
    with pytest.raises(ValueError, match="bytes"):
        write_text_file(project_root, "workspace/big.md", huge)
