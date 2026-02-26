"""Tests for MetadataStore."""

import tempfile
import threading

import pytest

from distill.store.metadata import MetadataStore
from tests.helpers.factories import make_knowledge_input


@pytest.fixture
def store(project_root: str) -> MetadataStore:
    s = MetadataStore("project", project_root)
    yield s
    s.close()


class TestInsert:
    def test_generates_uuid_and_timestamps(self, store: MetadataStore) -> None:
        inp = make_knowledge_input(content="test insert")
        chunk = store.insert(inp)

        assert chunk.id
        assert chunk.created_at
        assert chunk.updated_at
        assert chunk.access_count == 0
        assert chunk.content == "test insert"

    def test_stores_and_retrieves_tags_as_array(self, store: MetadataStore) -> None:
        inp = make_knowledge_input(tags=["typescript", "config"])
        chunk = store.insert(inp)
        retrieved = store.get_by_id(chunk.id)

        assert retrieved is not None
        assert retrieved.tags == ["typescript", "config"]


class TestGetById:
    def test_returns_chunk_for_existing_id(self, store: MetadataStore) -> None:
        inp = make_knowledge_input(content="findable")
        chunk = store.insert(inp)
        found = store.get_by_id(chunk.id)

        assert found is not None
        assert found.content == "findable"
        assert found.type == "pattern"

    def test_returns_none_for_nonexistent_id(self, store: MetadataStore) -> None:
        found = store.get_by_id("non-existent-id")
        assert found is None


class TestSearch:
    def test_filters_by_type(self, store: MetadataStore) -> None:
        store.insert(make_knowledge_input(content="search-type-pref", type="preference"))
        store.insert(make_knowledge_input(content="search-type-dec", type="decision"))

        prefs = store.search(type="preference")
        assert all(c.type == "preference" for c in prefs)

    def test_respects_limit(self, store: MetadataStore) -> None:
        results = store.search(limit=2)
        assert len(results) <= 2


class TestTouch:
    def test_increments_access_count(self, store: MetadataStore) -> None:
        chunk = store.insert(make_knowledge_input(content="touchable"))
        assert chunk.access_count == 0

        store.touch(chunk.id)
        updated = store.get_by_id(chunk.id)
        assert updated is not None
        assert updated.access_count == 1

        store.touch(chunk.id)
        updated2 = store.get_by_id(chunk.id)
        assert updated2 is not None
        assert updated2.access_count == 2

    def test_updates_last_accessed_at(self, store: MetadataStore) -> None:
        chunk = store.insert(make_knowledge_input(content="touchable-time"))
        assert chunk.last_accessed_at is None

        store.touch(chunk.id)
        updated = store.get_by_id(chunk.id)
        assert updated is not None
        assert updated.last_accessed_at is not None


class TestMove:
    def test_preserves_id_and_created_at(self, tmp_path: str) -> None:
        src = MetadataStore("project", str(tmp_path))
        dst_path = str(tmp_path) + "_dst"
        import os
        os.makedirs(dst_path, exist_ok=True)
        dst = MetadataStore("project", dst_path)

        chunk = src.insert(make_knowledge_input(content="move me"))
        original_id = chunk.id
        original_created_at = chunk.created_at

        src.move(chunk, dst)

        assert src.get_by_id(original_id) is None
        moved = dst.get_by_id(original_id)
        assert moved is not None
        assert moved.id == original_id
        assert moved.created_at == original_created_at
        assert moved.content == "move me"

        src.close()
        dst.close()

    def test_preserves_access_count(self, tmp_path: str) -> None:
        src = MetadataStore("project", str(tmp_path))
        dst_path = str(tmp_path) + "_dst2"
        import os
        os.makedirs(dst_path, exist_ok=True)
        dst = MetadataStore("project", dst_path)

        chunk = src.insert(make_knowledge_input(content="access counted"))
        src.touch(chunk.id)
        src.touch(chunk.id)
        chunk = src.get_by_id(chunk.id)

        src.move(chunk, dst)

        moved = dst.get_by_id(chunk.id)
        assert moved is not None
        assert moved.access_count == 2

        src.close()
        dst.close()


