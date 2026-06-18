from __future__ import annotations

from fastapi.testclient import TestClient


def build_minimal_pdf_with_text(text: str) -> bytes:
    escaped_text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    content_stream = f"BT /F1 12 Tf 72 720 Td ({escaped_text}) Tj ET".encode("latin-1")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length "
        + str(len(content_stream)).encode("ascii")
        + b" >>\nstream\n"
        + content_stream
        + b"\nendstream",
    ]

    pdf = b"%PDF-1.4\n"
    offsets: list[int] = []

    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf += f"{index} 0 obj\n".encode("ascii") + obj + b"\nendobj\n"

    xref_offset = len(pdf)
    pdf += f"xref\n0 {len(objects) + 1}\n".encode("ascii")
    pdf += b"0000000000 65535 f \n"

    for offset in offsets:
        pdf += f"{offset:010d} 00000 n \n".encode("ascii")

    pdf += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    ).encode("ascii")

    return pdf


def test_health(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_document_and_chat(client: TestClient) -> None:
    document_response = client.post(
        "/api/documents",
        json={
            "title": "SIALabs Portfolio",
            "content": (
                "SIALabs Local RAG is a portfolio project that demonstrates FastAPI, "
                "React, SQLite, RAG, local embeddings and optional Ollama integration."
            ),
            "source_type": "manual",
        },
    )

    assert document_response.status_code == 201
    document = document_response.json()
    assert document["total_chunks"] >= 1

    chat_response = client.post(
        "/api/chat",
        json={"question": "Which technologies does this project demonstrate?"},
    )

    assert chat_response.status_code == 200
    body = chat_response.json()
    assert body["provider"] == "mock"
    assert body["sources"]
    assert body["sources"][0]["document_title"] == "SIALabs Portfolio"


def test_duplicate_document_returns_conflict(client: TestClient) -> None:
    payload = {
        "title": "Duplicated document",
        "content": "This content is long enough to pass the MVP document validation.",
        "source_type": "manual",
    }

    first = client.post("/api/documents", json=payload)
    second = client.post("/api/documents", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409


def test_upload_markdown_document_still_works(client: TestClient) -> None:
    response = client.post(
        "/api/documents/upload",
        files={
            "file": (
                "demo.md",
                b"# Demo\n\nSIALabs Local RAG supports Markdown upload for local indexing.",
                "text/markdown",
            )
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "demo.md"
    assert body["source_type"] == "upload"
    assert body["total_chunks"] >= 1


def test_document_upload_accepts_text_pdf(client: TestClient) -> None:
    pdf_content = build_minimal_pdf_with_text(
        "SIALabs PDF ingestion support validates text extraction for RAG."
    )

    response = client.post(
        "/api/documents/upload",
        files={"file": ("demo.pdf", pdf_content, "application/pdf")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "demo.pdf"
    assert body["source_type"] == "upload"
    assert body["total_chunks"] >= 1


def test_document_upload_rejects_unreadable_pdf(client: TestClient) -> None:
    response = client.post(
        "/api/documents/upload",
        files={"file": ("empty.pdf", b"%PDF-1.4\nnot a valid pdf", "application/pdf")},
    )

    assert response.status_code == 422
    assert "PDF" in response.json()["detail"]


def test_document_upload_rejects_unsupported_extension(client: TestClient) -> None:
    response = client.post(
        "/api/documents/upload",
        files={"file": ("dados.exe", b"conteudo", "application/octet-stream")},
    )

    assert response.status_code == 415