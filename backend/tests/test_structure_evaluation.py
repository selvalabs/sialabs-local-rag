from __future__ import annotations

import json
from pathlib import Path

import pytest

from sialabs_local_rag.chunking import chunk_parsed_segments
from sialabs_local_rag.database import Database
from sialabs_local_rag.parsing import parse_uploaded_document_structured
from sialabs_local_rag.providers import HashEmbeddingProvider
from sialabs_local_rag.retrieval import RetrievalOptions, retrieve_sources
from sialabs_local_rag.source_metadata import persist_chunk_source_metadata
from sialabs_local_rag.storage import ChunkInput, Storage

_EVALUATION_DIR = Path(__file__).resolve().parents[1] / "evaluation"


@pytest.mark.asyncio
async def test_structure_sensitive_evaluation_cases(tmp_path: Path) -> None:
    fixture = json.loads(
        (_EVALUATION_DIR / "structure-cases.json").read_text(encoding="utf-8")
    )
    assert fixture["version"] == 1

    provider = HashEmbeddingProvider()
    for case in fixture["cases"]:
        case_id = str(case["id"])
        database = Database(f"sqlite:///{tmp_path / f'{case_id}.db'}")
        database.init_schema()
        storage = Storage(database)
        parsed = parse_uploaded_document_structured(
            case["filename"],
            case["content"].encode("utf-8"),
        )
        structured_chunks = chunk_parsed_segments(
            parsed.segments,
            chunk_size=300,
            overlap=40,
        )
        embeddings = await provider.embed(
            [chunk.content for chunk in structured_chunks]
        )
        created = storage.create_document(
            title=case["title"],
            source_type="evaluation",
            original_content=parsed.content,
            chunks=[
                ChunkInput(
                    index=index,
                    content=chunk.content,
                    embedding=embeddings[index],
                )
                for index, chunk in enumerate(structured_chunks)
            ],
            embedding_provider=provider.name,
            embedding_model=provider.model,
        )
        persist_chunk_source_metadata(database, created.id, structured_chunks)

        query_embedding = (await provider.embed([case["question"]]))[0]
        sources = retrieve_sources(
            storage=storage,
            query_text=case["question"],
            query_embedding=query_embedding,
            top_k=2,
            embedding_provider=provider.name,
            embedding_model=provider.model,
            options=RetrievalOptions(mode="hybrid"),
        )

        matching = [
            source
            for source in sources
            if source.section_title == case["expected_section"]
        ]
        assert matching, case_id
        assert matching[0].source_locator == case["expected_locator"]
        assert case["expected_evidence"] in matching[0].content
