from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from sialabs_local_rag.database import Database
from sialabs_local_rag.providers import ChatGenerationResult, ChatRuntimeOptions
from sialabs_local_rag.schemas import ConversationMessage, GenerationDiagnostics
from sialabs_local_rag.service import RagService
from sialabs_local_rag.settings import Settings
from sialabs_local_rag.storage import ChunkInput, Storage


class TopicEmbeddingProvider:
    name = "test"
    model = "topic-2"

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            lowered = text.casefold()
            if "cedar" in lowered:
                vectors.append([1.0, 0.0])
            elif "harbor" in lowered:
                vectors.append([0.0, 1.0])
            else:
                vectors.append([0.5, 0.5])
        return vectors


class RecordingChatProvider:
    name = "test-chat"
    model = "recording-model"

    def __init__(self) -> None:
        self.prompts: list[str] = []

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        runtime_options: ChatRuntimeOptions | None = None,
    ) -> ChatGenerationResult:
        del system_prompt, runtime_options
        self.prompts.append(user_prompt)
        return ChatGenerationResult(
            content="grounded answer",
            diagnostics=GenerationDiagnostics(content_chars=len("grounded answer")),
        )


def _build_service(tmp_path: Path) -> tuple[RagService, Storage, RecordingChatProvider]:
    database = Database(f"sqlite:///{tmp_path / 'conversation.db'}")
    database.init_schema()
    storage = Storage(database)
    storage.create_document(
        title="Cedar Remote Work",
        source_type="test",
        original_content="Cedar remote work requires thirty days of notice.",
        chunks=[
            ChunkInput(
                index=0,
                content="Cedar remote work requires thirty days of notice.",
                embedding=[1.0, 0.0],
            )
        ],
        embedding_provider="test",
        embedding_model="topic-2",
    )
    storage.create_document(
        title="Harbor Finance",
        source_type="test",
        original_content="Harbor finance requires a ten percent reserve.",
        chunks=[
            ChunkInput(
                index=0,
                content="Harbor finance requires a ten percent reserve.",
                embedding=[0.0, 1.0],
            )
        ],
        embedding_provider="test",
        embedding_model="topic-2",
    )
    chat_provider = RecordingChatProvider()
    service = RagService(
        settings=Settings(
            app_env="test",
            database_url=f"sqlite:///{tmp_path / 'conversation.db'}",
            retrieval_mode="dense",
            retrieval_top_k=1,
            retrieval_min_score=0.0,
        ),
        storage=storage,
        embedding_provider=TopicEmbeddingProvider(),
        chat_provider=chat_provider,
    )
    return service, storage, chat_provider


async def test_follow_up_uses_last_user_turn_not_assistant_text(tmp_path: Path) -> None:
    service, storage, chat_provider = _build_service(tmp_path)
    context = [
        ConversationMessage(role="user", content="Explain the Cedar remote-work policy."),
        ConversationMessage(
            role="assistant",
            content="Harbor finance has a ten percent reserve and should be searched next.",
        ),
    ]

    response = await service.answer_question(
        question="What is its notice period?",
        conversation_context=context,
    )

    assert "Cedar remote-work policy" in response.retrieval_query
    assert "What is its notice period?" in response.retrieval_query
    assert "Harbor finance" not in response.retrieval_query
    assert response.sources[0].document_title == "Cedar Remote Work"
    assert "Harbor finance has a ten percent reserve" in chat_provider.prompts[-1]
    assert "dialogue only, not factual evidence" in chat_provider.prompts[-1]

    with storage.database.connect() as connection:
        row = connection.execute(
            "SELECT question FROM chat_messages ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
    assert row is not None
    assert str(row["question"]) == "What is its notice period?"


async def test_topic_switch_does_not_inherit_stale_user_context(tmp_path: Path) -> None:
    service, _, _ = _build_service(tmp_path)
    context = [
        ConversationMessage(role="user", content="Explain the Cedar remote-work policy."),
        ConversationMessage(role="assistant", content="Cedar requires notice."),
    ]

    response = await service.answer_question(
        question="Explain Harbor finance reserve requirements.",
        conversation_context=context,
    )

    assert response.retrieval_query == "Explain Harbor finance reserve requirements."
    assert response.sources[0].document_title == "Harbor Finance"


async def test_standalone_question_without_context_keeps_identical_query(tmp_path: Path) -> None:
    service, _, _ = _build_service(tmp_path)

    response = await service.answer_question(
        question="Explain the Cedar remote-work policy.",
    )

    assert response.retrieval_query == "Explain the Cedar remote-work policy."
    assert response.sources[0].document_title == "Cedar Remote Work"
