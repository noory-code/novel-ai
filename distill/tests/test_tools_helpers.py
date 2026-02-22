"""Tests for tools helpers."""

from __future__ import annotations

import pytest

from distill.store.metadata import MetadataStore
from distill.tools.helpers import ScopeCallbackContext, for_each_scope


@pytest.fixture
def stores_dir(tmp_path):
    """Create tmp dirs for global and project stores."""
    (tmp_path / ".distill" / "knowledge").mkdir(parents=True)
    return tmp_path


class TestForEachScope:
    @pytest.mark.asyncio
    async def test_iterates_global_only_when_no_project(self, stores_dir, monkeypatch):
        monkeypatch.setattr("distill.store.scope.GLOBAL_DIR", stores_dir / ".distill" / "knowledge")
        visited: list[str] = []

        def cb(ctx: ScopeCallbackContext):
            visited.append(ctx.scope)

        await for_each_scope(None, None, cb)
        assert visited == ["global"]

    @pytest.mark.asyncio
    async def test_iterates_both_scopes_with_project(self, stores_dir, monkeypatch):
        monkeypatch.setattr("distill.store.scope.GLOBAL_DIR", stores_dir / ".distill" / "knowledge")
        project_dir = stores_dir / "myproject"
        (project_dir / ".distill" / "knowledge").mkdir(parents=True)
        visited: list[str] = []

        def cb(ctx: ScopeCallbackContext):
            visited.append(ctx.scope)

        await for_each_scope(None, str(project_dir), cb)
        assert visited == ["global", "project"]

    @pytest.mark.asyncio
    async def test_iterates_single_scope_when_specified(self, stores_dir, monkeypatch):
        monkeypatch.setattr("distill.store.scope.GLOBAL_DIR", stores_dir / ".distill" / "knowledge")
        visited: list[str] = []

        def cb(ctx: ScopeCallbackContext):
            visited.append(ctx.scope)

        await for_each_scope("global", None, cb)
        assert visited == ["global"]

    @pytest.mark.asyncio
    async def test_provides_vector_when_requested(self, stores_dir, monkeypatch):
        monkeypatch.setattr("distill.store.scope.GLOBAL_DIR", stores_dir / ".distill" / "knowledge")
        has_vector: list[bool] = []

        def cb(ctx: ScopeCallbackContext):
            has_vector.append(ctx.vector is not None)

        await for_each_scope("global", None, cb, include_vector=True)
        assert has_vector == [True]

    @pytest.mark.asyncio
    async def test_no_vector_by_default(self, stores_dir, monkeypatch):
        monkeypatch.setattr("distill.store.scope.GLOBAL_DIR", stores_dir / ".distill" / "knowledge")
        has_vector: list[bool] = []

        def cb(ctx: ScopeCallbackContext):
            has_vector.append(ctx.vector is not None)

        await for_each_scope("global", None, cb)
        assert has_vector == [False]

    @pytest.mark.asyncio
    async def test_silently_skips_missing_scope(self, stores_dir, monkeypatch):
        monkeypatch.setattr("distill.store.scope.GLOBAL_DIR", stores_dir / ".distill" / "knowledge")
        visited: list[str] = []

        def cb(ctx: ScopeCallbackContext):
            visited.append(ctx.scope)

        # project scope with no project_root should fail silently
        await for_each_scope("project", None, cb)
        assert visited == []

    @pytest.mark.asyncio
    async def test_supports_async_callback(self, stores_dir, monkeypatch):
        monkeypatch.setattr("distill.store.scope.GLOBAL_DIR", stores_dir / ".distill" / "knowledge")
        visited: list[str] = []

        async def cb(ctx: ScopeCallbackContext):
            visited.append(ctx.scope)

        await for_each_scope("global", None, cb)
        assert visited == ["global"]

    @pytest.mark.asyncio
    async def test_iterates_all_three_scopes_with_workspace(self, stores_dir, monkeypatch):
        """global + workspace + project when all three roots are available."""
        monkeypatch.setattr("distill.store.scope.GLOBAL_DIR", stores_dir / ".distill" / "knowledge")
        project_dir = stores_dir / "myproject"
        (project_dir / ".distill" / "knowledge").mkdir(parents=True)
        workspace_dir = stores_dir / "workspace"
        (workspace_dir / ".distill" / "knowledge").mkdir(parents=True)
        visited: list[str] = []

        def cb(ctx: ScopeCallbackContext):
            visited.append(ctx.scope)

        await for_each_scope(None, str(project_dir), cb, workspace_root=str(workspace_dir))
        assert visited == ["global", "workspace", "project"]

    @pytest.mark.asyncio
    async def test_iterates_global_and_workspace_without_project(self, stores_dir, monkeypatch):
        """global + workspace when project_root is None."""
        monkeypatch.setattr("distill.store.scope.GLOBAL_DIR", stores_dir / ".distill" / "knowledge")
        workspace_dir = stores_dir / "workspace"
        (workspace_dir / ".distill" / "knowledge").mkdir(parents=True)
        visited: list[str] = []

        def cb(ctx: ScopeCallbackContext):
            visited.append(ctx.scope)

        await for_each_scope(None, None, cb, workspace_root=str(workspace_dir))
        assert visited == ["global", "workspace"]

    @pytest.mark.asyncio
    async def test_workspace_scope_explicit(self, stores_dir, monkeypatch):
        """Explicit workspace scope with workspace_root passes correctly."""
        monkeypatch.setattr("distill.store.scope.GLOBAL_DIR", stores_dir / ".distill" / "knowledge")
        workspace_dir = stores_dir / "workspace"
        (workspace_dir / ".distill" / "knowledge").mkdir(parents=True)
        visited: list[str] = []

        def cb(ctx: ScopeCallbackContext):
            visited.append(ctx.scope)

        await for_each_scope("workspace", None, cb, workspace_root=str(workspace_dir))
        assert visited == ["workspace"]

    @pytest.mark.asyncio
    async def test_workspace_scope_without_workspace_root_skips(self, stores_dir, monkeypatch):
        """workspace scope without workspace_root should silently skip."""
        monkeypatch.setattr("distill.store.scope.GLOBAL_DIR", stores_dir / ".distill" / "knowledge")
        visited: list[str] = []

        def cb(ctx: ScopeCallbackContext):
            visited.append(ctx.scope)

        await for_each_scope("workspace", None, cb, workspace_root=None)
        assert visited == []
