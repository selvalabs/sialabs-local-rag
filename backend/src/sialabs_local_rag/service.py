from __future__ import annotations

from time import perf_counter

from sialabs_local_rag.chunking import chunk_text
from sialabs_local_rag.prompting import SYSTEM_PROMPT, build_rag_prompt
from sialabs_local_rag.providers import (
    ChatProvider,
    ChatRuntimeOptions,
    EmbeddingProvider,
    ProviderError,
)
from sialabs_local_rag.schemas import (
    ChatResponse,
    DocumentResponse,
    RuntimeOptions,
    RuntimeTestResponse,
)
from sialabs_local_rag.settings import Settings
from sialabs_local_rag.storage import ChunkInput, Storage


class EmptyDocumentError(ValueError):
    """Raised when text cannot produce valid chunks."""


class RagService:
    """Application service for ingestion and retrieval augmented generation."""

    def __init__(
        self,
        settings: Settings,
        storage: Storage,
        embedding_provider: EmbeddingProvider,
        chat_provider: ChatProvider,
    ) -> None:
        self.settings = settings
        self.storage = storage
        self.embedding_provider = embedding_provider
        self.chat_provider = chat_provider

    async def ingest_text(self, title: str, content: str, source_type: str) -> DocumentResponse:
        chunks = chunk_text(
            content,
            chunk_size=self.settings.chunk_size,
            overlap=self.settings.chunk_overlap,
        )
        if not chunks:
            raise EmptyDocumentError("Document content did not produce any chunks.")

        embeddings = await self.embedding_provider.embed(chunks)
        chunk_inputs = [
            ChunkInput(index=index, content=chunk, embedding=embeddings[index])
            for index, chunk in enumerate(chunks)
        ]
        return self.storage.create_document(
            title=title.strip(),
            source_type=source_type.strip(),
            original_content=content,
            chunks=chunk_inputs,
        )

    async def answer_question(
        self,
        question: str,
        top_k: int | None = None,
        runtime_options: RuntimeOptions | None = None,
    ) -> ChatResponse:
        started_at = perf_counter()
        selected_top_k = top_k or get_top_k_for_runtime(
            runtime_options,
            default_top_k=self.settings.retrieval_top_k,
        )
        query_embedding = (await self.embedding_provider.embed([question]))[0]
        sources = self.storage.search_chunks(query_embedding=query_embedding, top_k=selected_top_k)
        provider_runtime_options = to_provider_runtime_options(runtime_options)

        if not sources:
            answer = "Não encontrei documentos indexados para responder essa pergunta."
        else:
            user_prompt = build_rag_prompt(question=question, sources=sources)
            answer = await self.chat_provider.generate(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=user_prompt,
                runtime_options=provider_runtime_options,
            )

        latency_ms = int((perf_counter() - started_at) * 1000)
        response_model = get_response_model(runtime_options, self.chat_provider.model)
        self.storage.create_chat_record(
            question=question,
            answer=answer,
            provider=self.chat_provider.name,
            model=response_model,
            latency_ms=latency_ms,
            sources=sources,
        )

        return ChatResponse(
            answer=answer,
            sources=sources,
            provider=self.chat_provider.name,
            model=response_model,
            retrieval_top_k=selected_top_k,
            latency_ms=latency_ms,
        )

    async def test_runtime(
        self,
        prompt: str,
        runtime_options: RuntimeOptions | None,
    ) -> RuntimeTestResponse:
        started_at = perf_counter()
        provider_runtime_options = to_provider_runtime_options(runtime_options)
        response_model = get_response_model(runtime_options, self.chat_provider.model)

        try:
            answer = await self.chat_provider.generate(
                system_prompt="Responda de forma curta para validar o runtime local.",
                user_prompt=prompt,
                runtime_options=provider_runtime_options,
            )
            return RuntimeTestResponse(
                success=True,
                provider=self.chat_provider.name,
                model=response_model,
                latency_ms=int((perf_counter() - started_at) * 1000),
                answer=answer,
                error=None,
            )
        except ProviderError as exc:
            return RuntimeTestResponse(
                success=False,
                provider=self.chat_provider.name,
                model=response_model,
                latency_ms=int((perf_counter() - started_at) * 1000),
                answer=None,
                error=str(exc),
            )


def get_response_model(runtime_options: RuntimeOptions | None, default_model: str) -> str:
    if runtime_options and runtime_options.model:
        return runtime_options.model
    return default_model


def get_top_k_for_runtime(runtime_options: RuntimeOptions | None, default_top_k: int) -> int:
    if runtime_options is None:
        return default_top_k
    if runtime_options.profile == "economy":
        return 2
    if runtime_options.profile == "balanced":
        return 3
    if runtime_options.profile == "strong":
        return 5
    return default_top_k


def to_provider_runtime_options(runtime_options: RuntimeOptions | None) -> ChatRuntimeOptions | None:
    if runtime_options is None:
        return None
    return ChatRuntimeOptions(
        model=runtime_options.model,
        num_ctx=runtime_options.num_ctx,
        num_gpu=runtime_options.num_gpu,
        keep_alive=runtime_options.keep_alive,
        temperature=runtime_options.temperature,
    )
