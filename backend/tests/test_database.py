from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

import sialabs_local_rag.database as database_module
from sialabs_local_rag.database import Database, DatabaseError, Migration


def test_fresh_database_records_current_schema_version(tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'fresh.db'}")

    database.init_schema()

    assert database.schema_version() == database_module.latest_schema_version()
    with database.connect() as connection:
        tables = {
            str(row["name"])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
    assert {"schema_version", "documents", "chunks", "chat_messages"} <= tables


def test_init_schema_is_idempotent(tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'idempotent.db'}")

    database.init_schema()
    first_version = database.schema_version()
    database.init_schema()

    assert database.schema_version() == first_version


def test_pre_vnext_database_is_adopted_without_losing_data(tmp_path: Path) -> None:
    database_path = tmp_path / "legacy.db"
    _create_pre_vnext_database(database_path)
    database = Database(f"sqlite:///{database_path}")

    database.init_schema()

    assert database.schema_version() == 1
    with database.connect() as connection:
        row = connection.execute(
            "SELECT title FROM documents WHERE id = 'legacy-document'"
        ).fetchone()
    assert row is not None
    assert row["title"] == "Legacy document"


def test_partial_legacy_schema_is_rejected_transactionally(tmp_path: Path) -> None:
    database_path = tmp_path / "partial.db"
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE documents (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                source_type TEXT NOT NULL,
                content_hash TEXT NOT NULL UNIQUE,
                total_chars INTEGER NOT NULL,
                total_chunks INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

    database = Database(f"sqlite:///{database_path}")

    with pytest.raises(DatabaseError, match="partial legacy schema"):
        database.init_schema()

    assert database.schema_version() == 0
    with sqlite3.connect(database_path) as connection:
        schema_version_exists = connection.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type = 'table' AND name = 'schema_version'
            """
        ).fetchone()
    assert schema_version_exists is None


def test_failed_migration_rolls_back_schema_and_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database = Database(f"sqlite:///{tmp_path / 'rollback.db'}")
    database.init_schema()

    def failing_migration(connection: sqlite3.Connection) -> None:
        connection.execute("CREATE TABLE should_be_rolled_back (id INTEGER PRIMARY KEY)")
        raise RuntimeError("intentional migration failure")

    migrations = (
        *database_module.MIGRATIONS,
        Migration(version=2, name="intentional-failure", apply=failing_migration),
    )
    monkeypatch.setattr(database_module, "MIGRATIONS", migrations)

    with pytest.raises(DatabaseError, match="intentional migration failure"):
        database.init_schema()

    assert database.schema_version() == 1
    with database.connect() as connection:
        rolled_back_table = connection.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type = 'table' AND name = 'should_be_rolled_back'
            """
        ).fetchone()
    assert rolled_back_table is None


def test_newer_database_schema_is_rejected(tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'newer.db'}")
    database.init_schema()
    with database.connect() as connection:
        connection.execute("UPDATE schema_version SET version = 999 WHERE singleton = 1")

    with pytest.raises(DatabaseError, match="newer than this application version"):
        database.init_schema()


def _create_pre_vnext_database(database_path: Path) -> None:
    with sqlite3.connect(database_path) as connection:
        connection.executescript(
            """
            PRAGMA foreign_keys = ON;

            CREATE TABLE documents (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                source_type TEXT NOT NULL,
                content_hash TEXT NOT NULL UNIQUE,
                total_chars INTEGER NOT NULL,
                total_chunks INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE chunks (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                token_estimate INTEGER NOT NULL,
                embedding_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(document_id, chunk_index)
            );

            CREATE INDEX idx_chunks_document_id ON chunks(document_id);
            CREATE INDEX idx_chunks_chunk_index ON chunks(chunk_index);

            CREATE TABLE chat_messages (
                id TEXT PRIMARY KEY,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                latency_ms INTEGER NOT NULL,
                metadata_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        connection.execute(
            """
            INSERT INTO documents (
                id, title, source_type, content_hash, total_chars,
                total_chunks, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "legacy-document",
                "Legacy document",
                "manual",
                "legacy-content-hash",
                14,
                0,
                "2026-01-01T00:00:00+00:00",
                "2026-01-01T00:00:00+00:00",
            ),
        )
