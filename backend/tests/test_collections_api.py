from __future__ import annotations

from fastapi.testclient import TestClient


def test_collection_listing_never_exposes_local_root_path(client: TestClient) -> None:
    response = client.get("/api/collections")

    assert response.status_code == 200
    body = response.json()
    assert body["collections"][0]["id"] == "default"
    assert body["collections"][0]["name"] == "Local base"
    assert body["collections"][0]["kind"] == "manual"
    assert "root_path" not in body["collections"][0]


def test_http_api_does_not_register_arbitrary_local_paths(client: TestClient) -> None:
    response = client.post(
        "/api/collections",
        json={"name": "Unsafe", "root_path": "/tmp/private"},
    )

    assert response.status_code == 405


def test_manual_document_is_queryable_in_default_collection(client: TestClient) -> None:
    created = client.post(
        "/api/documents",
        json={
            "title": "Default collection source",
            "content": "DEFAULT-COLLECTION-55 belongs to the manual local base collection.",
            "source_type": "manual",
        },
    )
    assert created.status_code == 201

    collections = client.get("/api/collections").json()["collections"]
    default = next(item for item in collections if item["id"] == "default")
    assert default["active_sources"] == 1

    response = client.post(
        "/api/chat",
        json={
            "question": "Where is DEFAULT-COLLECTION-55 documented?",
            "collection_id": "default",
            "top_k": 3,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["collection_id"] == "default"
    assert body["sources"]
    assert all(source["collection_id"] == "default" for source in body["sources"])
    assert any("DEFAULT-COLLECTION-55" in source["content"] for source in body["sources"])


def test_unknown_collection_returns_not_found_before_retrieval(client: TestClient) -> None:
    response = client.post(
        "/api/chat",
        json={
            "question": "Does this collection exist?",
            "collection_id": "does-not-exist",
        },
    )

    assert response.status_code == 404
    assert "Collection not found" in response.json()["detail"]
