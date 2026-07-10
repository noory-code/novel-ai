"""Tests for the store tool."""

from __future__ import annotations

import pytest

from distill.tools.store import store


@pytest.fixture(autouse=True)
def isolate_global_store(tmp_path, monkeypatch):
    """Redirect GLOBAL_DIR to tmp_path so tests never write to ~/.distill/."""
    store_dir = tmp_path / ".distill-global" / "knowledge"
    store_dir.mkdir(parents=True)
    monkeypatch.setattr("distill.store.scope.GLOBAL_DIR", store_dir)


class TestStoreValidation:
    @pytest.mark.asyncio
    async def test_empty_chunks_returns_error(self, tmp_path):
        result = await store(chunks=[], session_id="s1", _project_root=str(tmp_path))
        assert "No valid knowledge chunks" in result

    @pytest.mark.asyncio
    async def test_invalid_chunks_returns_error(self, tmp_path):
        result = await store(chunks=[{"bad": "data"}], session_id="s1", _project_root=str(tmp_path))
        assert "No valid knowledge chunks" in result

    @pytest.mark.asyncio
    async def test_non_dict_chunks_ignored(self, tmp_path):
        result = await store(chunks=["not a dict", 42], session_id="s1", _project_root=str(tmp_path))
        assert "No valid knowledge chunks" in result


class TestStoreSuccess:
    @pytest.mark.asyncio
    async def test_stores_valid_chunk(self, tmp_path):
        chunks = [
            {
                "content": "Always use uv for Python dependency management",
                "type": "preference",
                "scope": "global",
                "tags": ["python", "tooling"],
                "confidence": 0.9,
            }
        ]
        result = await store(chunks=chunks, session_id="test-session", _project_root=str(tmp_path))
        assert "Stored 1/1" in result

    @pytest.mark.asyncio
    async def test_stores_multiple_chunks(self, tmp_path):
        chunks = [
            {
                "content": "Use pytest for testing",
                "type": "preference",
                "scope": "global",
                "tags": ["testing"],
                "confidence": 0.85,
            },
            {
                "content": "SQLite for local knowledge store",
                "type": "decision",
                "scope": "project",
                "tags": ["database"],
                "confidence": 0.95,
            },
        ]
        result = await store(chunks=chunks, session_id="test-session", _project_root=str(tmp_path))
        assert "Stored 2/2" in result

    @pytest.mark.asyncio
    async def test_summary_includes_content(self, tmp_path):
        chunks = [
            {
                "content": "Use black for code formatting",
                "type": "preference",
                "scope": "global",
                "tags": ["python"],
                "confidence": 0.9,
            }
        ]
        result = await store(chunks=chunks, session_id="s1", _project_root=str(tmp_path))
        assert "black" in result

    @pytest.mark.asyncio
    async def test_invalid_trigger_defaults_to_manual(self, tmp_path):
        chunks = [
            {
                "content": "Test pattern",
                "type": "pattern",
                "scope": "project",
                "tags": [],
                "confidence": 0.7,
            }
        ]
        result = await store(
            chunks=chunks, session_id="s1", trigger="invalid_trigger", _project_root=str(tmp_path)
        )
        assert "Stored 1/1" in result

    @pytest.mark.asyncio
    async def test_scope_override(self, tmp_path):
        chunks = [
            {
                "content": "Project-specific pattern",
                "type": "pattern",
                "scope": "project",
                "tags": [],
                "confidence": 0.7,
            }
        ]
        # Override to global scope
        result = await store(
            chunks=chunks, session_id="s1", scope="global", _project_root=str(tmp_path)
        )
        assert "Stored 1/1" in result

    @pytest.mark.asyncio
    async def test_project_field_populated_from_project_root(self, tmp_path):
        """project_root basename is stored in KnowledgeInput.project."""
        from distill.store.metadata import MetadataStore

        project_dir = tmp_path / "my-project"
        project_dir.mkdir()
        store_dir = project_dir / ".distill" / "knowledge"
        store_dir.mkdir(parents=True)

        chunks = [
            {
                "content": "Use Riverpod for state management",
                "type": "preference",
                "scope": "global",
                "tags": ["flutter"],
                "confidence": 0.9,
            }
        ]
        await store(chunks=chunks, session_id="s1", _project_root=str(project_dir))

        meta = MetadataStore("global")
        entries = meta.get_all()
        meta.close()

        assert len(entries) == 1
        assert entries[0].project == "my-project"

    @pytest.mark.asyncio
    async def test_conflict_type_shows_warning(self, tmp_path):
        chunks = [
            {
                "content": "Conflicting rule detected",
                "type": "conflict",
                "scope": "project",
                "tags": [],
                "confidence": 0.8,
            }
        ]
        result = await store(chunks=chunks, session_id="s1", _project_root=str(tmp_path))
        assert "CONFLICT" in result

    @pytest.mark.asyncio
    async def test_mixed_valid_invalid_chunks(self, tmp_path):
        chunks = [
            {"bad": "data"},
            {
                "content": "Valid pattern",
                "type": "pattern",
                "scope": "project",
                "tags": [],
                "confidence": 0.7,
            },
        ]
        result = await store(chunks=chunks, session_id="s1", _project_root=str(tmp_path))
        # Only 1 valid chunk
        assert "Stored 1/1" in result
