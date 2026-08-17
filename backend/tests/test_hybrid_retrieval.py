from __future__ import annotations

from pathlib import Path

import pytest

from sialabs_local_rag.database import Database
from sialabs_local_rag.retrieval import RetrievalOptions, retrieve_sources
from sialabs_local_rag.storage import ChunkInput, Storage


def _build_storage(tmp_path: Path) -> Storage:
    database = Database(f"sqlite:///{tmp_path / 'hybrid.db'}")
    database.init_schema()
    return Storage(database)


def _fts_available(storage: Storage) -> bool:
    with storage.database.connect() as connection:
        row = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'chunks_fts'"
        ).fetchone()
    return row is not None


def test_fts_index_tracks_document_create_and_delete(tmp_path: Path) -> None:
    storage = _build_storage(tmp_path)
    if not _fts_available(storage):
        pytest.skip("SQLite build does not provide FTS5")

    document = storage.create_document(
        title="Telemetry Manual",
        source_type="manual",
        original_content="The ZX-81 telemetry reset code is documented here.",
        chunks=[
            ChunkInput(
                index=0,
                content="Use exact code ZX-81 to reset the telemetry console.",
                embedding=[0.0, 1.0],
            )
        ],
        embedding_provider="test",
        embedding_model="two-dimensional",
    )

    with storage.database.connect() as connection:
        indexed = connection.execute(
            "SELECT chunk_id, document_title FROM chunks_fts WHERE chunks_fts MATCH ?",
            ('"zx-81"',),
        ).fetchall()
    assert len(indexed) == 1
    assert str(indexed[0]["document_title"]) == "Telemetry Manual"

    assert storage.delete_document(document.id) is True
    with storage.database.connect() as connection:
        remaining = connection.execute("SELECT COUNT(*) AS count FROM chunks_fts").fetchone()
    assert remaining is not None
    assert int(remaining["count"]) == 0


def test_hybrid_recovers_exact_code_that_dense_ranking_misses(tmp_path: Path) -> None:
    storage = _build_storage(tmp_path)
    if not _fts_available(storage):
        pytest.skip("SQLite build does not provide FTS5")

    target = storage.create_document(
        title="Telemetry Manual",
        source_type="manual",
        original_content="ZX-81 is the exact emergency reset code.",
        chunks=[
            ChunkInput(
                index=0,
                content="Emergency reset requires exact code ZX-81.",
                embedding=[0.0, 1.0],
            )
        ],
        embedding_provider="test",
        embedding_model="two-dimensional",
    )
    decoy = storage.create_document(
        title="Generic Operations",
        source_type="manual",
        original_content="Generic operations guidance without the telemetry reset code.",
        chunks=[
            ChunkInput(
                index=0,
                content="General operational recovery guidance.",
                embedding=[1.0, 0.0],
            )
        ],
        embedding_provider="test",
        embedding_model="two-dimensional",
    )

    dense = retrieve_sources(
        storage=storage,
        query_text="What does ZX-81 do?",
        query_embedding=[1.0, 0.0],
        top_k=1,
        embedding_provider="test",
        embedding_model="two-dimensional",
        options=RetrievalOptions(mode="dense", minimum_dense_score=0.5),
    )
    hybrid = retrieve_sources(
        storage=storage,
        query_text="What does ZX-81 do?",
        query_embedding=[1.0, 0.0],
        top_k=1,
        embedding_provider="test",
        embedding_model="two-dimensional",
        options=RetrievalOptions(mode="hybrid", minimum_dense_score=0.5),
    )

    assert dense[0].document_id == decoy.id
    assert hybrid[0].document_id == target.id
    assert hybrid[0].lexical_rank == 1
    assert "lexical" in hybrid[0].retrieval_channels


def test_hybrid_falls_back_to_dense_when_fts_table_is_unavailable(tmp_path: Path) -> None:
    storage = _build_storage(tmp_path)
    storage.create_document(
        title="Dense fallback",
        source_type="manual",
        original_content="Dense fallback content with enough text for a search test.",
        chunks=[
            ChunkInput(
                index=0,
                content="Dense fallback content.",
                embedding=[1.0, 0.0],
            )
        ],
        embedding_provider="test",
        embedding_model="two-dimensional",
    )

    if _fts_available(storage):
        with storage.database.connect() as connection:
            connection.execute("DROP TABLE chunks_fts")

    sources = retrieve_sources(
        storage=storage,
        query_text="Dense fallback content",
        query_embedding=[1.0, 0.0],
        top_k=1,
        embedding_provider="test",
        embedding_model="two-dimensional",
        options=RetrievalOptions(mode="hybrid"),
    )

    assert len(sources) == 1
    assert sources[0].document_title == "Dense fallback"
    assert sources[0].retrieval_channels == ["dense"]
