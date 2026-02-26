"""Metadata store backed by SQLite."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone

from distill.store.scope import resolve_db_path
from distill.store.types import (
    ChunkRelation,
    KnowledgeChunk,
    KnowledgeInput,
    KnowledgeScope,
    KnowledgeSource,
    KnowledgeType,
    KnowledgeVisibility,
    LifecycleEvent,
    LifecycleEventType,
    RelationType,
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS knowledge (
  id TEXT PRIMARY KEY,
  content TEXT NOT NULL,
  type TEXT NOT NULL CHECK(type IN ('pattern','preference','decision','mistake','workaround','conflict')),
  scope TEXT NOT NULL CHECK(scope IN ('global','project','workspace')),
  visibility TEXT CHECK(visibility IN ('global','workspace','project','private')),
  project TEXT,
  tags TEXT NOT NULL DEFAULT '[]',
  session_id TEXT NOT NULL,
  trigger TEXT NOT NULL CHECK("trigger" IN ('pre_compact','session_end','manual','ingest')),
  source_timestamp TEXT NOT NULL,
  confidence REAL NOT NULL DEFAULT 0.5,
  access_count INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  last_accessed_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_knowledge_scope ON knowledge(scope);
CREATE INDEX IF NOT EXISTS idx_knowledge_type ON knowledge(type);
CREATE INDEX IF NOT EXISTS idx_knowledge_project ON knowledge(project);

CREATE TABLE IF NOT EXISTS distill_meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS lifecycle_events (
  id TEXT PRIMARY KEY,
  chunk_id TEXT NOT NULL,
  event_type TEXT NOT NULL CHECK(event_type IN ('created','promoted','demoted','crystallized','deleted')),
  from_scope TEXT CHECK(from_scope IN ('global','project','workspace')),
  to_scope TEXT CHECK(to_scope IN ('global','project','workspace')),
  timestamp TEXT NOT NULL,
  note TEXT
);

CREATE INDEX IF NOT EXISTS idx_lifecycle_chunk ON lifecycle_events(chunk_id);

CREATE TABLE IF NOT EXISTS chunk_relations (
  from_id TEXT NOT NULL,
  to_id TEXT NOT NULL,
  relation_type TEXT NOT NULL CHECK(relation_type IN ('refines','contradicts','depends_on','supersedes')),
  confidence REAL NOT NULL DEFAULT 0.8,
  created_at TEXT NOT NULL,
  PRIMARY KEY (from_id, to_id, relation_type)
);

CREATE INDEX IF NOT EXISTS idx_relations_from ON chunk_relations(from_id);
CREATE INDEX IF NOT EXISTS idx_relations_to ON chunk_relations(to_id);
"""

_MIGRATIONS = [
    "ALTER TABLE knowledge ADD COLUMN last_accessed_at TEXT",
    "ALTER TABLE knowledge ADD COLUMN visibility TEXT CHECK(visibility IN ('global','workspace','project','private'))",
    "CREATE INDEX IF NOT EXISTS idx_knowledge_visibility ON knowledge(visibility)",
    "CREATE TABLE IF NOT EXISTS lifecycle_events (id TEXT PRIMARY KEY, chunk_id TEXT NOT NULL, event_type TEXT NOT NULL CHECK(event_type IN ('created','promoted','demoted','crystallized','deleted')), from_scope TEXT CHECK(from_scope IN ('global','project','workspace')), to_scope TEXT CHECK(to_scope IN ('global','project','workspace')), timestamp TEXT NOT NULL, note TEXT)",
    "CREATE INDEX IF NOT EXISTS idx_lifecycle_chunk ON lifecycle_events(chunk_id)",
    "CREATE TABLE IF NOT EXISTS chunk_relations (from_id TEXT NOT NULL, to_id TEXT NOT NULL, relation_type TEXT NOT NULL CHECK(relation_type IN ('refines','contradicts','depends_on','supersedes')), confidence REAL NOT NULL DEFAULT 0.8, created_at TEXT NOT NULL, PRIMARY KEY (from_id, to_id, relation_type))",
    "CREATE INDEX IF NOT EXISTS idx_relations_from ON chunk_relations(from_id)",
    "CREATE INDEX IF NOT EXISTS idx_relations_to ON chunk_relations(to_id)",
]


