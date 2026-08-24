from __future__ import annotations

import json
import re
import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from sialabs_local_rag.schemas import SourceChunk
from sialabs_local_rag.source_metadata import enrich_source_metadata
from sialabs_local_rag.storage import EmbeddingIndexCompatibilityError, Storage
from sialabs_local_rag.vector_math import cosine_similarity

RetrievalMode = Literal["dense", "hybrid"]
RetrievalChannel = Literal["dense", "lexical"]

_TOKEN_PATTERN = re.compile(r"[\w-]+", flags=re.UNICODE)
_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "da",
    "das",
    "de",
    "do",
    "dos",
    "e",
    "em",
    "for",
    "from",
    "how",
    "in",
    "is",
    "o",
    "of",
    "on",
    "or",
    "para",
    "por",
    "que",
    "the",
    "to",
    "um",
    "uma",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
}


@dataclass(frozen=True)
class RetrievalOptions:
    mode: RetrievalMode = "hybrid"
    minimum_dense_score: float = 0.0
    dense_weight: float = 1.0
    lexical_weight: float = 1.2
    rrf_k: int = 60
    candidate_multiplier: int = 4


def retrieve_sources(
    storage: Storage,
    query_text: str,
    query_embedding: Sequence[float],
    top_k: int,
    embedding_provider: str,
    embedding_model: str,
    options: RetrievalOptions,
    collection_id: str | None = None,
) -> list[SourceChunk]:
    candidate_k = max(top_k, top_k * options.candidate_multiplier)
    if collection_id is None:
        dense = storage.search_chunks(
            query_embedding=query_embedding,
            top_k=candidate_k,
            embedding_provider=embedding_provider,
            embedding_model=embedding_model,
            minimum_score=options.minimum_dense_score,
        )
    else:
        dense = _search_dense_collection(
            storage=storage,
            query_embedding=query_embedding,
            limit=candidate_k,
            embedding_provider=embedding_provider,
            embedding_model=embedding_model,
            minimum_score=options.minimum_dense_score,
            collection_id=collection_id,
        )

    if options.mode == "dense":
        selected = _annotate_dense(dense[:top_k])
    else:
        lexical = _search_lexical(
            storage,
            query_text=query_text,
            limit=candidate_k,
            collection_id=collection_id,
        )
        if not lexical:
            selected = _annotate_dense(dense[:top_k])
        else:
            selected = _fuse_rrf(
                dense=dense,
                lexical=lexical,
                top_k=top_k,
                dense_weight=options.dense_weight,
                lexical_weight=options.lexical_weight,
                rrf_k=options.rrf_k,
            )

    return enrich_source_metadata(storage.database, selected)


