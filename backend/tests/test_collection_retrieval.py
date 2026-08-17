from __future__ import annotations

from pathlib import Path

from sialabs_local_rag.collection_store import CollectionStore
from sialabs_local_rag.database import Database
from sialabs_local_rag.retrieval import RetrievalOptions, retrieve_sources
from sialabs_local_rag.storage import ChunkInput, Storage


def test_collection_filter_isolates_dense_and_lexical_candidates(tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'isolation.db'}")
    database.init_schema()
    storage = Storage(database)
    collections = CollectionStore(database)
    first_folder = tmp_path / "alpha"
    second_folder = tmp_path / "beta"
    first_folder.mkdir()
    second_folder.mkdir()
    alpha_collection = collections.register_folder("Alpha", first_folder)
    beta_collection = collections.register_folder("Beta", second_folder)

    alpha_document = storage.create_document(
        title="Alpha document",
        source_type="folder",
        original_content="ALPHA-ONLY-77 belongs only to the Alpha collection.",
        chunks=[
            ChunkInput(
                index=0,
                content="ALPHA-ONLY-77 belongs only to the Alpha collection.",
                embedding=[0.8, 0.2],
            )
        ],
        embedding_provider="test",
        embedding_model="two-dimensional",
    )
    beta_document = storage.create_document(
        title="Beta document",
        source_type="folder",
        original_content="BETA-TARGET-99 belongs only to the Beta collection.",
        chunks=[
            ChunkInput(
                index=0,
                content="BETA-TARGET-99 belongs only to the Beta collection.",
                embedding=[1.0, 0.0],
            )
        ],
        embedding_provider="test",
        embedding_model="two-dimensional",
    )
    collections.upsert_file_source(
        alpha_collection.id,
        "alpha.txt",
        alpha_document.id,
        "alpha-raw-hash",
        50,
        1,
    )
    collections.upsert_file_source(
        beta_collection.id,
        "beta.txt",
        beta_document.id,
        "beta-raw-hash",
        50,
        1,
    )

    alpha_sources = retrieve_sources(
        storage=storage,
        query_text="BETA-TARGET-99",
        query_embedding=[1.0, 0.0],
        top_k=3,
        embedding_provider="test",
        embedding_model="two-dimensional",
        options=RetrievalOptions(mode="hybrid", minimum_dense_score=0.0),
        collection_id=alpha_collection.id,
    )
    beta_sources = retrieve_sources(
        storage=storage,
        query_text="BETA-TARGET-99",
        query_embedding=[1.0, 0.0],
        top_k=3,
        embedding_provider="test",
        embedding_model="two-dimensional",
        options=RetrievalOptions(mode="hybrid", minimum_dense_score=0.0),
        collection_id=beta_collection.id,
    )
    full_base_sources = retrieve_sources(
        storage=storage,
        query_text="BETA-TARGET-99",
        query_embedding=[1.0, 0.0],
        top_k=1,
        embedding_provider="test",
        embedding_model="two-dimensional",
        options=RetrievalOptions(mode="hybrid", minimum_dense_score=0.0),
    )

    assert alpha_sources
    assert {source.document_id for source in alpha_sources} == {alpha_document.id}
    assert all(source.collection_id == alpha_collection.id for source in alpha_sources)
    assert all("BETA-TARGET-99" not in source.content for source in alpha_sources)

    assert beta_sources
    assert {source.document_id for source in beta_sources} == {beta_document.id}
    assert all(source.collection_id == beta_collection.id for source in beta_sources)

    assert full_base_sources[0].document_id == beta_document.id
    assert full_base_sources[0].collection_id is None
