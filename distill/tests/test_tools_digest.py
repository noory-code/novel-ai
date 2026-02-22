"""Tests for digest tool."""

from __future__ import annotations

import pytest

from distill.store.metadata import MetadataStore
from distill.tools.digest import digest, _simple_similarity
from tests.helpers.factories import make_knowledge_input


@pytest.fixture
def digest_env(tmp_path, monkeypatch):
    """Set up environment with test data for digest."""
    store_dir = tmp_path / ".distill" / "knowledge"
    store_dir.mkdir(parents=True)
    monkeypatch.setattr("distill.store.scope.GLOBAL_DIR", store_dir)
    monkeypatch.setattr("distill.tools.digest.detect_project_root", lambda **_: None)

    meta = MetadataStore("global")

    meta.insert(make_knowledge_input(
        content="Use TypeScript strict mode for better type safety in projects",
        type="pattern", scope="global", confidence=0.9,
    ))
    meta.insert(make_knowledge_input(
        content="Use TypeScript strict mode for better type safety in all projects",
        type="preference", scope="global", confidence=0.85,
    ))
    meta.insert(make_knowledge_input(
        content="Completely different topic about database indexes",
        type="decision", scope="global", confidence=0.3,
    ))

    yield meta
    meta.close()


class TestSimpleSimilarity:
    def test_identical_strings(self):
        assert _simple_similarity("hello world", "hello world") == 1.0

    def test_completely_different(self):
        assert _simple_similarity("hello world", "foo bar baz") == 0.0

    def test_partial_overlap(self):
        score = _simple_similarity("use strict mode", "use strict checking")
        assert 0.3 < score < 0.8

    def test_empty_strings(self):
        assert _simple_similarity("", "") == 0.0

    def test_case_insensitive(self):
        assert _simple_similarity("Hello World", "hello world") == 1.0


class TestDigest:
    @pytest.mark.asyncio
    async def test_detects_duplicates(self, digest_env):
        result = await digest()
        assert "Potential duplicates" in result

    @pytest.mark.asyncio
    async def test_detects_stale_entries(self, digest_env):
        result = await digest()
        # The entry with confidence 0.3 and 0 access should be stale
        assert "Stale entries" in result
        assert "database indexes" in result

    @pytest.mark.asyncio
    async def test_shows_entry_count(self, digest_env):
        result = await digest()
        assert "3 entries" in result

    @pytest.mark.asyncio
    async def test_empty_store(self, tmp_path, monkeypatch):
        store_dir = tmp_path / "empty" / ".distill" / "knowledge"
        store_dir.mkdir(parents=True)
        monkeypatch.setattr("distill.store.scope.GLOBAL_DIR", store_dir)
        monkeypatch.setattr("distill.tools.digest.detect_project_root", lambda **_: None)

        result = await digest()
        assert "0 entries" in result

    @pytest.mark.asyncio
    async def test_no_duplicates_when_distinct(self, tmp_path, monkeypatch):
        store_dir = tmp_path / "distinct" / ".distill" / "knowledge"
        store_dir.mkdir(parents=True)
        monkeypatch.setattr("distill.store.scope.GLOBAL_DIR", store_dir)
        monkeypatch.setattr("distill.tools.digest.detect_project_root", lambda **_: None)

        meta = MetadataStore("global")
        meta.insert(make_knowledge_input(content="Topic A about cats", scope="global", confidence=0.9))
        meta.insert(make_knowledge_input(content="Topic B about databases", scope="global", confidence=0.9))

        result = await digest()
        assert "No duplicates detected" in result
        meta.close()