def _search_dense_collection(
    storage: Storage,
    query_embedding: Sequence[float],
    limit: int,
    embedding_provider: str,
    embedding_model: str,
    minimum_score: float,
    collection_id: str,
) -> list[SourceChunk]:
    storage.assert_embedding_compatible(
        provider=embedding_provider,
        model=embedding_model,
    )
    with storage.database.connect() as connection:
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
            WHERE EXISTS (
                SELECT 1
                FROM collection_sources
                WHERE collection_sources.collection_id = ?
                  AND collection_sources.document_id = chunks.document_id
                  AND collection_sources.status = 'active'
            )
            """,
            (collection_id,),
        ).fetchall()

    scored: list[SourceChunk] = []
    for row in rows:
        raw_embedding = json.loads(str(row["embedding_json"]))
        if not isinstance(raw_embedding, list):
            raise EmbeddingIndexCompatibilityError(
                "Stored collection embedding is invalid; reset and re-ingest the index."
            )
        embedding = [float(value) for value in raw_embedding]
        if len(embedding) != len(query_embedding):
            raise EmbeddingIndexCompatibilityError(
                "Embedding dimension mismatch in collection retrieval. "
                "Reset the index and re-ingest documents."
            )
        raw_score = cosine_similarity(query_embedding, embedding)
        if raw_score < minimum_score:
            continue
        scored.append(
            SourceChunk(
                chunk_id=str(row["chunk_id"]),
                document_id=str(row["document_id"]),
                document_title=str(row["document_title"]),
                chunk_index=int(row["chunk_index"]),
                score=round(raw_score, 6),
                content=str(row["content"]),
                collection_id=collection_id,
            )
        )

    scored.sort(key=lambda item: item.score, reverse=True)
    return scored[:limit]


def _annotate_dense(sources: Sequence[SourceChunk]) -> list[SourceChunk]:
    return [
        source.model_copy(
            update={
                "dense_score": source.score,
                "dense_rank": rank,
                "retrieval_channels": ["dense"],
            }
        )
        for rank, source in enumerate(sources, start=1)
    ]


def lexical_query_from_text(text: str) -> str:
    terms: list[str] = []
    seen: set[str] = set()
    for raw_token in _TOKEN_PATTERN.findall(text.casefold()):
        token = raw_token.strip("_-")
        if not token or token in _STOPWORDS:
            continue
        if len(token) < 3 and not any(char.isdigit() for char in token):
            continue
        if token in seen:
            continue
        seen.add(token)
        escaped = token.replace('"', '""')
        terms.append(f'"{escaped}"')
    return " OR ".join(terms)


def _search_lexical(
    storage: Storage,
    query_text: str,
    limit: int,
    collection_id: str | None = None,
) -> list[SourceChunk]:
    query = lexical_query_from_text(query_text)
    if not query:
        return []

    try:
        with storage.database.connect() as connection:
            if collection_id is None:
                rows = connection.execute(
                    """
                    SELECT
                        chunk_id,
                        document_id,
                        document_title,
                        chunk_index,
                        content
                    FROM chunks_fts
                    WHERE chunks_fts MATCH ?
                    ORDER BY bm25(chunks_fts, 0.0, 0.0, 1.5, 0.0, 1.0)
                    LIMIT ?
                    """,
                    (query, limit),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT
                        chunk_id,
                        document_id,
                        document_title,
                        chunk_index,
                        content
                    FROM chunks_fts
                    WHERE chunks_fts MATCH ?
                      AND EXISTS (
                          SELECT 1
                          FROM collection_sources
                          WHERE collection_sources.collection_id = ?
                            AND collection_sources.document_id = chunks_fts.document_id
                            AND collection_sources.status = 'active'
                      )
                    ORDER BY bm25(chunks_fts, 0.0, 0.0, 1.5, 0.0, 1.0)
                    LIMIT ?
                    """,
                    (query, collection_id, limit),
                ).fetchall()
    except sqlite3.OperationalError as exc:
        message = str(exc).lower()
        if "no such table" in message or "fts5" in message:
            return []
        raise

    return [
        SourceChunk(
            chunk_id=str(row["chunk_id"]),
            document_id=str(row["document_id"]),
            document_title=str(row["document_title"]),
            chunk_index=int(row["chunk_index"]),
            score=0.0,
            content=str(row["content"]),
            collection_id=collection_id,
        )
        for row in rows
    ]


def _fuse_rrf(
    dense: Sequence[SourceChunk],
    lexical: Sequence[SourceChunk],
    top_k: int,
    dense_weight: float,
    lexical_weight: float,
    rrf_k: int,
) -> list[SourceChunk]:
    dense_by_id = {source.chunk_id: source for source in dense}
    lexical_by_id = {source.chunk_id: source for source in lexical}
    dense_ranks = {source.chunk_id: rank for rank, source in enumerate(dense, start=1)}
    lexical_ranks = {source.chunk_id: rank for rank, source in enumerate(lexical, start=1)}

    candidates: list[SourceChunk] = []
    for chunk_id in dense_by_id.keys() | lexical_by_id.keys():
        dense_rank = dense_ranks.get(chunk_id)
        lexical_rank = lexical_ranks.get(chunk_id)
        fusion_score = 0.0
        channels: list[RetrievalChannel] = []

        if dense_rank is not None:
            fusion_score += dense_weight / (rrf_k + dense_rank)
            channels.append("dense")
        if lexical_rank is not None:
            fusion_score += lexical_weight / (rrf_k + lexical_rank)
            channels.append("lexical")

        source = dense_by_id.get(chunk_id) or lexical_by_id[chunk_id]
        dense_score = dense_by_id[chunk_id].score if chunk_id in dense_by_id else None
        candidates.append(
            source.model_copy(
                update={
                    "score": round(fusion_score, 8),
                    "dense_score": dense_score,
                    "dense_rank": dense_rank,
                    "lexical_rank": lexical_rank,
                    "fusion_score": round(fusion_score, 8),
                    "retrieval_channels": channels,
                }
            )
        )

    candidates.sort(
        key=lambda item: (
            -(item.fusion_score or 0.0),
            0 if item.lexical_rank is not None else 1,
            item.lexical_rank or 10_000,
            item.dense_rank or 10_000,
            item.chunk_id,
        )
    )
    return candidates[:top_k]
