from __future__ import annotations

from pathlib import Path

import pytest

from sialabs_local_rag.database import Database
from sialabs_local_rag.storage import (
    ChunkInput,
    EmbeddingIndexCompatibilityError,
    EmbeddingIndexReindexRequiredError,
    Storage,
)


def test_search_chunks_prefers_multiple_stronger_chunks_from_same_document(tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'test.db'}")
    database.init_schema()
    storage = Storage(database)

    first_document = storage.create_document(
        title="Dominant document",
        source_type="manual",
        original_content="Dominant document content with several similar chunks.",
        chunks=[
            ChunkInput(index=0, content="dominant chunk 0", embedding=[1.0, 0.0]),
            ChunkInput(index=1, content="dominant chunk 1", embedding=[0.9, 0.1]),
            ChunkInput(index=2, content="dominant chunk 2", embedding=[0.8, 0.2]),
        ],
        embedding_provider="test",
        embedding_model="test-model",
    )
    storage.create_document(
        title="Secondary document",
        source_type="manual",
        original_content="Secondary document content with one less similar chunk.",
        chunks=[ChunkInput(index=0, content="secondary chunk", embedding=[0.5, 0.5])],
        embedding_provider="test",
        embedding_model="test-model",
    )

    sources = storage.search_chunks(
        query_embedding=[1.0, 0.0],
        top_k=3,
        embedding_provider="test",
        embedding_model="test-model",
    )

    assert [source.document_id for source in sources] == [first_document.id] * 3
    assert [source.chunk_index for source in sources] == [0, 1, 2]
    assert [source.score for source in sources] == sorted(
        [source.score for source in sources], reverse=True
    )


def test_search_chunks_applies_minimum_score_and_can_return_fewer_than_top_k(tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'threshold.db'}")
    database.init_schema()
    storage = Storage(database)

    storage.create_document(
        title="Threshold document",
        source_type="manual",
        original_content="Threshold document with strong and weak evidence chunks.",
        chunks=[
            ChunkInput(index=0, content="strong", embedding=[1.0, 0.0]),
            ChunkInput(index=1, content="medium", embedding=[0.8, 0.6]),
            ChunkInput(index=2, content="weak", embedding=[0.2, 0.98]),
        ],
        embedding_provider="test",
        embedding_model="test-model",
    )

    sources = storage.search_chunks(
        query_embedding=[1.0, 0.0],
        top_k=5,
        embedding_provider="test",
        embedding_model="test-model",
        minimum_score=0.75,
    )

    assert [source.chunk_index for source in sources] == [0, 1]
    assert len(sources) < 5


def test_search_chunks_can_reject_all_candidates_below_threshold(tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'no-evidence.db'}")
    database.init_schema()
    storage = Storage(database)

    storage.create_document(
        title="Unrelated document",
        source_type="manual",
        original_content="Document whose vector is orthogonal to the query.",
        chunks=[ChunkInput(index=0, content="unrelated", embedding=[0.0, 1.0])],
        embedding_provider="test",
        embedding_model="test-model",
    )

    sources = storage.search_chunks(
        query_embedding=[1.0, 0.0],
        top_k=3,
        embedding_provider="test",
        embedding_model="test-model",
        minimum_score=0.1,
    )

    assert sources == []


def test_embedding_index_rejects_different_model_while_chunks_exist(tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'mismatch.db'}")
    database.init_schema()
    storage = Storage(database)

    storage.create_document(
        title="First",
        source_type="manual",
        original_content="First indexed document content.",
        chunks=[ChunkInput(index=0, content="first chunk", embedding=[1.0, 0.0])],
        embedding_provider="ollama",
        embedding_model="embeddinggemma",
    )

    with pytest.raises(EmbeddingIndexCompatibilityError, match="stored index uses"):
        storage.create_document(
            title="Second",
            source_type="manual",
            original_content="Second indexed document content.",
            chunks=[ChunkInput(index=0, content="second chunk", embedding=[1.0, 0.0])],
            embedding_provider="ollama",
            embedding_model="different-model",
        )


def test_embedding_index_rejects_dimension_mismatch(tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'dimension.db'}")
    database.init_schema()
    storage = Storage(database)

    storage.create_document(
        title="Dimension source",
        source_type="manual",
        original_content="Document used to establish a two-dimensional embedding space.",
        chunks=[ChunkInput(index=0, content="dimension chunk", embedding=[1.0, 0.0])],
        embedding_provider="test",
        embedding_model="same-model",
    )

    with pytest.raises(EmbeddingIndexCompatibilityError, match="dimension mismatch"):
        storage.search_chunks(
            query_embedding=[1.0, 0.0, 0.0],
            top_k=1,
            embedding_provider="test",
            embedding_model="same-model",
        )


def test_legacy_chunks_without_embedding_metadata_require_reset(tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'legacy-index.db'}")
    database.init_schema()
    storage = Storage(database)

    with database.connect() as connection:
        connection.execute(
            """
            INSERT INTO documents (
                id, title, source_type, content_hash, total_chars,
                total_chunks, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "legacy-doc",
                "Legacy",
                "manual",
                "legacy-hash",
                20,
                1,
                "2026-01-01T00:00:00+00:00",
                "2026-01-01T00:00:00+00:00",
            ),
        )
        connection.execute(
            """
            INSERT INTO chunks (
                id, document_id, chunk_index, content,
                token_estimate, embedding_json, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "legacy-chunk",
                "legacy-doc",
                0,
                "legacy content",
                4,
                "[1.0,0.0]",
                "2026-01-01T00:00:00+00:00",
            ),
        )

    status = storage.get_embedding_index_status(
        configured_provider="test",
        configured_model="test-model",
    )
    assert status.state == "legacy"
    assert status.reindex_required is True

    with pytest.raises(EmbeddingIndexReindexRequiredError, match="predate embedding metadata"):
        storage.assert_embedding_compatible(provider="test", model="test-model")


def test_reset_embedding_index_allows_new_embedding_signature(tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'reset.db'}")
    database.init_schema()
    storage = Storage(database)

    storage.create_document(
        title="Before reset",
        source_type="manual",
        original_content="Content before resetting the embedding index.",
        chunks=[ChunkInput(index=0, content="before reset", embedding=[1.0, 0.0])],
        embedding_provider="test",
        embedding_model="old-model",
    )

    result = storage.reset_embedding_index()
    assert result.documents_deleted == 1
    assert result.chunks_deleted == 1

    storage.create_document(
        title="After reset",
        source_type="manual",
        original_content="Content after resetting the embedding index.",
        chunks=[ChunkInput(index=0, content="after reset", embedding=[1.0, 0.0, 0.0])],
        embedding_provider="test",
        embedding_model="new-model",
    )

    status = storage.get_embedding_index_status(
        configured_provider="test",
        configured_model="new-model",
    )
    assert status.state == "ready"
    assert status.stored_dimension == 3
