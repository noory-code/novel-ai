"""Tests for VectorStore and sanitize_fts_query."""

import tempfile

import pytest

from distill.store.vector import VectorStore, sanitize_fts_query


# --- sanitize_fts_query (pure function, no deps) ---


class TestSanitizeFtsQuery:
    def test_strips_special_characters(self) -> None:
        result = sanitize_fts_query("hello! world@#$")
        assert "hello" in result
        assert "world" in result
        assert "!" not in result
        assert "@" not in result

    def test_returns_empty_string_for_empty_input(self) -> None:
        assert sanitize_fts_query("") == ""
        assert sanitize_fts_query("   ") == ""

    def test_joins_tokens_with_or(self) -> None:
        result = sanitize_fts_query("typescript config")
        assert "OR" in result
        assert '"typescript"' in result
        assert '"config"' in result

    def test_handles_unicode_characters(self) -> None:
        result = sanitize_fts_query("한글 테스트")
        assert "한글" in result
        assert "테스트" in result


# --- VectorStore ---


@pytest.fixture
def vec_store(project_root: str) -> VectorStore:
    s = VectorStore("project", project_root)
    yield s
    s.close()


class TestVectorStoreCreation:
    def test_creates_both_tables(self, vec_store: VectorStore) -> None:
        # If constructor didn't throw, both tables exist
        assert vec_store is not None


class TestFtsSearch:
    def test_returns_empty_for_nonexistent_keyword(self, vec_store: VectorStore) -> None:
        results = vec_store.fts_search("nonexistentkeywordxyz")
        assert len(results) == 0

    def test_returns_empty_for_empty_query(self, vec_store: VectorStore) -> None:
        results = vec_store.fts_search("")
        assert len(results) == 0


class TestVectorSearch:
    def test_indexes_and_searches_via_similarity(self, vec_store: VectorStore) -> None:
        vec_store.index("v1", "TypeScript strict mode is recommended for all projects", ["typescript"])
        vec_store.index("v2", "Python virtual environments are useful for isolation", ["python"])

        results = vec_store.search("TypeScript strict mode")
        assert len(results) > 0
        assert results[0].id == "v1"
        assert results[0].score > 0

    def test_returns_empty_for_no_indexed_data(self) -> None:
        with tempfile.TemporaryDirectory(prefix="distill-vec-empty-") as tmp:
            s = VectorStore("project", tmp)
            results = s.search("anything")
            assert len(results) == 0
            s.close()

    def test_removes_entries_from_both_indexes(self, vec_store: VectorStore) -> None:
        vec_store.index("v-remove", "Removable content for testing removal", ["test"])
        before = vec_store.search("Removable content testing removal")
        assert any(r.id == "v-remove" for r in before)

        vec_store.remove("v-remove")

        after = vec_store.search("Removable content testing removal")
        assert not any(r.id == "v-remove" for r in after)

    def test_respects_limit_parameter(self, vec_store: VectorStore) -> None:
        vec_store.index("v-lim1", "limit test alpha content embedding", ["limit"])
        vec_store.index("v-lim2", "limit test beta content embedding", ["limit"])
        vec_store.index("v-lim3", "limit test gamma content embedding", ["limit"])

        results = vec_store.search("limit test content", 2)
        assert len(results) <= 2

    def test_search_returns_tags_as_array(self, vec_store: VectorStore) -> None:
        vec_store.index("v-tags", "Tags test content for array verification", ["typescript", "config"])
        results = vec_store.search("Tags test array")
        assert len(results) > 0
        assert isinstance(results[0].tags, list)

    def test_fts_search_works_after_index(self, vec_store: VectorStore) -> None:
        vec_store.index("v-fts", "FTS keyword search test content", ["fts"])
        results = vec_store.fts_search("keyword search")
        assert len(results) > 0
        assert results[0].id == "v-fts"
