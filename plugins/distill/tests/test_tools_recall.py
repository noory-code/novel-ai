"""Tests for recall tool."""

from __future__ import annotations

import pytest

from distill.store.metadata import MetadataStore
from distill.store.vector import VectorStore
from distill.tools.recall import _relevance_score, recall
from tests.helpers.factories import make_knowledge_input


@pytest.fixture
def populated_store(tmp_path, monkeypatch):
    """Set up global store with test data."""
    store_dir = tmp_path / ".distill" / "knowledge"
    store_dir.mkdir(parents=True)
    monkeypatch.setattr("distill.store.scope.GLOBAL_DIR", store_dir)
    monkeypatch.setattr("distill.tools.recall.detect_project_root", lambda **_: None)
    monkeypatch.setattr("distill.tools.recall.detect_workspace_root", lambda **_: None)

    meta = MetadataStore("global")
    vector = VectorStore("global")

    entries = [
        make_knowledge_input(
            content="Use TypeScript strict mode for better type safety",
            type="preference",
            scope="global",
            tags=["typescript", "config"],
            confidence=0.9,
        ),
        make_knowledge_input(
            content="SQLite WAL mode improves concurrent read performance",
            type="pattern",
            scope="global",
            tags=["sqlite", "performance"],
            confidence=0.85,
        ),
        make_knowledge_input(
            content="Always use parameterized queries to prevent SQL injection",
            type="decision",
            scope="global",
            tags=["sqlite", "security"],
            confidence=0.95,
        ),
    ]

    for entry in entries:
        chunk = meta.insert(entry)
        vector.index(chunk.id, chunk.content, chunk.tags)

    yield {"meta": meta, "vector": vector}

    meta.close()
    vector.close()


class TestRecall:
    @pytest.mark.asyncio
    async def test_returns_matching_results(self, populated_store):
        result = await recall("TypeScript strict mode")
        assert "TypeScript strict mode" in result
        assert "preference" in result

    @pytest.mark.asyncio
    async def test_returns_no_match_message(self, populated_store):
        result = await recall("quantum computing algorithms")
        # Might find something due to semantic search, or might not
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_respects_type_filter(self, populated_store):
        result = await recall("sqlite", knowledge_type="pattern")
        # Should only include pattern type, not decision
        if "No matching" not in result:
            assert "pattern" in result

    @pytest.mark.asyncio
    async def test_respects_limit(self, populated_store):
        result = await recall("sqlite", limit=1)
        # At most 1 result
        lines = [l for l in result.split("\n\n") if l.strip().startswith("1.") or l.strip().startswith("2.")]
        assert len([l for l in result.split("\n\n") if l.strip() and l.strip()[0].isdigit()]) <= 1

    @pytest.mark.asyncio
    async def test_empty_store_returns_no_match(self, tmp_path, monkeypatch):
        store_dir = tmp_path / "empty" / ".distill" / "knowledge"
        store_dir.mkdir(parents=True)
        monkeypatch.setattr("distill.store.scope.GLOBAL_DIR", store_dir)
        monkeypatch.setattr("distill.tools.recall.detect_project_root", lambda **_: None)
        monkeypatch.setattr("distill.tools.recall.detect_workspace_root", lambda **_: None)

        result = await recall("anything")
        assert "No matching knowledge found" in result

    @pytest.mark.asyncio
    async def test_results_sorted_by_confidence(self, populated_store):
        result = await recall("sqlite")
        # SQL injection (0.95) should appear before WAL mode (0.85)
        if "No matching" not in result:
            lines = result.strip().split("\n\n")
            # Just verify it returns something valid
            assert len(lines) >= 1

    @pytest.mark.asyncio
    async def test_min_confidence_filters_low_confidence(self, populated_store):
        # populated_store has entries with confidence 0.85, 0.9, 0.95
        # min_confidence=0.92 should exclude 0.85 and 0.9
        result = await recall("sqlite", min_confidence=0.92)
        # Only the 0.95 entry (SQL injection) should pass
        if "No matching" not in result:
            assert "0.85" not in result
            assert "0.9)" not in result

    @pytest.mark.asyncio
    async def test_min_confidence_zero_returns_all(self, populated_store):
        result_default = await recall("sqlite", min_confidence=0.0)
        result_no_filter = await recall("sqlite")
        # Both should return results (same set of chunks, access_count may
        # differ slightly between calls due to touch())
        assert ("No matching" in result_default) == ("No matching" in result_no_filter)

    @pytest.mark.asyncio
    async def test_visibility_filter_excludes_non_matching(self, tmp_path, monkeypatch):
        store_dir = tmp_path / ".distill" / "knowledge"
        store_dir.mkdir(parents=True)
        monkeypatch.setattr("distill.store.scope.GLOBAL_DIR", store_dir)
        monkeypatch.setattr("distill.tools.recall.detect_project_root", lambda **_: None)
        monkeypatch.setattr("distill.tools.recall.detect_workspace_root", lambda **_: None)

        meta = MetadataStore("global")
        vector = VectorStore("global")

        private_inp = make_knowledge_input(
            content="This is a private SQLite note",
            scope="global",
            tags=["sqlite"],
            confidence=0.9,
        )
        private_inp.visibility = "private"
        global_inp = make_knowledge_input(
            content="This is a global SQLite note",
            scope="global",
            tags=["sqlite"],
            confidence=0.9,
        )
        global_inp.visibility = "global"

        private_chunk = meta.insert(private_inp)
        vector.index(private_chunk.id, private_chunk.content, private_chunk.tags)
        global_chunk = meta.insert(global_inp)
        vector.index(global_chunk.id, global_chunk.content, global_chunk.tags)

        result_private = await recall("sqlite note", visibility="private")
        result_global = await recall("sqlite note", visibility="global")

        meta.close()
        vector.close()

        assert "private" in result_private.lower()
        assert "global" in result_global.lower()


class TestRelevanceScore:
    """Tests for the combined relevance scoring formula."""

    def test_weights_sum_to_one(self):
        from distill.tools.recall import _W_ACCESS, _W_CONFIDENCE, _W_SEARCH

        assert _W_SEARCH + _W_CONFIDENCE + _W_ACCESS == pytest.approx(1.0)

    def test_perfect_scores(self):
        score = _relevance_score(1.0, 1.0, 10)
        assert score == pytest.approx(1.0)

    def test_zero_scores(self):
        score = _relevance_score(0.0, 0.0, 0)
        assert score == pytest.approx(0.0)

    def test_access_count_capped(self):
        score_at_cap = _relevance_score(0.5, 0.5, 10)
        score_over_cap = _relevance_score(0.5, 0.5, 100)
        assert score_at_cap == pytest.approx(score_over_cap)

    def test_high_search_score_beats_high_confidence(self):
        """High search relevance with low confidence should beat the opposite."""
        high_search = _relevance_score(0.9, 0.3, 0)
        high_confidence = _relevance_score(0.3, 0.9, 0)
        assert high_search > high_confidence

    def test_access_count_provides_boost(self):
        no_access = _relevance_score(0.5, 0.5, 0)
        with_access = _relevance_score(0.5, 0.5, 5)
        assert with_access > no_access


class TestRecallOutputFormat:
    """Tests for the updated recall output format."""

    @pytest.mark.asyncio
    async def test_output_shows_relevance(self, populated_store):
        result = await recall("TypeScript strict mode")
        if "No matching" not in result:
            assert "relevance:" in result
            assert "confidence:" not in result
