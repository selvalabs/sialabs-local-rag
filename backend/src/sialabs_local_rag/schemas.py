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


class PublicConfigResponse(BaseModel):
    app_name: str
    llm_provider: str
    llm_model: str
    embedding_provider: str
    embedding_model: str
    retrieval_top_k: int
    chunk_size: int
    chunk_overlap: int


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


class SourceChunk(BaseModel):
    chunk_id: str
    document_id: str
    document_title: str
    chunk_index: int
    score: float
    content: str


class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=4000)
    top_k: int | None = Field(default=None, ge=1, le=12)
    runtime_options: RuntimeOptions | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]
    provider: str
    model: str
    retrieval_top_k: int
    latency_ms: int
