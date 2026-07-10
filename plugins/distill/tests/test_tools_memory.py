"""Tests for memory tool."""

from __future__ import annotations

import json

import pytest

from distill.store.metadata import MetadataStore
from distill.store.vector import VectorStore
from distill.tools.memory import memory
from tests.helpers.factories import make_knowledge_input
from tests.helpers.mock_server import MockContext


@pytest.fixture
def memory_env(tmp_path, monkeypatch):
    """Set up environment for memory tests."""
    store_dir = tmp_path / ".distill" / "knowledge"
    store_dir.mkdir(parents=True)
    monkeypatch.setattr("distill.store.scope.GLOBAL_DIR", store_dir)
    monkeypatch.setattr("distill.tools.memory.detect_project_root", lambda **_: None)
    monkeypatch.setattr("distill.tools.memory.detect_workspace_root", lambda **_: None)

    meta = MetadataStore("global")
    vector = VectorStore("global")

    chunk = meta.insert(make_knowledge_input(
        content="Test knowledge for memory operations",
        type="pattern",
        scope="global",
        tags=["test"],
        confidence=0.8,
    ))
    vector.index(chunk.id, chunk.content, chunk.tags)

    return {"meta": meta, "vector": vector, "chunk_id": chunk.id, "tmp_path": tmp_path}


class TestDelete:
    @pytest.mark.asyncio
    async def test_deletes_existing_entry(self, memory_env):
        result = await memory(action="delete", id=memory_env["chunk_id"])
        assert "Deleted" in result
        assert memory_env["chunk_id"] in result

    @pytest.mark.asyncio
    async def test_delete_not_found(self, memory_env):
        result = await memory(action="delete", id="nonexistent-id")
        assert "not found" in result

    @pytest.mark.asyncio
    async def test_delete_requires_id(self, memory_env):
        result = await memory(action="delete")
        assert "requires an id" in result


class TestCrystallize:
    @pytest.mark.asyncio
    async def test_crystallize_with_chunks(self, memory_env, monkeypatch):
        monkeypatch.setattr(
            "distill.tools.memory.load_config",
            lambda _: type("C", (), {"crystallize_model": "test-model"})(),
        )

        crystallize_response = json.dumps([
            {
                "topic": "test-patterns",
                "action": "create",
                "delivery": "rule",
                "rules": ["Test rule"],
                "source_ids": [memory_env["chunk_id"]],
            }
        ])
        ctx = MockContext(response=crystallize_response)

        # Mock the rules directory
        rules_dir = memory_env["tmp_path"] / ".claude" / "rules"
        rules_dir.mkdir(parents=True)

        result = await memory(action="crystallize", ctx=ctx)
        assert "Crystallized 1 knowledge chunks" in result

    @pytest.mark.asyncio
    async def test_crystallize_empty_store(self, tmp_path, monkeypatch):
        store_dir = tmp_path / "empty" / ".distill" / "knowledge"
        store_dir.mkdir(parents=True)
        monkeypatch.setattr("distill.store.scope.GLOBAL_DIR", store_dir)
        monkeypatch.setattr("distill.tools.memory.detect_project_root", lambda **_: None)
        monkeypatch.setattr("distill.tools.memory.detect_workspace_root", lambda **_: None)
        monkeypatch.setattr(
            "distill.tools.memory.load_config",
            lambda _: type("C", (), {"crystallize_model": "test-model"})(),
        )

        ctx = MockContext()
        result = await memory(action="crystallize", ctx=ctx)
        assert "No knowledge chunks to crystallize" in result


