from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sialabs_local_rag.api import api_router
from sialabs_local_rag.database import Database
from sialabs_local_rag.providers import create_chat_provider, create_embedding_provider
from sialabs_local_rag.schemas import HealthResponse
from sialabs_local_rag.service import RagService
from sialabs_local_rag.settings import Settings
from sialabs_local_rag.storage import Storage


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or Settings()
    database = Database(app_settings.database_url)
    database.init_schema()
    storage = Storage(database)
    embedding_provider = create_embedding_provider(app_settings)
    chat_provider = create_chat_provider(app_settings)
    rag_service = RagService(
        settings=app_settings,
        storage=storage,
        embedding_provider=embedding_provider,
        chat_provider=chat_provider,
    )

    app = FastAPI(
        title=app_settings.app_name,
        version="0.3.1",
        description="Local-first RAG API with optional Ollama/Gemma integration.",
    )
    app.state.settings = app_settings
    app.state.storage = storage
    app.state.rag_service = rag_service

    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            app=app_settings.app_name,
            environment=app_settings.app_env,
        )

    @app.get("/")
    def root() -> dict[str, str]:
        return {
            "app": app_settings.app_name,
            "docs": "/docs",
            "health": "/health",
        }

    app.include_router(api_router, prefix=app_settings.api_prefix)
    return app


app = create_app()
