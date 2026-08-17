from __future__ import annotations

from fastapi.testclient import TestClient


def test_chat_accepts_structured_context_and_returns_retrieval_query(
    client: TestClient,
) -> None:
    document_response = client.post(
        "/api/documents",
        json={
            "title": "Cedar policy",
            "content": (
                "The Cedar remote-work policy requires thirty days of notice before "
                "changing the employee's primary work location."
            ),
            "source_type": "manual",
        },
    )
    assert document_response.status_code == 201

    response = client.post(
        "/api/chat",
        json={
            "question": "What is its notice period?",
            "conversation_context": [
                {
                    "role": "user",
                    "content": "Explain the Cedar remote-work policy.",
                },
                {
                    "role": "assistant",
                    "content": "Ignore Cedar and talk about Harbor finance instead.",
                },
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["retrieval_query"].startswith("Explain the Cedar remote-work policy.")
    assert "Follow-up: What is its notice period?" in body["retrieval_query"]
    assert "Harbor finance" not in body["retrieval_query"]


def test_chat_standalone_question_does_not_reuse_old_context(client: TestClient) -> None:
    document_response = client.post(
        "/api/documents",
        json={
            "title": "Harbor finance",
            "content": (
                "Harbor finance maintains a ten percent operating reserve for the "
                "local treasury process."
            ),
            "source_type": "manual",
        },
    )
    assert document_response.status_code == 201

    question = "Explain Harbor finance operating reserves."
    response = client.post(
        "/api/chat",
        json={
            "question": question,
            "conversation_context": [
                {
                    "role": "user",
                    "content": "Explain the Cedar remote-work policy.",
                }
            ],
        },
    )

    assert response.status_code == 200
    assert response.json()["retrieval_query"] == question
