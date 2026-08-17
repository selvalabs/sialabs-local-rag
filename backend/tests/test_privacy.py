from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from starlette.requests import Request

from sialabs_local_rag.api import require_local_data_reset
from sialabs_local_rag.database import Database
from sialabs_local_rag.schemas import SourceChunk
from sialabs_local_rag.settings import Settings
from sialabs_local_rag.storage import ChunkInput, Storage


def _source(document_id: str = "doc-1", content: str = "private source excerpt") -> SourceChunk:
    return SourceChunk(
        chunk_id="chunk-1",
        document_id=document_id,
        document_title="Private document",
        chunk_index=0,
        score=0.91,
        content=content,
    )


def _chat_count(database: Database) -> int:
    with database.connect() as connection:
        row = connection.execute("SELECT COUNT(*) AS count FROM chat_messages").fetchone()
    return int(row["count"]) if row is not None else 0


def test_new_chat_records_do_not_duplicate_source_content(tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'privacy.db'}")
    database.init_schema()
    storage = Storage(database)

    storage.create_chat_record(
        question="What is private?",
        answer="A grounded answer.",
        provider="mock",
        model="test-model",
        latency_ms=12,
        sources=[_source(content="sensitive chunk text that must not be persisted")],
    )

    with database.connect() as connection:
        row = connection.execute("SELECT metadata_json FROM chat_messages").fetchone()

    assert row is not None
    metadata = json.loads(str(row["metadata_json"]))
    assert metadata["sources"][0]["chunk_id"] == "chunk-1"
    assert metadata["sources"][0]["document_id"] == "doc-1"
    assert "content" not in metadata["sources"][0]
    assert "sensitive chunk text" not in str(row["metadata_json"])


def test_schema_v3_scrubs_source_content_from_existing_chat_metadata(tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'migration.db'}")
    database.init_schema()

    legacy_metadata = {
        "sources": [
            {
                "chunk_id": "legacy-chunk",
                "document_id": "legacy-doc",
                "document_title": "Legacy document",
                "chunk_index": 0,
                "score": 0.8,
                "content": "legacy private source text",
            }
        ],
        "other": "preserved",
    }
    with database.connect() as connection:
        connection.execute(
            """
            INSERT INTO chat_messages (
                id, question, answer, provider, model,
                latency_ms, metadata_json, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "legacy-chat",
                "legacy question",
                "legacy answer",
                "mock",
                "mock-model",
                1,
                json.dumps(legacy_metadata),
                "2026-01-01T00:00:00+00:00",
            ),
        )
        connection.execute("UPDATE schema_version SET version = 2 WHERE singleton = 1")

    database.init_schema()

    with database.connect() as connection:
        row = connection.execute(
            "SELECT metadata_json FROM chat_messages WHERE id = 'legacy-chat'"
        ).fetchone()

    assert row is not None
    metadata = json.loads(str(row["metadata_json"]))
    assert metadata["other"] == "preserved"
    assert metadata["sources"][0]["chunk_id"] == "legacy-chunk"
    assert "content" not in metadata["sources"][0]
    assert "legacy private source text" not in str(row["metadata_json"])


def test_deleting_document_clears_persisted_chat_history(tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'delete-document.db'}")
    database.init_schema()
    storage = Storage(database)

    document = storage.create_document(
        title="Delete me",
        source_type="manual",
        original_content="Document content that will be deleted together with derived chat traces.",
        chunks=[ChunkInput(index=0, content="delete me", embedding=[1.0, 0.0])],
        embedding_provider="test",
        embedding_model="test-model",
    )
    storage.create_chat_record(
        question="Question",
        answer="Answer",
        provider="mock",
        model="test-model",
        latency_ms=1,
        sources=[_source(document_id=document.id)],
    )
    assert _chat_count(database) == 1

    assert storage.delete_document(document.id) is True
    assert _chat_count(database) == 0


def test_index_reset_also_clears_chat_history(tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'reset-index.db'}")
    database.init_schema()
    storage = Storage(database)

    document = storage.create_document(
        title="Reset me",
        source_type="manual",
        original_content="Document content used to test reset retention semantics.",
        chunks=[ChunkInput(index=0, content="reset me", embedding=[1.0, 0.0])],
        embedding_provider="test",
        embedding_model="test-model",
    )
    storage.create_chat_record(
        question="Question",
        answer="Answer",
        provider="mock",
        model="test-model",
        latency_ms=1,
        sources=[_source(document_id=document.id)],
    )

    storage.reset_embedding_index()

    assert _chat_count(database) == 0


def test_clear_chat_history_endpoint_deletes_backend_trace(client: TestClient) -> None:
    document_response = client.post(
        "/api/documents",
        json={
            "title": "Chat history source",
            "content": "A document with enough content to produce a grounded mock chat response.",
            "source_type": "manual",
        },
    )
    assert document_response.status_code == 201
    chat_response = client.post(
        "/api/chat",
        json={"question": "What does the source contain?"},
    )
    assert chat_response.status_code == 200

    response = client.delete("/api/chat/history")

    assert response.status_code == 200
    assert response.json()["messages_deleted"] == 1
    assert _chat_count(client.app.state.storage.database) == 0


def test_full_local_data_reset_requires_explicit_confirmation(client: TestClient) -> None:
    response = client.delete("/api/local-data")

    assert response.status_code == 400
    assert "X-Confirm-Local-Data-Reset" in response.json()["detail"]


def test_full_local_data_reset_clears_documents_vectors_and_chat(client: TestClient) -> None:
    document_response = client.post(
        "/api/documents",
        json={
            "title": "Reset all source",
            "content": "A document that will be removed by the guarded full local data reset.",
            "source_type": "manual",
        },
    )
    assert document_response.status_code == 201
    chat_response = client.post(
        "/api/chat",
        json={"question": "What is being reset?"},
    )
    assert chat_response.status_code == 200

    response = client.delete(
        "/api/local-data",
        headers={"X-Confirm-Local-Data-Reset": "delete-all"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["documents_deleted"] == 1
    assert body["chunks_deleted"] >= 1
    assert body["chat_messages_deleted"] == 1
    assert client.get("/api/documents").json()["documents"] == []
    assert _chat_count(client.app.state.storage.database) == 0


def test_full_local_data_reset_rejects_non_loopback_clients() -> None:
    request = Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "DELETE",
            "scheme": "http",
            "path": "/api/local-data",
            "raw_path": b"/api/local-data",
            "query_string": b"",
            "headers": [],
            "client": ("10.10.10.10", 12345),
            "server": ("localhost", 8000),
        }
    )
    settings = Settings(app_env="development")

    with pytest.raises(HTTPException) as exc_info:
        require_local_data_reset(request, settings, "delete-all")

    assert exc_info.value.status_code == 403