class TestDelete:
    def test_returns_true_for_existing_entry(self, store: MetadataStore) -> None:
        chunk = store.insert(make_knowledge_input(content="deletable"))
        result = store.delete(chunk.id)
        assert result is True
        assert store.get_by_id(chunk.id) is None

    def test_returns_false_for_nonexistent_entry(self, store: MetadataStore) -> None:
        result = store.delete("non-existent")
        assert result is False


class TestStats:
    def test_returns_totals_and_breakdowns(self, store: MetadataStore) -> None:
        store.insert(make_knowledge_input(content="for stats"))
        s = store.stats()
        assert isinstance(s["total"], int)
        assert isinstance(s["byType"], dict)
        assert isinstance(s["byScope"], dict)


class TestGetAll:
    def test_returns_all_entries(self, store: MetadataStore) -> None:
        store.insert(make_knowledge_input(content="all-1"))
        store.insert(make_knowledge_input(content="all-2"))
        all_chunks = store.get_all()
        assert isinstance(all_chunks, list)
        assert len(all_chunks) >= 2


class TestCountSince:
    def test_counts_entries_after_timestamp(self, store: MetadataStore) -> None:
        store.insert(make_knowledge_input(content="count-test"))

        past = "2000-01-01T00:00:00.000Z"
        count = store.count_since(past)
        assert count > 0

        future = "2099-01-01T00:00:00.000Z"
        count_future = store.count_since(future)
        assert count_future == 0


class TestMeta:
    def test_returns_none_for_nonexistent_key(self, store: MetadataStore) -> None:
        assert store.get_meta("nonexistent_key") is None

    def test_stores_and_retrieves_value(self, store: MetadataStore) -> None:
        store.set_meta("test_key", "test_value")
        assert store.get_meta("test_key") == "test_value"

    def test_upserts_on_duplicate_key(self, store: MetadataStore) -> None:
        store.set_meta("upsert_key", "first")
        store.set_meta("upsert_key", "second")
        assert store.get_meta("upsert_key") == "second"


class TestVisibility:
    def test_insert_with_visibility(self, store: MetadataStore) -> None:
        from tests.helpers.factories import make_knowledge_input
        inp = make_knowledge_input(content="visible chunk")
        inp.visibility = "project"
        chunk = store.insert(inp)
        assert chunk.visibility == "project"
        retrieved = store.get_by_id(chunk.id)
        assert retrieved is not None
        assert retrieved.visibility == "project"

    def test_insert_without_visibility_defaults_to_none(self, store: MetadataStore) -> None:
        inp = make_knowledge_input(content="no visibility")
        chunk = store.insert(inp)
        assert chunk.visibility is None

    def test_search_filters_by_visibility(self, store: MetadataStore) -> None:
        inp_private = make_knowledge_input(content="private chunk")
        inp_private.visibility = "private"
        inp_global = make_knowledge_input(content="global chunk")
        inp_global.visibility = "global"
        store.insert(inp_private)
        store.insert(inp_global)

        private_results = store.search(visibility="private")
        global_results = store.search(visibility="global")
        assert all(c.visibility == "private" for c in private_results)
        assert all(c.visibility == "global" for c in global_results)


class TestLifecycleEvents:
    def test_add_and_retrieve_lifecycle_event(self, store: MetadataStore) -> None:
        chunk = store.insert(make_knowledge_input(content="lifecycle test"))
        event = store.add_lifecycle_event(
            chunk.id,
            "promoted",
            from_scope="project",
            to_scope="workspace",
            note="Manual promotion",
        )
        assert event.chunk_id == chunk.id
        assert event.event_type == "promoted"
        assert event.from_scope == "project"
        assert event.to_scope == "workspace"
        assert event.note == "Manual promotion"
        assert event.timestamp

        events = store.get_lifecycle(chunk.id)
        assert len(events) == 1
        assert events[0].event_type == "promoted"

    def test_multiple_lifecycle_events_ordered(self, store: MetadataStore) -> None:
        chunk = store.insert(make_knowledge_input(content="multi lifecycle"))
        store.add_lifecycle_event(chunk.id, "created")
        store.add_lifecycle_event(chunk.id, "promoted", from_scope="project", to_scope="global")
        store.add_lifecycle_event(chunk.id, "demoted", from_scope="global", to_scope="project")

        events = store.get_lifecycle(chunk.id)
        assert len(events) == 3
        assert events[0].event_type == "created"
        assert events[1].event_type == "promoted"
        assert events[2].event_type == "demoted"

    def test_get_lifecycle_empty_for_unknown_chunk(self, store: MetadataStore) -> None:
        events = store.get_lifecycle("nonexistent-id")
        assert events == []