class TestPromoteDemote:
    @pytest.mark.asyncio
    async def test_promote_project_to_workspace(self, tmp_path, monkeypatch):
        """project → workspace (one step up)."""
        project_dir = tmp_path / "project"
        project_store = project_dir / ".distill" / "knowledge"
        project_store.mkdir(parents=True)
        workspace_dir = tmp_path / "workspace"
        workspace_store = workspace_dir / ".distill" / "knowledge"
        workspace_store.mkdir(parents=True)
        global_store = tmp_path / ".distill" / "knowledge"
        global_store.mkdir(parents=True)
        monkeypatch.setattr("distill.store.scope.GLOBAL_DIR", global_store)
        monkeypatch.setattr("distill.tools.memory.detect_project_root", lambda **_: str(project_dir))
        monkeypatch.setattr("distill.tools.memory.detect_workspace_root", lambda **_: str(workspace_dir))

        meta = MetadataStore("project", str(project_dir))
        vector = VectorStore("project", str(project_dir))
        chunk = meta.insert(make_knowledge_input(
            content="Promote me to workspace",
            scope="project",
            tags=["test"],
        ))
        vector.index(chunk.id, chunk.content, chunk.tags)
        meta.close()
        vector.close()

        original_id = chunk.id
        result = await memory(action="promote", id=chunk.id)
        assert "Promoted" in result
        assert "project → workspace" in result
        assert original_id in result  # ID preserved, no "New ID"

    @pytest.mark.asyncio
    async def test_promote_workspace_to_global(self, tmp_path, monkeypatch):
        """workspace → global (one step up)."""
        workspace_dir = tmp_path / "workspace"
        workspace_store = workspace_dir / ".distill" / "knowledge"
        workspace_store.mkdir(parents=True)
        global_store = tmp_path / ".distill" / "knowledge"
        global_store.mkdir(parents=True)
        monkeypatch.setattr("distill.store.scope.GLOBAL_DIR", global_store)
        monkeypatch.setattr("distill.tools.memory.detect_project_root", lambda **_: None)
        monkeypatch.setattr("distill.tools.memory.detect_workspace_root", lambda **_: str(workspace_dir))

        meta = MetadataStore("workspace", workspace_root=str(workspace_dir))
        vector = VectorStore("workspace", workspace_root=str(workspace_dir))
        chunk = meta.insert(make_knowledge_input(
            content="Promote me to global",
            scope="workspace",
            tags=["test"],
        ))
        vector.index(chunk.id, chunk.content, chunk.tags)
        meta.close()
        vector.close()

        result = await memory(action="promote", id=chunk.id)
        assert "Promoted" in result
        assert "workspace → global" in result

    @pytest.mark.asyncio
    async def test_demote_global_to_workspace(self, tmp_path, monkeypatch):
        """global → workspace (one step down)."""
        workspace_dir = tmp_path / "workspace"
        workspace_store = workspace_dir / ".distill" / "knowledge"
        workspace_store.mkdir(parents=True)
        global_store = tmp_path / ".distill" / "knowledge"
        global_store.mkdir(parents=True)
        monkeypatch.setattr("distill.store.scope.GLOBAL_DIR", global_store)
        monkeypatch.setattr("distill.tools.memory.detect_project_root", lambda **_: None)
        monkeypatch.setattr("distill.tools.memory.detect_workspace_root", lambda **_: str(workspace_dir))

        meta = MetadataStore("global")
        vector = VectorStore("global")
        chunk = meta.insert(make_knowledge_input(
            content="Demote me to workspace",
            scope="global",
            tags=["test"],
        ))
        vector.index(chunk.id, chunk.content, chunk.tags)
        meta.close()
        vector.close()

        result = await memory(action="demote", id=chunk.id)
        assert "Demoted" in result
        assert "global → workspace" in result

    @pytest.mark.asyncio
    async def test_demote_project_already_at_boundary(self, tmp_path, monkeypatch):
        """project is the lowest scope — cannot demote further."""
        project_dir = tmp_path / "project"
        project_store = project_dir / ".distill" / "knowledge"
        project_store.mkdir(parents=True)
        global_store = tmp_path / ".distill" / "knowledge"
        global_store.mkdir(parents=True)
        monkeypatch.setattr("distill.store.scope.GLOBAL_DIR", global_store)
        monkeypatch.setattr("distill.tools.memory.detect_project_root", lambda **_: str(project_dir))
        monkeypatch.setattr("distill.tools.memory.detect_workspace_root", lambda **_: None)

        meta = MetadataStore("project", str(project_dir))
        vector = VectorStore("project", str(project_dir))
        chunk = meta.insert(make_knowledge_input(
            content="Already at project boundary",
            scope="project",
            tags=["test"],
        ))
        vector.index(chunk.id, chunk.content, chunk.tags)
        meta.close()
        vector.close()

        result = await memory(action="demote", id=chunk.id)
        assert "boundary" in result or "Cannot demote" in result

    @pytest.mark.asyncio
    async def test_promote_global_already_at_boundary(self, memory_env, monkeypatch):
        """global is the highest scope — cannot promote further."""
        monkeypatch.setattr("distill.tools.memory.detect_workspace_root", lambda **_: None)
        result = await memory(action="promote", id=memory_env["chunk_id"])
        assert "boundary" in result or "Cannot promote" in result

    @pytest.mark.asyncio
    async def test_promote_records_lifecycle_event(self, tmp_path, monkeypatch):
        """Promote should record a 'promoted' lifecycle event in target store."""
        project_dir = tmp_path / "project"
        project_store = project_dir / ".distill" / "knowledge"
        project_store.mkdir(parents=True)
        workspace_dir = tmp_path / "workspace"
        workspace_store = workspace_dir / ".distill" / "knowledge"
        workspace_store.mkdir(parents=True)
        global_store = tmp_path / ".distill" / "knowledge"
        global_store.mkdir(parents=True)
        monkeypatch.setattr("distill.store.scope.GLOBAL_DIR", global_store)
        monkeypatch.setattr("distill.tools.memory.detect_project_root", lambda **_: str(project_dir))
        monkeypatch.setattr("distill.tools.memory.detect_workspace_root", lambda **_: str(workspace_dir))

        meta = MetadataStore("project", str(project_dir))
        vector = VectorStore("project", str(project_dir))
        chunk = meta.insert(make_knowledge_input(
            content="lifecycle event test",
            scope="project",
            tags=["test"],
        ))
        vector.index(chunk.id, chunk.content, chunk.tags)
        meta.close()
        vector.close()

        await memory(action="promote", id=chunk.id)

        # Check lifecycle event was recorded in workspace store
        with MetadataStore("workspace", workspace_root=str(workspace_dir)) as target_meta:
            events = target_meta.get_lifecycle(chunk.id)
        assert len(events) == 1
        assert events[0].event_type == "promoted"
        assert events[0].from_scope == "project"
        assert events[0].to_scope == "workspace"

    @pytest.mark.asyncio
    async def test_promote_not_found(self, tmp_path, monkeypatch):
        project_dir = tmp_path / "project"
        project_store = project_dir / ".distill" / "knowledge"
        project_store.mkdir(parents=True)
        global_store = tmp_path / ".distill" / "knowledge"
        global_store.mkdir(parents=True)
        monkeypatch.setattr("distill.store.scope.GLOBAL_DIR", global_store)
        monkeypatch.setattr("distill.tools.memory.detect_project_root", lambda **_: str(project_dir))
        monkeypatch.setattr("distill.tools.memory.detect_workspace_root", lambda **_: None)

        result = await memory(action="promote", id="nonexistent")
        assert "not found" in result

    @pytest.mark.asyncio
    async def test_promote_requires_id(self, memory_env):
        result = await memory(action="promote")
        assert "requires an id" in result
