"""Tests for store/scope.py — walk-up root detection."""

from __future__ import annotations

import os

import pytest

from distill.store.scope import (
    detect_project_root,
    detect_workspace_root,
    resolve_db_path,
    resolve_store_path,
)


class TestDetectProjectRoot:
    def test_finds_pyproject_toml_in_cwd(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[project]")
        result = detect_project_root(str(tmp_path))
        assert result == str(tmp_path)

    def test_finds_package_json_in_cwd(self, tmp_path):
        (tmp_path / "package.json").write_text("{}")
        result = detect_project_root(str(tmp_path))
        assert result == str(tmp_path)

    def test_finds_claude_md_in_cwd(self, tmp_path):
        (tmp_path / "CLAUDE.md").write_text("# Project")
        result = detect_project_root(str(tmp_path))
        assert result == str(tmp_path)

    def test_walks_up_to_find_marker(self, tmp_path):
        """Marker in parent, CWD is a subdirectory."""
        (tmp_path / "pyproject.toml").write_text("[project]")
        subdir = tmp_path / "src" / "myapp"
        subdir.mkdir(parents=True)
        result = detect_project_root(str(subdir))
        assert result == str(tmp_path)

    def test_returns_none_when_no_marker(self, tmp_path):
        empty = tmp_path / "no_markers"
        empty.mkdir()
        result = detect_project_root(str(empty))
        assert result is None

    def test_does_not_use_git_as_marker(self, tmp_path):
        """A plain .git dir should NOT count as project root marker."""
        (tmp_path / ".git").mkdir()
        result = detect_project_root(str(tmp_path))
        assert result is None

    def test_stops_at_nearest_ancestor(self, tmp_path):
        """If both parent and grandparent have markers, stop at nearest."""
        (tmp_path / "pyproject.toml").write_text("[project]")
        child = tmp_path / "child"
        child.mkdir()
        (child / "pyproject.toml").write_text("[project.child]")
        grandchild = child / "sub"
        grandchild.mkdir()
        result = detect_project_root(str(grandchild))
        assert result == str(child)


class TestDetectWorkspaceRoot:
    def test_finds_git_in_cwd(self, tmp_path):
        (tmp_path / ".git").mkdir()
        result = detect_workspace_root(str(tmp_path))
        assert result == str(tmp_path)

    def test_walks_up_to_find_git(self, tmp_path):
        (tmp_path / ".git").mkdir()
        subdir = tmp_path / "packages" / "app"
        subdir.mkdir(parents=True)
        result = detect_workspace_root(str(subdir))
        assert result == str(tmp_path)

    def test_returns_none_when_no_git(self, tmp_path):
        empty = tmp_path / "no_git"
        empty.mkdir()
        result = detect_workspace_root(str(empty))
        assert result is None

    def test_project_and_workspace_can_be_same(self, tmp_path):
        """Single-repo: git root is also project root (same path returned for both)."""
        (tmp_path / ".git").mkdir()
        (tmp_path / "pyproject.toml").write_text("[project]")
        proj = detect_project_root(str(tmp_path))
        ws = detect_workspace_root(str(tmp_path))
        assert proj == ws == str(tmp_path)

    def test_project_and_workspace_differ_in_monorepo(self, tmp_path):
        """Monorepo: workspace root (.git) is above project root (pyproject.toml)."""
        (tmp_path / ".git").mkdir()
        app_dir = tmp_path / "apps" / "web"
        app_dir.mkdir(parents=True)
        (app_dir / "pyproject.toml").write_text("[project]")

        proj = detect_project_root(str(app_dir))
        ws = detect_workspace_root(str(app_dir))

        assert proj == str(app_dir)
        assert ws == str(tmp_path)
        assert proj != ws


class TestResolveStorePath:
    def test_global_scope_returns_global_dir(self, tmp_path, monkeypatch):
        global_store = tmp_path / ".distill" / "knowledge"
        global_store.mkdir(parents=True)
        monkeypatch.setattr("distill.store.scope.GLOBAL_DIR", global_store)
        result = resolve_store_path("global")
        assert result == global_store

    def test_project_scope_requires_project_root(self):
        with pytest.raises(ValueError, match="project"):
            resolve_store_path("project", project_root=None)

    def test_workspace_scope_requires_workspace_root(self):
        with pytest.raises(ValueError, match="workspace"):
            resolve_store_path("workspace", workspace_root=None)

    def test_workspace_scope_under_workspace_dir(self, tmp_path):
        result = resolve_store_path("workspace", workspace_root=str(tmp_path))
        assert str(tmp_path) in str(result)
        assert "knowledge" in str(result)


class TestResolveDbPath:
    def test_returns_metadata_db_filename(self, tmp_path, monkeypatch):
        global_store = tmp_path / ".distill" / "knowledge"
        global_store.mkdir(parents=True)
        monkeypatch.setattr("distill.store.scope.GLOBAL_DIR", global_store)
        result = resolve_db_path("global")
        assert result.name == "metadata.db"
