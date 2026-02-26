"""Vector store for semantic knowledge search.

Dual-index: FTS5 for keyword search + sqlite-vec for semantic search.
Embedding model loaded lazily on first call.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass

import numpy as np
import sqlite_vec

from distill.store.scope import resolve_db_path
from distill.store.types import KnowledgeScope

EMBEDDING_DIM = 384
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

FTS_SCHEMA = """
CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
  id UNINDEXED,
  content,
  tags
);
"""

VEC_SCHEMA = f"""
CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_vec USING vec0(
  knowledge_id text primary key,
  embedding float[{EMBEDDING_DIM}] distance_metric=cosine
);
"""

# Shared embedder (lazy singleton)
_embedder = None


def _get_embedder():
    global _embedder
    if _embedder is None:
        from fastembed import TextEmbedding

        _embedder = TextEmbedding(model_name=EMBEDDING_MODEL)
    return _embedder


def _reset_embedder() -> None:
    """Reset the shared embedder (for testing)."""
    global _embedder
    _embedder = None


def _embed(text: str) -> bytes:
    """Embed text and return as bytes for sqlite-vec."""
    embedder = _get_embedder()
    embeddings = list(embedder.embed([text]))
    vec = np.array(embeddings[0], dtype=np.float32)
    return vec.tobytes()


@dataclass
class SearchResult:
    id: str
    content: str
    tags: list[str]
    score: float


class VectorStore:
    def __init__(
        self,
        scope: KnowledgeScope,
        project_root: str | None = None,
        workspace_root: str | None = None,
    ) -> None:
        db_path = resolve_db_path(scope, project_root, workspace_root)
        self._conn: sqlite3.Connection | None = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode = WAL")
        self._conn.execute("PRAGMA busy_timeout = 5000")

        # Load sqlite-vec extension
        self._conn.enable_load_extension(True)
        sqlite_vec.load(self._conn)
        self._conn.enable_load_extension(False)

        # Create both tables
        self._conn.executescript(FTS_SCHEMA)
        self._conn.executescript(VEC_SCHEMA)

    def index(self, id: str, content: str, tags: list[str]) -> None:
        """Index a knowledge chunk in both FTS5 and vector index."""
        # FTS5 index
        self._conn.execute(
            "INSERT OR REPLACE INTO knowledge_fts (id, content, tags) VALUES (?, ?, ?)",
            (id, content, " ".join(tags)),
        )

        # Vector index
        embedding = _embed(content)
        self._conn.execute(
            "INSERT OR REPLACE INTO knowledge_vec (knowledge_id, embedding) VALUES (?, ?)",
            (id, embedding),
        )
        self._conn.commit()

    def search(self, query: str, limit: int = 5) -> list[SearchResult]:
        """Semantic search using vector similarity (KNN)."""
        query_embedding = _embed(query)

        vec_rows = self._conn.execute(
            """SELECT knowledge_id, distance
               FROM knowledge_vec
               WHERE embedding MATCH ?
               AND k = ?""",
            (query_embedding, limit),
        ).fetchall()

        if not vec_rows:
            return []

        # Build distance map
        distance_map = {row["knowledge_id"]: row["distance"] for row in vec_rows}
        ids = list(distance_map.keys())
        placeholders = ",".join("?" for _ in ids)

        fts_rows = self._conn.execute(
            f"SELECT id, content, tags FROM knowledge_fts WHERE id IN ({placeholders})",
            ids,
        ).fetchall()

        results = [
            SearchResult(
                id=row["id"],
                content=row["content"],
                tags=[t for t in row["tags"].split(" ") if t],
                score=1 - distance_map.get(row["id"], 1),
            )
            for row in fts_rows
        ]
        results.sort(key=lambda r: r.score, reverse=True)
        return results

    def fts_search(self, query: str, limit: int = 5) -> list[SearchResult]:
        """Keyword search using FTS5 only (no embedding needed)."""
        sanitized = sanitize_fts_query(query)
        if not sanitized:
            return []

        rows = self._conn.execute(
            """SELECT id, content, tags, rank
               FROM knowledge_fts
               WHERE knowledge_fts MATCH ?
               ORDER BY rank
               LIMIT ?""",
            (sanitized, limit),
        ).fetchall()

        return [
            SearchResult(
                id=row["id"],
                content=row["content"],
                tags=[t for t in row["tags"].split(" ") if t],
                score=-row["rank"],
            )
            for row in rows
        ]

    def remove(self, id: str) -> None:
        """Remove an entry from both indexes."""
        self._conn.execute("DELETE FROM knowledge_fts WHERE id = ?", (id,))
        self._conn.execute("DELETE FROM knowledge_vec WHERE knowledge_id = ?", (id,))
        self._conn.commit()

    def close(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            finally:
                self._conn = None

    def __enter__(self) -> VectorStore:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        """Context manager exit — ensures close() is always called."""
        self.close()


def sanitize_fts_query(query: str) -> str:
    """Sanitize query for FTS5 MATCH syntax.

    Splits into tokens and joins with OR for broad matching.
    """
    tokens = re.sub(r"[^\w\s]", " ", query, flags=re.UNICODE).split()
    tokens = [t for t in tokens if t]

    if not tokens:
        return ""

    return " OR ".join(f'"{t}"' for t in tokens)
