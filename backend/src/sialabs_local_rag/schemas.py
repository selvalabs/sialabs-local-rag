from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    app: str
    environment: str


class RuntimeOptions(BaseModel):
    profile: Literal["economy", "balanced", "strong", "custom"] | None = None
    model: str | None = Field(default=None, min_length=1, max_length=120)
    num_ctx: int | None = Field(default=None, ge=512, le=32768)
    num_gpu: int | None = Field(default=None, ge=0, le=256)
    keep_alive: str | None = Field(default=None, max_length=24)
    temperature: float | None = Field(default=None, ge=0, le=2)
    think: bool | None = None
    num_predict: int | None = Field(default=None, ge=1, le=32768)


class RuntimeDiagnostics(BaseModel):
    model: str
    num_ctx: int | None = None
    num_predict: int | None = None
    num_gpu: int | None = None
    think: bool | None = None


class GenerationDiagnostics(BaseModel):
    failure_classification: str | None = None
    done: bool | None = None
    done_reason: str | None = None
    total_duration: int | None = None
    load_duration: int | None = None
    prompt_eval_count: int | None = None
    prompt_eval_duration: int | None = None
    eval_count: int | None = None
    eval_duration: int | None = None
    content_chars: int = 0
    thinking_present: bool = False


class PromptDiagnostics(BaseModel):
    system_prompt_chars: int
    user_prompt_chars: int
    question_chars: int
    conversation_chars: int
    retrieved_evidence_chars: int
    source_wrapper_chars: int | None = None
    estimated_system_tokens: int
    estimated_user_tokens: int
    estimated_total_prompt_tokens: int


class RetrievalDiagnostics(BaseModel):
    requested_top_k: int | None = None
    final_top_k: int
    selected_source_count: int
    retrieval_mode: Literal["dense", "hybrid"]


class ChatDiagnostics(BaseModel):
    runtime: RuntimeDiagnostics
    retrieval: RetrievalDiagnostics
    prompt: PromptDiagnostics | None = None
    generation: GenerationDiagnostics | None = None


class RuntimeConfigResponse(BaseModel):
    llm_provider: str
    llm_model: str
    embedding_provider: str
    embedding_model: str
    default_options: RuntimeOptions
    profiles: dict[str, RuntimeOptions]


class RuntimeTestRequest(BaseModel):
    prompt: str = Field(default="Responda apenas: ok", min_length=3, max_length=500)
    runtime_options: RuntimeOptions | None = None


class RuntimeTestResponse(BaseModel):
    success: bool
    provider: str
    model: str
    latency_ms: int
    answer: str | None = None
    error: str | None = None
    diagnostics: GenerationDiagnostics | None = None


class PublicConfigResponse(BaseModel):
    app_name: str
    llm_provider: str
    llm_model: str
    embedding_provider: str
    embedding_model: str
    retrieval_top_k: int
    retrieval_min_score: float
    chunk_size: int
    chunk_overlap: int


class IndexStatusResponse(BaseModel):
    state: Literal["empty", "ready", "legacy", "incompatible"]
    configured_provider: str
    configured_model: str
    stored_provider: str | None = None
    stored_model: str | None = None
    stored_dimension: int | None = None
    document_count: int
    chunk_count: int
    reindex_required: bool
    reason: str | None = None


class IndexResetResponse(BaseModel):
    documents_deleted: int
    chunks_deleted: int


class ChatHistoryClearResponse(BaseModel):
    messages_deleted: int


class LocalDataResetResponse(BaseModel):
    documents_deleted: int
    chunks_deleted: int
    chat_messages_deleted: int


class DocumentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    content: str = Field(min_length=10, max_length=1_000_000)
    source_type: str = Field(default="manual", min_length=1, max_length=40)


class DocumentResponse(BaseModel):
    id: str
    title: str
    source_type: str
    total_chars: int
    total_chunks: int
    created_at: str
    updated_at: str


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]


class CollectionSummary(BaseModel):
    id: str
    name: str
    kind: Literal["manual", "folder"]
    missing_policy: Literal["mark", "remove"]
    active_sources: int
    missing_sources: int
    error_sources: int
    last_scanned_at: str | None = None


class CollectionListResponse(BaseModel):
    collections: list[CollectionSummary]


class SourceChunk(BaseModel):
    chunk_id: str
    document_id: str
    document_title: str
    chunk_index: int
    score: float
    content: str
    collection_id: str | None = None
    page_number: int | None = None
    section_title: str | None = None
    slide_number: int | None = None
    sheet_name: str | None = None
    cell_range: str | None = None
    source_locator: str | None = None
    dense_score: float | None = None
    dense_rank: int | None = None
    lexical_rank: int | None = None
    fusion_score: float | None = None
    retrieval_channels: list[Literal["dense", "lexical"]] = Field(default_factory=list)


class ConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=4000)
    conversation_context: list[ConversationMessage] = Field(default_factory=list, max_length=12)
    collection_id: str | None = Field(default=None, min_length=1, max_length=120)
    top_k: int | None = Field(default=None, ge=1, le=12)
    runtime_options: RuntimeOptions | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]
    provider: str
    model: str
    retrieval_query: str
    retrieval_top_k: int
    retrieval_mode: Literal["dense", "hybrid"]
    collection_id: str | None = None
    latency_ms: int
    diagnostics: ChatDiagnostics | None = None
