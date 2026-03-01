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

        # fastembed>=0.7 required. The model_name= kwarg API changed in 0.7.
        _embedder = TextEmbedding(model_name=EMBEDDING_MODEL)
    return _embedder


def _reset_embedder() -> None:
    """Reset the shared embedder (for testing)."""
    global _embedder
    _embedder = None


def _embed(text: str) -> bytes:
    """Embed a single text and return it as bytes for sqlite-vec."""
    embedder = _get_embedder()
    embeddings = list(embedder.embed([text]))
    vec = np.array(embeddings[0], dtype=np.float32)
    return vec.tobytes()


def _embed_many(texts: list[str]) -> list[bytes]:
    """Embed multiple texts in a batch and return them as a list of bytes for sqlite-vec."""
    embedder = _get_embedder()
    embeddings = list(embedder.embed(texts))
    return [np.array(emb, dtype=np.float32).tobytes() for emb in embeddings]


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
        self._conn_impl: sqlite3.Connection | None = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn_impl.row_factory = sqlite3.Row

        # Check if WAL mode is already set before enabling it
        row = self._conn_impl.execute("PRAGMA journal_mode").fetchone()
        if row and row[0].lower() != "wal":
            self._conn_impl.execute("PRAGMA journal_mode = WAL")

        self._conn_impl.execute("PRAGMA busy_timeout = 5000")

        # Load the sqlite-vec extension
        self._conn_impl.enable_load_extension(True)
        sqlite_vec.load(self._conn_impl)
        self._conn_impl.enable_load_extension(False)

        # Create tables
        self._conn_impl.executescript(FTS_SCHEMA)
        self._conn_impl.executescript(VEC_SCHEMA)

    @property
    def _conn(self) -> sqlite3.Connection:
        """Access the internal connection object (with None check)."""
        if self._conn_impl is None:
            raise RuntimeError("Database connection is closed")
        return self._conn_impl

    def index(self, id: str, content: str, tags: list[str]) -> None:
        """Index a knowledge chunk into both the FTS5 and vector indexes."""
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

    def index_many(self, ids: list[str], contents: list[str], tags_list: list[list[str]]) -> None:
        """Batch-index multiple knowledge chunks into both the FTS5 and vector indexes."""
        if not ids or len(ids) != len(contents) or len(ids) != len(tags_list):
            raise ValueError("ids, contents, and tags_list must have the same length")

        # Batch embedding
        embeddings = _embed_many(contents)

        # Insert all rows in a single transaction
        with self._conn:
            for id, content, tags, embedding in zip(ids, contents, tags_list, embeddings):
                # FTS5 index
                self._conn.execute(
                    "INSERT OR REPLACE INTO knowledge_fts (id, content, tags) VALUES (?, ?, ?)",
                    (id, content, " ".join(tags)),
                )
                # Vector index
                self._conn.execute(
                    "INSERT OR REPLACE INTO knowledge_vec (knowledge_id, embedding) VALUES (?, ?)",
                    (id, embedding),
                )

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

        # TODO: Python-level join is a known limitation because sqlite-vec and FTS5 are
        # separate virtual tables that are difficult to optimize with a SQL JOIN. Consider
        # improving this in the future.
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
        if self._conn_impl is not None:
            try:
                self._conn_impl.close()
            finally:
                self._conn_impl = None

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
