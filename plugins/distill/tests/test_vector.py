"""Tests for VectorStore and sanitize_fts_query."""

import tempfile
import threading

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
        result = sanitize_fts_query("hangul test")
        assert "hangul" in result
        assert "test" in result


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


class TestConcurrentAccess:
    def test_concurrent_writes_succeed_with_busy_timeout(self) -> None:
        """Verify that two VectorStore instances writing concurrently do not raise SQLITE_BUSY."""
        with tempfile.TemporaryDirectory(prefix="distill-concurrent-") as tmp:
            # Initialize the database first (including extension loading)
            init_store = VectorStore("project", tmp)
            init_store.close()

            errors = []

            def write_to_store(store_id: int) -> None:
                try:
                    store = VectorStore("project", tmp)
                    store.index(f"concurrent-{store_id}", f"Concurrent write test content {store_id}", ["test"])
                    store.close()
                except Exception as e:
                    errors.append(e)

            threads = [threading.Thread(target=write_to_store, args=(i,)) for i in range(2)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            assert len(errors) == 0, f"Errors during concurrent writes: {errors}"

            # Verify both records were saved successfully
            store = VectorStore("project", tmp)
            results = store.search("Concurrent write test", limit=10)
            assert len(results) == 2
            store.close()


class TestHybridSearch:
    def test_combines_vector_and_fts_results(self, vec_store: VectorStore) -> None:
        vec_store.index("h1", "TypeScript strict mode config", ["typescript"])
        vec_store.index("h2", "Python virtual environments", ["python"])

        results = vec_store.hybrid_search("TypeScript strict mode")
        assert len(results) > 0
        assert results[0].id == "h1"
        assert results[0].score > 0

    def test_fts_contributes_to_ranking(self, vec_store: VectorStore) -> None:
        """FTS keyword hits should boost results that also match semantically."""
        vec_store.index("hk1", "Use SQLite WAL mode for concurrency", ["sqlite", "wal"])
        vec_store.index("hk2", "Database performance tuning guide", ["database"])

        results = vec_store.hybrid_search("SQLite WAL")
        assert len(results) > 0
        # The entry with exact keyword match should rank first
        assert results[0].id == "hk1"

    def test_deduplicates_results(self, vec_store: VectorStore) -> None:
        """Same entry from vector and FTS should appear only once."""
        vec_store.index("hd1", "Unique test content for dedup", ["test"])
        results = vec_store.hybrid_search("Unique test content dedup")
        ids = [r.id for r in results]
        assert len(ids) == len(set(ids))

    def test_returns_empty_for_no_data(self) -> None:
        with tempfile.TemporaryDirectory(prefix="distill-hybrid-") as tmp:
            s = VectorStore("project", tmp)
            results = s.hybrid_search("anything")
            assert len(results) == 0
            s.close()

    def test_respects_limit(self, vec_store: VectorStore) -> None:
        for i in range(5):
            vec_store.index(f"hl{i}", f"Hybrid limit test content {i}", ["limit"])
        results = vec_store.hybrid_search("Hybrid limit test", limit=2)
        assert len(results) <= 2


class TestCloseIdempotency:
    def test_close_is_idempotent(self, vec_store: VectorStore) -> None:
        """Verify that calling close() twice does not raise an exception."""
        vec_store.close()
        vec_store.close()  # Second call should also be safe
