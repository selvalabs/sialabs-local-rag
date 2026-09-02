from __future__ import annotations

from collections.abc import Sequence
from time import perf_counter

from sialabs_local_rag.chunking import chunk_parsed_segments
from sialabs_local_rag.collection_store import CollectionStore
from sialabs_local_rag.conversation import build_retrieval_query
from sialabs_local_rag.parsing import ParsedDocument, parse_plain_text_document
from sialabs_local_rag.prompting import SYSTEM_PROMPT, build_rag_prompt
from sialabs_local_rag.providers import (
    ChatProvider,
    ChatRuntimeOptions,
    EmbeddingProvider,
    ProviderError,
)
from sialabs_local_rag.retrieval import RetrievalOptions, retrieve_sources
from sialabs_local_rag.schemas import (
    ChatResponse,
    ConversationMessage,
    DocumentResponse,
    IndexResetResponse,
    IndexStatusResponse,
    RuntimeOptions,
    RuntimeTestResponse,
)
from sialabs_local_rag.settings import Settings
from sialabs_local_rag.source_metadata import persist_chunk_source_metadata
from sialabs_local_rag.storage import ChunkInput, Storage

_PROFILE_TOP_K = {
    "economy": 2,
    "balanced": 3,
    "strong": 5,
}


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
        self.collections = CollectionStore(storage.database)

    async def ingest_text(self, title: str, content: str, source_type: str) -> DocumentResponse:
        return await self.ingest_parsed_document(
            title=title,
            document=parse_plain_text_document(content),
            source_type=source_type,
        )

    async def ingest_parsed_document(
        self,
        title: str,
        document: ParsedDocument,
        source_type: str,
    ) -> DocumentResponse:
        structured_chunks = chunk_parsed_segments(
            document.segments,
            chunk_size=self.settings.chunk_size,
            overlap=self.settings.chunk_overlap,
        )
        if not structured_chunks:
            raise EmptyDocumentError("Document content did not produce any chunks.")

        self.storage.assert_embedding_compatible(
            provider=self.embedding_provider.name,
            model=self.embedding_provider.model,
        )
        chunk_contents = [chunk.content for chunk in structured_chunks]
        embeddings = await self.embedding_provider.embed(chunk_contents)
        if len(embeddings) != len(structured_chunks):
            raise ProviderError(
                "Embedding provider returned an unexpected number of vectors."
            )

        chunk_inputs = [
            ChunkInput(
                index=index,
                content=chunk.content,
                embedding=embeddings[index],
            )
            for index, chunk in enumerate(structured_chunks)
        ]
        created = self.storage.create_document(
            title=title.strip(),
            source_type=source_type.strip(),
            original_content=document.content,
            chunks=chunk_inputs,
            embedding_provider=self.embedding_provider.name,
            embedding_model=self.embedding_provider.model,
        )
        persist_chunk_source_metadata(
            database=self.storage.database,
            document_id=created.id,
            chunks=structured_chunks,
        )
        self.collections.attach_default_document(created)
        return created

    async def answer_question(
        self,
        question: str,
        conversation_context: Sequence[ConversationMessage] = (),
        collection_id: str | None = None,
        top_k: int | None = None,
        runtime_options: RuntimeOptions | None = None,
    ) -> ChatResponse:
        started_at = perf_counter()
        if collection_id is not None:
            self.collections.get_collection(collection_id)

        selected_top_k = top_k or get_top_k_for_runtime(
            runtime_options,
            default_top_k=self.settings.retrieval_top_k,
        )
        self.storage.assert_embedding_compatible(
            provider=self.embedding_provider.name,
            model=self.embedding_provider.model,
        )

        retrieval_query = build_retrieval_query(question, conversation_context)
        query_embedding = (await self.embedding_provider.embed([retrieval_query]))[0]
        sources = retrieve_sources(
            storage=self.storage,
            query_text=retrieval_query,
            query_embedding=query_embedding,
            top_k=selected_top_k,
            embedding_provider=self.embedding_provider.name,
            embedding_model=self.embedding_provider.model,
            options=RetrievalOptions(
                mode=self.settings.retrieval_mode,
                minimum_dense_score=self.settings.retrieval_min_score,
                dense_weight=self.settings.retrieval_dense_weight,
                lexical_weight=self.settings.retrieval_lexical_weight,
                rrf_k=self.settings.retrieval_rrf_k,
                candidate_multiplier=self.settings.retrieval_candidate_multiplier,
            ),
            collection_id=collection_id,
        )
        provider_runtime_options = to_provider_runtime_options(runtime_options)

        if not sources:
            answer = (
                "Não encontrei evidência relevante suficiente nos documentos indexados "
                "para responder essa pergunta."
            )
        else:
            user_prompt = build_rag_prompt(
                question=question,
                sources=sources,
                conversation_context=conversation_context,
            )
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
            retrieval_query=retrieval_query,
            retrieval_top_k=selected_top_k,
            retrieval_mode=self.settings.retrieval_mode,
            collection_id=collection_id,
            latency_ms=latency_ms,
        )

    def get_index_status(self) -> IndexStatusResponse:
        return self.storage.get_embedding_index_status(
            configured_provider=self.embedding_provider.name,
            configured_model=self.embedding_provider.model,
        )

    def reset_index(self) -> IndexResetResponse:
        return self.storage.reset_embedding_index()

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
    if runtime_options is None or runtime_options.profile is None:
        return default_top_k
    return _PROFILE_TOP_K.get(runtime_options.profile, default_top_k)


def to_provider_runtime_options(
    runtime_options: RuntimeOptions | None,
) -> ChatRuntimeOptions | None:
    if runtime_options is None:
        return None
    return ChatRuntimeOptions(
        model=runtime_options.model,
        num_ctx=runtime_options.num_ctx,
        num_gpu=runtime_options.num_gpu,
        keep_alive=runtime_options.keep_alive,
        temperature=runtime_options.temperature,
        think=runtime_options.think,
    )