def _row_to_chunk(row: sqlite3.Row) -> KnowledgeChunk:
    """Convert a SQLite row to a KnowledgeChunk."""
    keys = row.keys()
    return KnowledgeChunk(
        id=row["id"],
        content=row["content"],
        type=row["type"],
        scope=row["scope"],
        visibility=row["visibility"] if "visibility" in keys else None,
        project=row["project"],
        tags=json.loads(row["tags"]),
        source=KnowledgeSource(
            session_id=row["session_id"],
            timestamp=row["source_timestamp"],
            trigger=row["trigger"],
        ),
        confidence=row["confidence"],
        access_count=row["access_count"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        last_accessed_at=row["last_accessed_at"] if "last_accessed_at" in keys else None,
    )


class MetadataStore:
    def __init__(
        self,
        scope: KnowledgeScope,
        project_root: str | None = None,
        workspace_root: str | None = None,
    ) -> None:
        db_path = resolve_db_path(scope, project_root, workspace_root)
        self._conn_impl: sqlite3.Connection | None = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn_impl.row_factory = sqlite3.Row

        # WAL 모드가 이미 설정되어 있는지 확인 후 설정
        row = self._conn_impl.execute("PRAGMA journal_mode").fetchone()
        if row and row[0].lower() != "wal":
            self._conn_impl.execute("PRAGMA journal_mode = WAL")

        self._conn_impl.execute("PRAGMA busy_timeout = 5000")
        self._conn_impl.executescript(SCHEMA)
        self._apply_migrations()

    @property
    def _conn(self) -> sqlite3.Connection:
        """내부 연결 객체 접근 (None 체크 포함)."""
        if self._conn_impl is None:
            raise RuntimeError("Database connection is closed")
        return self._conn_impl

    def _apply_migrations(self) -> None:
        """Apply schema migrations that may fail if column already exists."""
        for sql in _MIGRATIONS:
            try:
                self._conn.execute(sql)
                self._conn.commit()
            except sqlite3.OperationalError:
                pass  # column already exists

    def insert(self, input: KnowledgeInput) -> KnowledgeChunk:
        """Insert a new knowledge chunk, returns full chunk with generated id/timestamps."""
        now = datetime.now(timezone.utc).isoformat()
        chunk_id = str(uuid.uuid4())

        self._conn.execute(
            """INSERT INTO knowledge
               (id, content, type, scope, visibility, project, tags, session_id, "trigger",
                source_timestamp, confidence, access_count, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)""",
            (
                chunk_id,
                input.content,
                input.type,
                input.scope,
                input.visibility,
                input.project,
                json.dumps(input.tags),
                input.source.session_id,
                input.source.trigger,
                input.source.timestamp,
                input.confidence,
                now,
                now,
            ),
        )
        self._conn.commit()

        return KnowledgeChunk(
            id=chunk_id,
            content=input.content,
            type=input.type,
            scope=input.scope,
            visibility=input.visibility,
            project=input.project,
            tags=input.tags,
            source=input.source,
            confidence=input.confidence,
            access_count=0,
            created_at=now,
            updated_at=now,
        )

    def get_by_id(self, id: str) -> KnowledgeChunk | None:
        """Get a knowledge chunk by ID."""
        cur = self._conn.execute("SELECT * FROM knowledge WHERE id = ?", (id,))
        row = cur.fetchone()
        return _row_to_chunk(row) if row else None

    def search(
        self,
        *,
        scope: KnowledgeScope | None = None,
        type: KnowledgeType | None = None,
        project: str | None = None,
        visibility: KnowledgeVisibility | None = None,
        limit: int = 20,
    ) -> list[KnowledgeChunk]:
        """Search by filters (metadata only)."""
        conditions: list[str] = []
        params: list = []

        if scope:
            conditions.append("scope = ?")
            params.append(scope)
        if type:
            conditions.append("type = ?")
            params.append(type)
        if project:
            conditions.append("project = ?")
            params.append(project)
        if visibility:
            conditions.append("(visibility = ? OR visibility IS NULL)")
            params.append(visibility)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        params.append(limit)

        cur = self._conn.execute(
            f"SELECT * FROM knowledge {where} ORDER BY updated_at DESC LIMIT ?",
            params,
        )
        return [_row_to_chunk(row) for row in cur.fetchall()]

    def touch(self, id: str) -> None:
        """Increment access count and update last_accessed_at."""
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            "UPDATE knowledge SET access_count = access_count + 1, updated_at = ?, last_accessed_at = ? WHERE id = ?",
            (now, now, id),
        )
        self._conn.commit()

    def update_scope(self, id: str, new_scope: KnowledgeScope) -> None:
        """Update scope (promote/demote)."""
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            "UPDATE knowledge SET scope = ?, updated_at = ? WHERE id = ?",
            (new_scope, now, id),
        )
        self._conn.commit()

    def move(self, chunk: KnowledgeChunk, target: MetadataStore) -> None:
        """Move a chunk to target store, preserving id, created_at, and access_count."""
        target._conn.execute(
            """INSERT OR REPLACE INTO knowledge
               (id, content, type, scope, visibility, project, tags, session_id, "trigger",
                source_timestamp, confidence, access_count, created_at, updated_at,
                last_accessed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                chunk.id,
                chunk.content,
                chunk.type,
                chunk.scope,
                chunk.visibility,
                chunk.project,
                json.dumps(chunk.tags),
                chunk.source.session_id,
                chunk.source.trigger,
                chunk.source.timestamp,
                chunk.confidence,
                chunk.access_count,
                chunk.created_at,
                chunk.updated_at,
                chunk.last_accessed_at,
            ),
        )
        target._conn.commit()
        self.delete(chunk.id)

    def delete(self, id: str) -> bool:
        """Delete a knowledge entry."""
        cur = self._conn.execute("DELETE FROM knowledge WHERE id = ?", (id,))
        self._conn.commit()
        return cur.rowcount > 0

    def stats(self) -> dict:
        """Get aggregate statistics."""
        total = self._conn.execute("SELECT COUNT(*) as cnt FROM knowledge").fetchone()["cnt"]

        by_type: dict[str, int] = {}
        for row in self._conn.execute(
            "SELECT type, COUNT(*) as cnt FROM knowledge GROUP BY type"
        ):
            by_type[row["type"]] = row["cnt"]

        by_scope: dict[str, int] = {}
        for row in self._conn.execute(
            "SELECT scope, COUNT(*) as cnt FROM knowledge GROUP BY scope"
        ):
            by_scope[row["scope"]] = row["cnt"]

        return {"total": total, "byType": by_type, "byScope": by_scope}

    def get_all(self) -> list[KnowledgeChunk]:
        """Get all knowledge chunks."""
        cur = self._conn.execute("SELECT * FROM knowledge ORDER BY created_at ASC")
        return [_row_to_chunk(row) for row in cur.fetchall()]

    def count_since(self, timestamp: str) -> int:
        """Count chunks created after a given timestamp."""
        row = self._conn.execute(
            "SELECT COUNT(*) as cnt FROM knowledge WHERE created_at > ?",
            (timestamp,),
        ).fetchone()
        return row["cnt"]

    def get_meta(self, key: str) -> str | None:
        """Get a distill_meta value."""
        row = self._conn.execute(
            "SELECT value FROM distill_meta WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else None

    def set_meta(self, key: str, value: str) -> None:
        """Set a distill_meta value."""
        self._conn.execute(
            "INSERT INTO distill_meta (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        self._conn.commit()

    # ── Lifecycle events ──────────────────────────────────────────────────────

    def add_lifecycle_event(
        self,
        chunk_id: str,
        event_type: LifecycleEventType,
        *,
        from_scope: KnowledgeScope | None = None,
        to_scope: KnowledgeScope | None = None,
        note: str | None = None,
    ) -> LifecycleEvent:
        """Record a lifecycle state transition for a chunk."""
        now = datetime.now(timezone.utc).isoformat()
        event_id = str(uuid.uuid4())
        self._conn.execute(
            """INSERT INTO lifecycle_events
               (id, chunk_id, event_type, from_scope, to_scope, timestamp, note)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (event_id, chunk_id, event_type, from_scope, to_scope, now, note),
        )
        self._conn.commit()
        return LifecycleEvent(
            chunk_id=chunk_id,
            event_type=event_type,
            from_scope=from_scope,
            to_scope=to_scope,
            timestamp=now,
            note=note,
        )

    def get_lifecycle(self, chunk_id: str) -> list[LifecycleEvent]:
        """Get all lifecycle events for a chunk, ordered by timestamp."""
        cur = self._conn.execute(
            "SELECT * FROM lifecycle_events WHERE chunk_id = ? ORDER BY timestamp ASC",
            (chunk_id,),
        )
        return [
            LifecycleEvent(
                chunk_id=row["chunk_id"],
                event_type=row["event_type"],
                from_scope=row["from_scope"],
                to_scope=row["to_scope"],
                timestamp=row["timestamp"],
                note=row["note"],
            )
            for row in cur.fetchall()
        ]

    # ── Chunk relations ───────────────────────────────────────────────────────

    def add_relation(
        self,
        from_id: str,
        to_id: str,
        relation_type: RelationType,
        confidence: float = 0.8,
    ) -> ChunkRelation:
        """Add a directional relationship between two chunks."""
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            """INSERT OR REPLACE INTO chunk_relations
               (from_id, to_id, relation_type, confidence, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (from_id, to_id, relation_type, confidence, now),
        )
        self._conn.commit()
        return ChunkRelation(
            from_id=from_id,
            to_id=to_id,
            relation_type=relation_type,
            confidence=confidence,
            created_at=now,
        )

    def get_relations(
        self,
        chunk_id: str,
        *,
        direction: str = "both",
    ) -> list[ChunkRelation]:
        """Get relations involving a chunk. direction: 'from', 'to', or 'both'."""
        if direction == "from":
            sql = "SELECT * FROM chunk_relations WHERE from_id = ?"
            params = [chunk_id]
        elif direction == "to":
            sql = "SELECT * FROM chunk_relations WHERE to_id = ?"
            params = [chunk_id]
        else:
            sql = "SELECT * FROM chunk_relations WHERE from_id = ? OR to_id = ?"
            params = [chunk_id, chunk_id]

        cur = self._conn.execute(sql, params)
        return [
            ChunkRelation(
                from_id=row["from_id"],
                to_id=row["to_id"],
                relation_type=row["relation_type"],
                confidence=row["confidence"],
                created_at=row["created_at"],
            )
            for row in cur.fetchall()
        ]

    # ── Context manager ───────────────────────────────────────────────────────

    def close(self) -> None:
        """데이터베이스 연결 종료."""
        if self._conn_impl is not None:
            self._conn_impl.close()
            self._conn_impl = None

    def __enter__(self) -> MetadataStore:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        """Context manager exit — ensures close() is always called."""
        self.close()
