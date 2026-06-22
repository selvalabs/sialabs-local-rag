from __future__ import annotations

import json
import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from uuid import uuid4

from sialabs_local_rag.chunking import estimate_tokens
from sialabs_local_rag.database import Database
from sialabs_local_rag.schemas import DocumentResponse, SourceChunk
from sialabs_local_rag.vector_math import cosine_similarity


@dataclass(frozen=True)
class ChunkInput:
    index: int
    content: str
    embedding: list[float]


@dataclass(frozen=True)
class SearchResult:
    source: SourceChunk
    embedding: list[float]


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def content_digest(content: str) -> str:
    return sha256(content.encode("utf-8")).hexdigest()


class DuplicateDocumentError(RuntimeError):
    """Raised when a document with the same content already exists."""


class Storage:
    """SQLite persistence layer for documents, chunks and chat traces."""

    def __init__(self, database: Database) -> None:
        self.database = database

    def create_document(
        self,
        title: str,
        source_type: str,
        original_content: str,
        chunks: Sequence[ChunkInput],
    ) -> DocumentResponse:
        document_id = str(uuid4())
        now = utc_now_iso()
        digest = content_digest(original_content)

        try:
            with self.database.connect() as connection:
                connection.execute(
                    """
                    INSERT INTO documents (
                        id, title, source_type, content_hash, total_chars,
                        total_chunks, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        document_id,
                        title,
                        source_type,
                        digest,
                        len(original_content),
                        len(chunks),
                        now,
                        now,
                    ),
                )
                connection.executemany(
                    """
                    INSERT INTO chunks (
                        id, document_id, chunk_index, content,
                        token_estimate, embedding_json, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            str(uuid4()),
                            document_id,
                            chunk.index,
                            chunk.content,
                            estimate_tokens(chunk.content),
                            json.dumps(chunk.embedding, separators=(",", ":")),
                            now,
                        )
                        for chunk in chunks
                    ],
                )
        except sqlite3.IntegrityError as exc:
            raise DuplicateDocumentError(
                "A document with the same content already exists."
            ) from exc

        return DocumentResponse(
            id=document_id,
            title=title,
            source_type=source_type,
            total_chars=len(original_content),
            total_chunks=len(chunks),
            created_at=now,
            updated_at=now,
        )

    def list_documents(self) -> list[DocumentResponse]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, title, source_type, total_chars, total_chunks, created_at, updated_at
                FROM documents
                ORDER BY created_at DESC
                """
            ).fetchall()

        return [self._document_from_row(row) for row in rows]

    def delete_document(self, document_id: str) -> bool:
        with self.database.connect() as connection:
            cursor = connection.execute("DELETE FROM documents WHERE id = ?", (document_id,))
            return cursor.rowcount > 0

    def search_chunks(self, query_embedding: Sequence[float], top_k: int) -> list[SourceChunk]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    chunks.id AS chunk_id,
                    chunks.document_id AS document_id,
                    documents.title AS document_title,
                    chunks.chunk_index AS chunk_index,
                    chunks.content AS content,
                    chunks.embedding_json AS embedding_json
                FROM chunks
                JOIN documents ON documents.id = chunks.document_id
                """
            ).fetchall()

        scored: list[SourceChunk] = []
        for row in rows:
            embedding = self._embedding_from_json(str(row["embedding_json"]))
            score = cosine_similarity(query_embedding, embedding)
            scored.append(
                SourceChunk(
                    chunk_id=str(row["chunk_id"]),
                    document_id=str(row["document_id"]),
                    document_title=str(row["document_title"]),
                    chunk_index=int(row["chunk_index"]),
                    score=round(score, 6),
                    content=str(row["content"]),
                )
            )

        ranked = sorted(scored, key=lambda item: item.score, reverse=True)
        return self._diversify_sources_by_document(ranked, top_k)

    def create_chat_record(
        self,
        question: str,
        answer: str,
        provider: str,
        model: str,
        latency_ms: int,
        sources: Sequence[SourceChunk],
    ) -> None:
        metadata = {
            "sources": [source.model_dump() for source in sources],
        }
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO chat_messages (
                    id, question, answer, provider, model,
                    latency_ms, metadata_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid4()),
                    question,
                    answer,
                    provider,
                    model,
                    latency_ms,
                    json.dumps(metadata, ensure_ascii=False),
                    utc_now_iso(),
                ),
            )

    @staticmethod
    def _diversify_sources_by_document(
        ranked_sources: Sequence[SourceChunk],
        top_k: int,
    ) -> list[SourceChunk]:
        selected: list[SourceChunk] = []
        selected_chunk_ids: set[str] = set()
        selected_document_ids: set[str] = set()

        for source in ranked_sources:
            if source.document_id in selected_document_ids:
                continue
            selected.append(source)
            selected_chunk_ids.add(source.chunk_id)
            selected_document_ids.add(source.document_id)
            if len(selected) >= top_k:
                return selected

        for source in ranked_sources:
            if source.chunk_id in selected_chunk_ids:
                continue
            selected.append(source)
            if len(selected) >= top_k:
                return selected

        return selected

    @staticmethod
    def _document_from_row(row: sqlite3.Row) -> DocumentResponse:
        return DocumentResponse(
            id=str(row["id"]),
            title=str(row["title"]),
            source_type=str(row["source_type"]),
            total_chars=int(row["total_chars"]),
            total_chunks=int(row["total_chunks"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )

    @staticmethod
    def _embedding_from_json(raw_value: str) -> list[float]:
        parsed = json.loads(raw_value)
        if not isinstance(parsed, list):
            return []
        return [float(value) for value in parsed]
