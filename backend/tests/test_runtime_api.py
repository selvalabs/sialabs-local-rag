from __future__ import annotations

from fastapi.testclient import TestClient


def test_runtime_profiles_make_thinking_explicit(client: TestClient) -> None:
    response = client.get("/api/runtime")

    assert response.status_code == 200
    body = response.json()
    assert body["default_options"]["profile"] == "balanced"
    assert body["default_options"]["think"] is False
    assert body["profiles"]["economy"]["num_ctx"] == 2048
    assert body["profiles"]["economy"]["num_gpu"] == 0
    assert body["profiles"]["economy"]["think"] is False
    assert body["profiles"]["balanced"]["think"] is False
    assert body["profiles"]["strong"]["think"] is True
