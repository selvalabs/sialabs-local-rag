from __future__ import annotations

from typing import Annotated, cast

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Header,
    HTTPException,
    Request,
    UploadFile,
    status,
)

from sialabs_local_rag.collection_store import CollectionNotFoundError, CollectionStore
from sialabs_local_rag.ocr import OcrUnavailableError
from sialabs_local_rag.parsing import (
    DocumentParsingError,
    UnsupportedDocumentTypeError,
    parse_uploaded_document_structured,
)
from sialabs_local_rag.providers import ProviderError
from sialabs_local_rag.schemas import (
    ChatHistoryClearResponse,
    ChatRequest,
    ChatResponse,
    CollectionListResponse,
    CollectionSummary,
    DocumentCreate,
    DocumentListResponse,
    DocumentResponse,
    IndexResetResponse,
    IndexStatusResponse,
    LocalDataResetResponse,
    PublicConfigResponse,
    RuntimeConfigResponse,
    RuntimeOptions,
    RuntimeTestRequest,
    RuntimeTestResponse,
)
from sialabs_local_rag.service import EmptyDocumentError, RagService
from sialabs_local_rag.settings import Settings
from sialabs_local_rag.storage import (
    DuplicateDocumentError,
    EmbeddingIndexCompatibilityError,
    Storage,
)

MAX_UPLOAD_BYTES = 10_000_000
_LOOPBACK_HOSTS = {"127.0.0.1", "::1"}
_LOCAL_DATA_RESET_CONFIRMATION = "delete-all"

api_router = APIRouter()


def get_settings(request: Request) -> Settings:
    return cast(Settings, request.app.state.settings)


def get_storage(request: Request) -> Storage:
    return cast(Storage, request.app.state.storage)


def get_rag_service(request: Request) -> RagService:
    return cast(RagService, request.app.state.rag_service)


def get_llm_model(settings: Settings) -> str:
    if settings.llm_provider == "ollama":
        return settings.ollama_chat_model
    return "deterministic-local-mock"


def get_embedding_model(settings: Settings) -> str:
    if settings.embedding_provider == "ollama":
        return settings.ollama_embed_model
    return "hash-bow-128"


def get_runtime_profiles(settings: Settings) -> dict[str, RuntimeOptions]:
    return {
        "economy": RuntimeOptions(
            profile="economy",
            model=settings.ollama_chat_model,
            num_ctx=1024,
            num_gpu=0,
            keep_alive="1m",
            temperature=settings.ollama_temperature,
        ),
        "balanced": RuntimeOptions(
            profile="balanced",
            model=settings.ollama_chat_model,
            num_ctx=settings.ollama_num_ctx or 2048,
            num_gpu=settings.ollama_num_gpu,
            keep_alive=settings.ollama_keep_alive,
            temperature=settings.ollama_temperature,
        ),
        "strong": RuntimeOptions(
            profile="strong",
            model=settings.ollama_chat_model,
            num_ctx=4096,
            num_gpu=settings.ollama_num_gpu,
            keep_alive=settings.ollama_keep_alive,
            temperature=settings.ollama_temperature,
        ),
    }


def require_local_data_reset(
    request: Request,
    settings: Settings,
    confirmation: str | None,
) -> None:
    client_host = request.client.host if request.client is not None else None
    is_test_client = settings.app_env == "test" and client_host == "testclient"
    if client_host not in _LOOPBACK_HOSTS and not is_test_client:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Full local data reset is only available from the loopback interface.",
        )
    if confirmation != _LOCAL_DATA_RESET_CONFIRMATION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Full local data reset requires header "
                "X-Confirm-Local-Data-Reset: delete-all."
            ),
        )


@api_router.get("/config", response_model=PublicConfigResponse)
def get_public_config(settings: Annotated[Settings, Depends(get_settings)]) -> PublicConfigResponse:
    return PublicConfigResponse(
        app_name=settings.app_name,
        llm_provider=settings.llm_provider,
        llm_model=get_llm_model(settings),
        embedding_provider=settings.embedding_provider,
        embedding_model=get_embedding_model(settings),
        retrieval_top_k=settings.retrieval_top_k,
        retrieval_min_score=settings.retrieval_min_score,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )


@api_router.get("/runtime", response_model=RuntimeConfigResponse)
def get_runtime_config(
    settings: Annotated[Settings, Depends(get_settings)],
) -> RuntimeConfigResponse:
    return RuntimeConfigResponse(
        llm_provider=settings.llm_provider,
        llm_model=get_llm_model(settings),
        embedding_provider=settings.embedding_provider,
        embedding_model=get_embedding_model(settings),
        default_options=RuntimeOptions(
            profile="balanced",
            model=settings.ollama_chat_model,
            num_ctx=settings.ollama_num_ctx,
            num_gpu=settings.ollama_num_gpu,
            keep_alive=settings.ollama_keep_alive,
            temperature=settings.ollama_temperature,
        ),
        profiles=get_runtime_profiles(settings),
    )


