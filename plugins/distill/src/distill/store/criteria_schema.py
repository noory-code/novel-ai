"""Database schema owned by the criteria store."""

from __future__ import annotations

import sqlite3


def install_schema(connection: sqlite3.Connection) -> None:
    """Install the five criteria tables without touching knowledge tables."""
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS criteria (
            id TEXT PRIMARY KEY,
            project TEXT NOT NULL,
            current_version INTEGER NOT NULL,
            revoked INTEGER NOT NULL DEFAULT 0,
            identity_digest TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS criteria_project_idx ON criteria(project);
        CREATE TABLE IF NOT EXISTS criterion_versions (
            criterion_id TEXT NOT NULL,
            version INTEGER NOT NULL,
            statement TEXT NOT NULL,
            applies_when TEXT NOT NULL,
            exceptions TEXT NOT NULL,
            notes TEXT NOT NULL,
            overrides TEXT NOT NULL,
            confirmation TEXT NOT NULL,
            ai_confidence REAL,
            origin TEXT NOT NULL,
            reason TEXT,
            supersedes TEXT,
            recorded_at TEXT NOT NULL,
            status TEXT NOT NULL,
            PRIMARY KEY (criterion_id, version)
        );
        CREATE TABLE IF NOT EXISTS criterion_events (
            sequence INTEGER PRIMARY KEY AUTOINCREMENT,
            criterion_id TEXT NOT NULL,
            event TEXT NOT NULL,
            version INTEGER NOT NULL,
            generation INTEGER NOT NULL,
            reason TEXT,
            origin TEXT NOT NULL,
            recorded_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS criteria_requests (
            idempotency_key TEXT PRIMARY KEY,
            payload_digest TEXT NOT NULL,
            response TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS criteria_meta (
            key TEXT PRIMARY KEY,
            value INTEGER NOT NULL
        );
        INSERT OR IGNORE INTO criteria_meta(key, value) VALUES ('generation', 0);
        """
    )
    connection.commit()
