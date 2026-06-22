from __future__ import annotations

from pathlib import Path

from sialabs_local_rag.database import Database
from sialabs_local_rag.storage import ChunkInput, Storage


def test_search_chunks_diversifies_top_sources_by_document(tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'test.db'}")
    database.init_schema()
    storage = Storage(database)

    first_document = storage.create_document(
        title="Dominant document",
        source_type="manual",
        original_content="Dominant document content with several similar chunks.",
        chunks=[
            ChunkInput(index=0, content="dominant chunk 0", embedding=[1.0, 0.0]),
            ChunkInput(index=1, content="dominant chunk 1", embedding=[0.99, 0.0]),
            ChunkInput(index=2, content="dominant chunk 2", embedding=[0.98, 0.0]),
        ],
    )
    second_document = storage.create_document(
        title="Secondary document",
        source_type="manual",
        original_content="Secondary document content with one less similar chunk.",
        chunks=[ChunkInput(index=0, content="secondary chunk", embedding=[0.5, 0.0])],
    )

    sources = storage.search_chunks(query_embedding=[1.0, 0.0], top_k=3)
    document_ids = [source.document_id for source in sources]

    assert document_ids[0] == first_document.id
    assert second_document.id in document_ids
    assert len(sources) == 3
