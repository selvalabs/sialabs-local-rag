from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from sialabs_local_rag.database import Database
from sialabs_local_rag.schemas import DocumentResponse
from sialabs_local_rag.storage import content_digest, utc_now_iso

DEFAULT_COLLECTION_ID = "default"


class CollectionNotFoundError(LookupError):
    """Raised when a requested collection does not exist."""


class CollectionPathError(ValueError):
    """Raised when a local folder registration is invalid."""


@dataclass(frozen=True)
class CollectionRecord:
    id: str
    name: str
    kind: str
    root_path: str | None
    missing_policy: str
    created_at: str
    updated_at: str
    last_scanned_at: str | None


@dataclass(frozen=True)
class CollectionSourceRecord:
    id: str
    collection_id: str
    document_id: str | None
    relative_path: str | None
    content_hash: str
    file_size: int | None
    modified_ns: int | None
    status: str
    last_seen_at: str | None
    last_error: str | None


class CollectionStore:
    def __init__(self, database: Database) -> None:
        self.database = database

    def register_folder(
        self,
        name: str,
        root_path: Path,
        missing_policy: str = "mark",
    ) -> CollectionRecord:
        resolved = root_path.expanduser().resolve()
        if not resolved.exists() or not resolved.is_dir():
            raise CollectionPathError(f"Collection folder does not exist: {resolved}")
        if missing_policy not in {"mark", "remove"}:
            raise CollectionPathError("missing_policy must be 'mark' or 'remove'.")

        now = utc_now_iso()
        collection_id = str(uuid4())
        try:
            with self.database.connect() as connection:
                connection.execute(
                    """
                    INSERT INTO collections (
                        id, name, kind, root_path, missing_policy, created_at, updated_at
                    )
                    VALUES (?, ?, 'folder', ?, ?, ?, ?)
                    """,
                    (
                        collection_id,
                        name.strip() or resolved.name,
                        str(resolved),
                        missing_policy,
                        now,
                        now,
                    ),
                )
        except Exception as exc:
            if "UNIQUE constraint failed: collections.root_path" in str(exc):
                raise CollectionPathError(
                    f"Folder is already registered as a collection: {resolved}"
                ) from exc
            raise
        return self.get_collection(collection_id)

    def get_collection(self, collection_id: str) -> CollectionRecord:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT
                    id, name, kind, root_path, missing_policy,
                    created_at, updated_at, last_scanned_at
                FROM collections
                WHERE id = ?
                """,
                (collection_id,),
            ).fetchone()
        if row is None:
            raise CollectionNotFoundError(f"Collection not found: {collection_id}")
        return CollectionRecord(
            id=str(row["id"]),
            name=str(row["name"]),
            kind=str(row["kind"]),
            root_path=str(row["root_path"]) if row["root_path"] is not None else None,
            missing_policy=str(row["missing_policy"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
            last_scanned_at=(
                str(row["last_scanned_at"]) if row["last_scanned_at"] is not None else None
            ),
        )

    def list_collections(self) -> list[CollectionRecord]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    id, name, kind, root_path, missing_policy,
                    created_at, updated_at, last_scanned_at
                FROM collections
                ORDER BY CASE WHEN id = 'default' THEN 0 ELSE 1 END, name COLLATE NOCASE
                """
            ).fetchall()
        return [
            CollectionRecord(
                id=str(row["id"]),
                name=str(row["name"]),
                kind=str(row["kind"]),
                root_path=(
                    str(row["root_path"]) if row["root_path"] is not None else None
                ),
                missing_policy=str(row["missing_policy"]),
                created_at=str(row["created_at"]),
                updated_at=str(row["updated_at"]),
                last_scanned_at=(
                    str(row["last_scanned_at"])
                    if row["last_scanned_at"] is not None
                    else None
                ),
            )
            for row in rows
        ]

    def list_sources(self, collection_id: str) -> dict[str, CollectionSourceRecord]:
        self.get_collection(collection_id)
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    id, collection_id, document_id, relative_path,
                    content_hash, file_size, modified_ns, status,
                    last_seen_at, last_error
                FROM collection_sources
                WHERE collection_id = ? AND relative_path IS NOT NULL
                """,
                (collection_id,),
            ).fetchall()
        return {
            str(row["relative_path"]): self._source_from_row(row)
            for row in rows
        }

    def attach_default_document(self, document: DocumentResponse) -> None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT content_hash FROM documents WHERE id = ?",
                (document.id,),
            ).fetchone()
            if row is None:
                return
            now = utc_now_iso()
            connection.execute(
                """
                INSERT OR IGNORE INTO collection_sources (
                    id, collection_id, document_id, relative_path, content_hash,
                    status, last_seen_at, created_at, updated_at
                )
                VALUES (?, 'default', ?, NULL, ?, 'active', ?, ?, ?)
                """,
                (
                    f"default:{document.id}",
                    document.id,
                    str(row["content_hash"]),
                    now,
                    now,
                    now,
                ),
            )

    def find_document_by_content(self, content: str) -> DocumentResponse | None:
        digest = content_digest(content)
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT
                    id, title, source_type, total_chars, total_chunks,
                    created_at, updated_at
                FROM documents
                WHERE content_hash = ?
                """,
                (digest,),
            ).fetchone()
        if row is None:
            return None
        return DocumentResponse(
            id=str(row["id"]),
            title=str(row["title"]),
            source_type=str(row["source_type"]),
            total_chars=int(row["total_chars"]),
            total_chunks=int(row["total_chunks"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )

    def upsert_file_source(
        self,
        collection_id: str,
        relative_path: str,
        document_id: str,
        raw_content_hash: str,
        file_size: int,
        modified_ns: int,
    ) -> str | None:
        self.get_collection(collection_id)
        now = utc_now_iso()
        with self.database.connect() as connection:
            previous = connection.execute(
                """
                SELECT id, document_id
                FROM collection_sources
                WHERE collection_id = ? AND relative_path = ?
                """,
                (collection_id, relative_path),
            ).fetchone()
            previous_document_id = (
                str(previous["document_id"])
                if previous is not None and previous["document_id"] is not None
                else None
            )
            source_id = str(previous["id"]) if previous is not None else str(uuid4())
            connection.execute(
                """
                INSERT INTO collection_sources (
                    id, collection_id, document_id, relative_path, content_hash,
                    file_size, modified_ns, status, last_seen_at, last_error,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, NULL, ?, ?)
                ON CONFLICT(collection_id, relative_path) DO UPDATE SET
                    document_id = excluded.document_id,
                    content_hash = excluded.content_hash,
                    file_size = excluded.file_size,
                    modified_ns = excluded.modified_ns,
                    status = 'active',
                    last_seen_at = excluded.last_seen_at,
                    last_error = NULL,
                    updated_at = excluded.updated_at
                """,
                (
                    source_id,
                    collection_id,
                    document_id,
                    relative_path,
                    raw_content_hash,
                    file_size,
                    modified_ns,
                    now,
                    now,
                    now,
                ),
            )
        return previous_document_id if previous_document_id != document_id else None

    def touch_unchanged_source(
        self,
        source_id: str,
        file_size: int,
        modified_ns: int,
    ) -> None:
        now = utc_now_iso()
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE collection_sources
                SET
                    file_size = ?, modified_ns = ?, status = 'active',
                    last_seen_at = ?, last_error = NULL, updated_at = ?
                WHERE id = ?
                """,
                (file_size, modified_ns, now, now, source_id),
            )

    def record_source_error(
        self,
        collection_id: str,
        relative_path: str,
        raw_content_hash: str,
        file_size: int,
        modified_ns: int,
        error: str,
    ) -> str | None:
        now = utc_now_iso()
        with self.database.connect() as connection:
            previous = connection.execute(
                """
                SELECT id, document_id
                FROM collection_sources
                WHERE collection_id = ? AND relative_path = ?
                """,
                (collection_id, relative_path),
            ).fetchone()
            source_id = str(previous["id"]) if previous is not None else str(uuid4())
            previous_document_id = (
                str(previous["document_id"])
                if previous is not None and previous["document_id"] is not None
                else None
            )
            connection.execute(
                """
                INSERT INTO collection_sources (
                    id, collection_id, document_id, relative_path, content_hash,
                    file_size, modified_ns, status, last_seen_at, last_error,
                    created_at, updated_at
                )
                VALUES (?, ?, NULL, ?, ?, ?, ?, 'error', ?, ?, ?, ?)
                ON CONFLICT(collection_id, relative_path) DO UPDATE SET
                    document_id = NULL,
                    content_hash = excluded.content_hash,
                    file_size = excluded.file_size,
                    modified_ns = excluded.modified_ns,
                    status = 'error',
                    last_seen_at = excluded.last_seen_at,
                    last_error = excluded.last_error,
                    updated_at = excluded.updated_at
                """,
                (
                    source_id,
                    collection_id,
                    relative_path,
                    raw_content_hash,
                    file_size,
                    modified_ns,
                    now,
                    error[:1000],
                    now,
                    now,
                ),
            )
        return previous_document_id

    def handle_missing_source(self, source: CollectionSourceRecord, policy: str) -> str | None:
        if source.relative_path is None:
            return None
        now = utc_now_iso()
        previous_document_id = source.document_id
        with self.database.connect() as connection:
            if policy == "remove":
                connection.execute(
                    "DELETE FROM collection_sources WHERE id = ?",
                    (source.id,),
                )
            else:
                connection.execute(
                    """
                    UPDATE collection_sources
                    SET
                        document_id = NULL, status = 'missing',
                        last_error = NULL, updated_at = ?
                    WHERE id = ?
                    """,
                    (now, source.id),
                )
        return previous_document_id

    def delete_document_if_orphaned(self, document_id: str | None) -> bool:
        if document_id is None:
            return False
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT 1 FROM collection_sources
                WHERE document_id = ? AND status = 'active'
                LIMIT 1
                """,
                (document_id,),
            ).fetchone()
        if row is not None:
            return False

        from sialabs_local_rag.storage import Storage

        return Storage(self.database).delete_document(document_id)

    def mark_collection_scanned(self, collection_id: str) -> None:
        now = utc_now_iso()
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE collections
                SET last_scanned_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (now, now, collection_id),
            )

    def collection_counts(self, collection_id: str) -> tuple[int, int, int]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT status, COUNT(*) AS count
                FROM collection_sources
                WHERE collection_id = ?
                GROUP BY status
                """,
                (collection_id,),
            ).fetchall()
        counts = {str(row["status"]): int(row["count"]) for row in rows}
        return (
            counts.get("active", 0),
            counts.get("missing", 0),
            counts.get("error", 0),
        )

    @staticmethod
    def _source_from_row(row: object) -> CollectionSourceRecord:
        data = row  # sqlite3.Row supports mapping access without importing sqlite3 here.
        return CollectionSourceRecord(
            id=str(data["id"]),  # type: ignore[index]
            collection_id=str(data["collection_id"]),  # type: ignore[index]
            document_id=(
                str(data["document_id"])  # type: ignore[index]
                if data["document_id"] is not None  # type: ignore[index]
                else None
            ),
            relative_path=(
                str(data["relative_path"])  # type: ignore[index]
                if data["relative_path"] is not None  # type: ignore[index]
                else None
            ),
            content_hash=str(data["content_hash"]),  # type: ignore[index]
            file_size=(
                int(data["file_size"])  # type: ignore[index]
                if data["file_size"] is not None  # type: ignore[index]
                else None
            ),
            modified_ns=(
                int(data["modified_ns"])  # type: ignore[index]
                if data["modified_ns"] is not None  # type: ignore[index]
                else None
            ),
            status=str(data["status"]),  # type: ignore[index]
            last_seen_at=(
                str(data["last_seen_at"])  # type: ignore[index]
                if data["last_seen_at"] is not None  # type: ignore[index]
                else None
            ),
            last_error=(
                str(data["last_error"])  # type: ignore[index]
                if data["last_error"] is not None  # type: ignore[index]
                else None
            ),
        )
