from fastapi.testclient import TestClient


def test_chat_openapi_contract_exposes_typed_context_and_retrieval_metadata(
    client: TestClient,
) -> None:
    document = client.get("/openapi.json").json()
    schemas = document["components"]["schemas"]

    chat_request = schemas["ChatRequest"]["properties"]
    assert chat_request["question"]["minLength"] == 3
    assert "conversation_context" in chat_request
    assert "collection_id" in chat_request
    assert "runtime_options" in chat_request
    runtime_options = schemas["RuntimeOptions"]["properties"]
    assert "num_predict" in runtime_options

    chat_response = schemas["ChatResponse"]["properties"]
    assert "collection_id" in chat_response
    assert "diagnostics" in chat_response
    source_chunk = schemas["SourceChunk"]["properties"]
    for field in ("source_locator", "dense_score", "dense_rank", "lexical_rank", "fusion_score"):
        assert field in source_chunk
    assert "retrieval_channels" in source_chunk


def test_openapi_documents_local_health_and_reset_routes(client: TestClient) -> None:
    document = client.get("/openapi.json").json()
    paths = document["paths"]

    assert "/health" in paths
    assert "/api/index/status" in paths
    assert "/api/index" in paths
    assert "delete" in paths["/api/index"]
