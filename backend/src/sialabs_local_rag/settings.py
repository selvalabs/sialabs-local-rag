from __future__ import annotations

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    app_name: str = "SoberanIA Labs Local RAG"
    app_env: str = "development"
    api_prefix: str = "/api"
    database_url: str = "sqlite:///./data/sialabs_local_rag.db"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    chunk_size: int = Field(default=1200, ge=300, le=8000)
    chunk_overlap: int = Field(default=180, ge=0, le=2000)
    retrieval_top_k: int = Field(default=5, ge=1, le=12)

    llm_provider: Literal["mock", "ollama"] = "mock"
    embedding_provider: Literal["hash", "ollama"] = "hash"

    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "gemma4:e2b"
    ollama_embed_model: str = "embeddinggemma"
    ollama_request_timeout_seconds: float = Field(default=120.0, gt=0)
    ollama_temperature: float = Field(default=0.2, ge=0, le=2)
    ollama_num_ctx: int | None = Field(default=1024, ge=512, le=32768)
    ollama_num_gpu: int | None = Field(default=None, ge=0, le=256)
    ollama_keep_alive: str | None = "5m"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
