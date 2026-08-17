from __future__ import annotations

import re
import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from sialabs_local_rag.schemas import SourceChunk
from sialabs_local_rag.storage import Storage

RetrievalMode = Literal["dense", "hybrid"]

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
) -> list[SourceChunk]:
    candidate_k = max(top_k, top_k * options.candidate_multiplier)
    dense = storage.search_chunks(
        query_embedding=query_embedding,
        top_k=candidate_k,
        embedding_provider=embedding_provider,
        embedding_model=embedding_model,
        minimum_score=options.minimum_dense_score,
    )

    if options.mode == "dense":
        return [
            source.model_copy(
                update={
                    "dense_score": source.score,
                    "dense_rank": rank,
                    "retrieval_channels": ["dense"],
                }
            )
            for rank, source in enumerate(dense[:top_k], start=1)
        ]

    lexical = _search_lexical(storage, query_text=query_text, limit=candidate_k)
    if not lexical:
        return [
            source.model_copy(
                update={
                    "dense_score": source.score,
                    "dense_rank": rank,
                    "retrieval_channels": ["dense"],
                }
            )
            for rank, source in enumerate(dense[:top_k], start=1)
        ]

    return _fuse_rrf(
        dense=dense,
        lexical=lexical,
        top_k=top_k,
        dense_weight=options.dense_weight,
        lexical_weight=options.lexical_weight,
        rrf_k=options.rrf_k,
    )


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


def _search_lexical(storage: Storage, query_text: str, limit: int) -> list[SourceChunk]:
    query = lexical_query_from_text(query_text)
    if not query:
        return []

    try:
        with storage.database.connect() as connection:
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
        channels: list[str] = []

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
            item.fusion_score or 0.0,
            0 if item.lexical_rank is not None else -1,
            -(item.lexical_rank or 10_000),
            -(item.dense_rank or 10_000),
        ),
        reverse=True,
    )
    return candidates[:top_k]