class TestChunkRelations:
    def test_add_and_retrieve_relation(self, store: MetadataStore) -> None:
        c1 = store.insert(make_knowledge_input(content="chunk 1"))
        c2 = store.insert(make_knowledge_input(content="chunk 2"))

        relation = store.add_relation(c1.id, c2.id, "refines", confidence=0.9)
        assert relation.from_id == c1.id
        assert relation.to_id == c2.id
        assert relation.relation_type == "refines"
        assert relation.confidence == 0.9

    def test_get_relations_from_direction(self, store: MetadataStore) -> None:
        c1 = store.insert(make_knowledge_input(content="source"))
        c2 = store.insert(make_knowledge_input(content="target"))
        store.add_relation(c1.id, c2.id, "depends_on")

        from_relations = store.get_relations(c1.id, direction="from")
        assert len(from_relations) == 1
        assert from_relations[0].to_id == c2.id

        to_relations = store.get_relations(c2.id, direction="to")
        assert len(to_relations) == 1
        assert to_relations[0].from_id == c1.id

    def test_get_relations_both_directions(self, store: MetadataStore) -> None:
        c1 = store.insert(make_knowledge_input(content="a"))
        c2 = store.insert(make_knowledge_input(content="b"))
        c3 = store.insert(make_knowledge_input(content="c"))
        store.add_relation(c1.id, c2.id, "refines")
        store.add_relation(c3.id, c1.id, "contradicts")

        both = store.get_relations(c1.id, direction="both")
        assert len(both) == 2

    def test_add_relation_upserts_on_duplicate(self, store: MetadataStore) -> None:
        c1 = store.insert(make_knowledge_input(content="x"))
        c2 = store.insert(make_knowledge_input(content="y"))
        store.add_relation(c1.id, c2.id, "refines", confidence=0.5)
        store.add_relation(c1.id, c2.id, "refines", confidence=0.9)

        relations = store.get_relations(c1.id, direction="from")
        assert len(relations) == 1
        assert relations[0].confidence == 0.9

    def test_get_relations_empty_for_unknown_chunk(self, store: MetadataStore) -> None:
        relations = store.get_relations("nonexistent-id")
        assert relations == []


class TestConcurrentAccess:
    def test_concurrent_writes_succeed_with_busy_timeout(self) -> None:
        """두 개의 MetadataStore 인스턴스가 동시에 쓰기 작업을 할 때 SQLITE_BUSY 오류가 발생하지 않는지 확인."""
        with tempfile.TemporaryDirectory(prefix="distill-concurrent-meta-") as tmp:
            errors = []

            def write_to_store(store_id: int) -> None:
                try:
                    store = MetadataStore("project", tmp)
                    inp = make_knowledge_input(content=f"Concurrent write test {store_id}")
                    store.insert(inp)
                    store.close()
                except Exception as e:
                    errors.append(e)

            threads = [threading.Thread(target=write_to_store, args=(i,)) for i in range(2)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            assert len(errors) == 0, f"동시 쓰기 중 오류 발생: {errors}"

            # 두 레코드가 모두 성공적으로 저장되었는지 확인
            store = MetadataStore("project", tmp)
            all_chunks = store.get_all()
            assert len(all_chunks) == 2
            store.close()


class TestCloseIdempotency:
    def test_close_is_idempotent(self, store: MetadataStore) -> None:
        """close()를 두 번 호출해도 예외가 발생하지 않는지 확인."""
        store.close()
        store.close()  # 두 번째 호출도 안전해야 함