@api_router.post("/runtime/test", response_model=RuntimeTestResponse)
async def test_runtime(
    payload: RuntimeTestRequest,
    service: Annotated[RagService, Depends(get_rag_service)],
) -> RuntimeTestResponse:
    return await service.test_runtime(
        prompt=payload.prompt, runtime_options=payload.runtime_options
    )


@api_router.get("/index/status", response_model=IndexStatusResponse)
def get_index_status(
    service: Annotated[RagService, Depends(get_rag_service)],
) -> IndexStatusResponse:
    return service.get_index_status()


@api_router.delete("/index", response_model=IndexResetResponse)
def reset_index(
    service: Annotated[RagService, Depends(get_rag_service)],
) -> IndexResetResponse:
    return service.reset_index()


@api_router.get("/collections", response_model=CollectionListResponse)
def list_collections(
    storage: Annotated[Storage, Depends(get_storage)],
) -> CollectionListResponse:
    collection_store = CollectionStore(storage.database)
    summaries: list[CollectionSummary] = []
    for collection in collection_store.list_collections():
        active, missing, errors = collection_store.collection_counts(collection.id)
        summaries.append(
            CollectionSummary.model_validate(
                {
                    "id": collection.id,
                    "name": collection.name,
                    "kind": collection.kind,
                    "missing_policy": collection.missing_policy,
                    "active_sources": active,
                    "missing_sources": missing,
                    "error_sources": errors,
                    "last_scanned_at": collection.last_scanned_at,
                }
            )
        )
    return CollectionListResponse(collections=summaries)


@api_router.delete("/chat/history", response_model=ChatHistoryClearResponse)
def clear_chat_history(
    storage: Annotated[Storage, Depends(get_storage)],
) -> ChatHistoryClearResponse:
    return storage.clear_chat_history()


@api_router.delete("/local-data", response_model=LocalDataResetResponse)
def reset_local_data(
    request: Request,
    storage: Annotated[Storage, Depends(get_storage)],
    settings: Annotated[Settings, Depends(get_settings)],
    confirmation: Annotated[
        str | None,
        Header(alias="X-Confirm-Local-Data-Reset"),
    ] = None,
) -> LocalDataResetResponse:
    require_local_data_reset(request, settings, confirmation)
    return storage.reset_local_data()


@api_router.post(
    "/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_document(
    payload: DocumentCreate,
    service: Annotated[RagService, Depends(get_rag_service)],
) -> DocumentResponse:
    try:
        return await service.ingest_text(
            title=payload.title,
            content=payload.content,
            source_type=payload.source_type,
        )
    except DuplicateDocumentError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except EmbeddingIndexCompatibilityError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except EmptyDocumentError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except ProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


@api_router.post(
    "/documents/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    service: Annotated[RagService, Depends(get_rag_service)],
    file: Annotated[UploadFile, File()],
    title: Annotated[str | None, Form()] = None,
) -> DocumentResponse:
    filename = file.filename or "uploaded-document.txt"

    raw_content = await file.read()
    if len(raw_content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Uploaded file is larger than the 10 MB local limit.",
        )

    try:
        document = parse_uploaded_document_structured(
            filename=filename,
            raw_content=raw_content,
        )
    except UnsupportedDocumentTypeError as exc:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=str(exc),
        ) from exc
    except OcrUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except DocumentParsingError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    try:
        return await service.ingest_parsed_document(
            title=title or filename,
            document=document,
            source_type="upload",
        )
    except DuplicateDocumentError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except EmbeddingIndexCompatibilityError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except EmptyDocumentError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except ProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


@api_router.get("/documents", response_model=DocumentListResponse)
def list_documents(storage: Annotated[Storage, Depends(get_storage)]) -> DocumentListResponse:
    return DocumentListResponse(documents=storage.list_documents())


@api_router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: str, storage: Annotated[Storage, Depends(get_storage)]) -> None:
    deleted = storage.delete_document(document_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")


@api_router.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    service: Annotated[RagService, Depends(get_rag_service)],
) -> ChatResponse:
    try:
        return await service.answer_question(
            question=payload.question,
            conversation_context=payload.conversation_context,
            collection_id=payload.collection_id,
            top_k=payload.top_k,
            runtime_options=payload.runtime_options,
        )
    except CollectionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except EmbeddingIndexCompatibilityError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
