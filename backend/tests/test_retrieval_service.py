from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from sialabs_local_rag.database import Database
from sialabs_local_rag.providers import ChatRuntimeOptions
from sialabs_local_rag.service import RagService
from sialabs_local_rag.settings import Settings
from sialabs_local_rag.storage import Storage


class OrthogonalEmbeddingProvider:
    name = "test"
    model = "orthogonal-2"

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [
            [0.0, 1.0] if text.startswith("UNRELATED") else [1.0, 0.0]
            for text in texts
        ]


class FailIfCalledChatProvider:
    name = "test"
    model = "must-not-run"

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        runtime_options: ChatRuntimeOptions | None = None,
    ) -> str:
        del system_prompt, user_prompt, runtime_options
        raise AssertionError("Chat generation must not run when retrieval returns no evidence.")


async def test_relevance_gate_returns_insufficient_evidence_without_llm_call(
    tmp_path: Path,
) -> None:
    database = Database(f"sqlite:///{tmp_path / 'service.db'}")
    database.init_schema()
    settings = Settings(
        app_env="test",
        database_url=f"sqlite:///{tmp_path / 'service.db'}",
        embedding_provider="hash",
        llm_provider="mock",
        retrieval_mode="dense",
        retrieval_min_score=0.1,
        chunk_size=300,
        chunk_overlap=0,
    )
    service = RagService(
        settings=settings,
        storage=Storage(database),
        embedding_provider=OrthogonalEmbeddingProvider(),
        chat_provider=FailIfCalledChatProvider(),
    )

    await service.ingest_text(
        title="Relevant source",
        content=(
            "This indexed document has enough text for ingestion and establishes "
            "a vector orthogonal to the later unrelated query."
        ),
        source_type="manual",
    )

    response = await service.answer_question("UNRELATED question with no relevant evidence")

    assert response.sources == []
    assert "evidência relevante suficiente" in response.answer
    assert response.provider == "test"
