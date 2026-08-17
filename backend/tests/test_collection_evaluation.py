from __future__ import annotations

import json
from pathlib import Path

from sialabs_local_rag.collection_store import CollectionStore
from sialabs_local_rag.database import Database
from sialabs_local_rag.retrieval import RetrievalOptions, retrieve_sources
from sialabs_local_rag.storage import ChunkInput, Storage

_EVALUATION_DIR = Path(__file__).resolve().parents[1] / "evaluation"


def test_collection_isolation_evaluation_fixture(tmp_path: Path) -> None:
    fixture = json.loads(
        (_EVALUATION_DIR / "collection-cases.json").read_text(encoding="utf-8")
    )
    assert fixture["version"] == 1

    database = Database(f"sqlite:///{tmp_path / 'collection-eval.db'}")
    database.init_schema()
    storage = Storage(database)
    collections = CollectionStore(database)
    collection_ids: dict[str, str] = {}

    for name in ("alpha", "beta"):
        root = tmp_path / name
        root.mkdir()
        collection_ids[name] = collections.register_folder(name.title(), root).id

    for item in fixture["documents"]:
        document = storage.create_document(
            title=item["title"],
            source_type="evaluation",
            original_content=item["content"],
            chunks=[
                ChunkInput(
                    index=0,
                    content=item["content"],
                    embedding=[float(value) for value in item["embedding"]],
                )
            ],
            embedding_provider="test",
            embedding_model="collection-eval-2",
        )
        collection_key = str(item["collection"])
        collections.upsert_file_source(
            collection_ids[collection_key],
            f"{collection_key}.txt",
            document.id,
            f"{collection_key}-raw-hash",
            len(item["content"]),
            1,
        )

    query_embedding = [float(value) for value in fixture["query"]["embedding"]]
    options = RetrievalOptions(mode="hybrid", minimum_dense_score=0.0)

    alpha_sources = retrieve_sources(
        storage=storage,
        query_text=fixture["query"]["text"],
        query_embedding=query_embedding,
        top_k=2,
        embedding_provider="test",
        embedding_model="collection-eval-2",
        options=options,
        collection_id=collection_ids["alpha"],
    )
    beta_sources = retrieve_sources(
        storage=storage,
        query_text=fixture["query"]["text"],
        query_embedding=query_embedding,
        top_k=2,
        embedding_provider="test",
        embedding_model="collection-eval-2",
        options=options,
        collection_id=collection_ids["beta"],
    )
    full_sources = retrieve_sources(
        storage=storage,
        query_text=fixture["query"]["text"],
        query_embedding=query_embedding,
        top_k=1,
        embedding_provider="test",
        embedding_model="collection-eval-2",
        options=options,
    )

    assert alpha_sources[0].document_title == fixture["expectations"]["alpha"]
    assert beta_sources[0].document_title == fixture["expectations"]["beta"]
    assert full_sources[0].document_title == fixture["expectations"]["full_base"]
    assert all(source.collection_id == collection_ids["alpha"] for source in alpha_sources)
    assert all(source.collection_id == collection_ids["beta"] for source in beta_sources)
