from __future__ import annotations

from fastapi.testclient import TestClient


def _build_two_page_pdf(first_text: str, second_text: str) -> bytes:
    first_stream = f"BT /F1 12 Tf 72 720 Td ({first_text}) Tj ET".encode("latin-1")
    second_stream = f"BT /F1 12 Tf 72 720 Td ({second_text}) Tj ET".encode("latin-1")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R 4 0 R] /Count 2 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 5 0 R >> >> /Contents 6 0 R >>"
        ),
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 5 0 R >> >> /Contents 7 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length "
        + str(len(first_stream)).encode("ascii")
        + b" >>\nstream\n"
        + first_stream
        + b"\nendstream",
        b"<< /Length "
        + str(len(second_stream)).encode("ascii")
        + b" >>\nstream\n"
        + second_stream
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


def test_markdown_upload_returns_section_metadata_in_retrieved_source(
    client: TestClient,
) -> None:
    markdown = (
        b"# Safety\n\n"
        b"Wear protective equipment during inspection.\n\n"
        b"# Recovery\n\n"
        b"Use exact recovery code ZX-81 before restarting the console.\n"
    )
    upload = client.post(
        "/api/documents/upload",
        files={"file": ("manual.md", markdown, "text/markdown")},
    )
    assert upload.status_code == 201

    response = client.post(
        "/api/chat",
        json={"question": "Which recovery section mentions ZX-81?", "top_k": 3},
    )
    assert response.status_code == 200

    recovery_sources = [
        source
        for source in response.json()["sources"]
        if source["section_title"] == "Recovery"
    ]
    assert recovery_sources
    assert recovery_sources[0]["source_locator"] == "section:Recovery"
    assert "Section: Recovery" in recovery_sources[0]["content"]
    assert "ZX-81" in recovery_sources[0]["content"]


def test_two_page_pdf_returns_originating_page_metadata(client: TestClient) -> None:
    pdf = _build_two_page_pdf(
        "ALPHA-PAGE-ONE inspection procedure",
        "BETA-PAGE-TWO recovery procedure",
    )
    upload = client.post(
        "/api/documents/upload",
        files={"file": ("two-pages.pdf", pdf, "application/pdf")},
    )
    assert upload.status_code == 201
    assert upload.json()["total_chunks"] == 2

    response = client.post(
        "/api/chat",
        json={"question": "Where is BETA-PAGE-TWO documented?", "top_k": 2},
    )
    assert response.status_code == 200

    page_two = [
        source for source in response.json()["sources"] if source["page_number"] == 2
    ]
    assert page_two
    assert page_two[0]["source_locator"] == "page:2"
    assert page_two[0]["content"].startswith("Page 2\n\n")
    assert "BETA-PAGE-TWO" in page_two[0]["content"]


def test_plain_text_ingestion_preserves_paragraph_boundary(client: TestClient) -> None:
    content = (
        "Alpha paragraph explains the SUNFLOWER-CODE operating rule.\n\n"
        "Second paragraph preserves a separate explanatory block."
    )
    upload = client.post(
        "/api/documents",
        json={
            "title": "Paragraph document",
            "content": content,
            "source_type": "manual",
        },
    )
    assert upload.status_code == 201

    response = client.post(
        "/api/chat",
        json={"question": "What is SUNFLOWER-CODE?", "top_k": 1},
    )
    assert response.status_code == 200
    source = response.json()["sources"][0]
    assert "Alpha paragraph" in source["content"]
    assert "\n\nSecond paragraph" in source["content"]
    assert source["page_number"] is None
    assert source["section_title"] is None
