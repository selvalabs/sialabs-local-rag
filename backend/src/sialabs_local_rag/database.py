from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


class DatabaseError(RuntimeError):
    """Raised when database configuration or schema migration is invalid."""


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    apply: Callable[[sqlite3.Connection], None]


def sqlite_path_from_url(database_url: str) -> Path:
    """Convert a sqlite:/// URL into a filesystem path."""

    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        raise DatabaseError("Only sqlite:/// database URLs are supported in this MVP.")

    raw_path = database_url.removeprefix(prefix)
    path = Path(raw_path)
    if not path.is_absolute():
        path = Path.cwd() / path
    return path


def _create_core_schema(connection: sqlite3.Connection) -> None:
    statements = (
        """
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            source_type TEXT NOT NULL,
            content_hash TEXT NOT NULL UNIQUE,
            total_chars INTEGER NOT NULL,
            total_chunks INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS chunks (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            token_estimate INTEGER NOT NULL,
            embedding_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(document_id, chunk_index)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id)",
        "CREATE INDEX IF NOT EXISTS idx_chunks_chunk_index ON chunks(chunk_index)",
        """
        CREATE TABLE IF NOT EXISTS chat_messages (
            id TEXT PRIMARY KEY,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            provider TEXT NOT NULL,
            model TEXT NOT NULL,
            latency_ms INTEGER NOT NULL,
            metadata_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """,
    )
    for statement in statements:
        connection.execute(statement)


def _create_embedding_index_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS embedding_index (
            singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
            provider TEXT NOT NULL,
            model TEXT NOT NULL,
            dimension INTEGER NOT NULL CHECK (dimension > 0),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )


def _sanitize_chat_source_metadata(connection: sqlite3.Connection) -> None:
    """Remove persisted source text from chat metadata while keeping trace identifiers."""

    allowed_source_keys = {
        "chunk_id",
        "document_id",
        "document_title",
        "chunk_index",
        "score",
    }
    rows = connection.execute("SELECT id, metadata_json FROM chat_messages").fetchall()

    for row in rows:
        raw_metadata = str(row["metadata_json"])
        try:
            parsed = json.loads(raw_metadata)
        except json.JSONDecodeError:
            parsed = {}

        metadata = parsed if isinstance(parsed, dict) else {}
        raw_sources = metadata.get("sources")
        sanitized_sources: list[dict[str, object]] = []

        if isinstance(raw_sources, list):
            for raw_source in raw_sources:
                if not isinstance(raw_source, dict):
                    continue
                sanitized_sources.append(
                    {
                        str(key): value
                        for key, value in raw_source.items()
                        if key in allowed_source_keys
                    }
                )

        metadata["sources"] = sanitized_sources
        connection.execute(
            "UPDATE chat_messages SET metadata_json = ? WHERE id = ?",
            (json.dumps(metadata, ensure_ascii=False), str(row["id"])),
        )


MIGRATIONS: tuple[Migration, ...] = (
    Migration(version=1, name="baseline-local-rag-schema", apply=_create_core_schema),
    Migration(version=2, name="embedding-index-metadata", apply=_create_embedding_index_schema),
    Migration(version=3, name="sanitize-chat-source-metadata", apply=_sanitize_chat_source_metadata),
)

_CORE_TABLES = {"documents", "chunks", "chat_messages"}


def latest_schema_version() -> int:
    return MIGRATIONS[-1].version if MIGRATIONS else 0


class Database:
    """Small SQLite connection factory with versioned schema migrations."""

    def __init__(self, database_url: str) -> None:
        self.path = sqlite_path_from_url(database_url)

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def init_schema(self) -> None:
        connection = self.connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            self._ensure_schema_version_table(connection)
            current_version = self._read_schema_version(connection)
            supported_version = latest_schema_version()

            if current_version > supported_version:
                raise DatabaseError(
                    "Database schema is newer than this application version "
                    f"({current_version} > {supported_version})."
                )

            if current_version == 0 and self._has_legacy_core_schema(connection):
                _create_core_schema(connection)
                self._write_schema_version(connection, 1)
                current_version = 1

            for migration in MIGRATIONS:
                if migration.version <= current_version:
                    continue
                migration.apply(connection)
                self._write_schema_version(connection, migration.version)
                current_version = migration.version

            connection.commit()
        except Exception as exc:
            connection.rollback()
            if isinstance(exc, DatabaseError):
                raise
            raise DatabaseError(f"Database schema migration failed: {exc}") from exc
        finally:
            connection.close()

    def schema_version(self) -> int:
        with self.connect() as connection:
            if not self._table_exists(connection, "schema_version"):
                return 0
            return self._read_schema_version(connection)

    @staticmethod
    def _ensure_schema_version_table(connection: sqlite3.Connection) -> None:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_version (
                singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                version INTEGER NOT NULL
            )
            """
        )

    @staticmethod
    def _read_schema_version(connection: sqlite3.Connection) -> int:
        row = connection.execute(
            "SELECT version FROM schema_version WHERE singleton = 1"
        ).fetchone()
        return int(row["version"]) if row is not None else 0

    @staticmethod
    def _write_schema_version(connection: sqlite3.Connection, version: int) -> None:
        connection.execute(
            """
            INSERT INTO schema_version (singleton, version)
            VALUES (1, ?)
            ON CONFLICT(singleton) DO UPDATE SET version = excluded.version
            """,
            (version,),
        )

    def _has_legacy_core_schema(self, connection: sqlite3.Connection) -> bool:
        existing_tables = {
            str(row["name"])
            for row in connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table' AND name IN ('documents', 'chunks', 'chat_messages')
                """
            ).fetchall()
        }
        if not existing_tables:
            return False
        if existing_tables != _CORE_TABLES:
            missing = ", ".join(sorted(_CORE_TABLES - existing_tables))
            raise DatabaseError(
                "Existing SQLite database has a partial legacy schema. "
                f"Missing required tables: {missing}. Restore a backup or use a fresh database."
            )
        return True

    @staticmethod
    def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
        row = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table_name,),
        ).fetchone()
        return row is not None
