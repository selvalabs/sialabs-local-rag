from __future__ import annotations

from dataclasses import dataclass

import pytest

import sialabs_local_rag.parsing as parsing_module
from sialabs_local_rag.parsing import (
    parse_markdown_document,
    parse_uploaded_document_structured,
)


def test_markdown_parser_preserves_heading_sections_and_paragraphs() -> None:
    document = parse_markdown_document(
        """
# Safety

First safety paragraph.

Second safety paragraph.

## Recovery

Recovery requires code ZX-81.
""".strip()
    )

    assert [segment.section_title for segment in document.segments] == [
        "Safety",
        "Recovery",
    ]
    assert document.segments[0].source_locator == "section:Safety"
    assert "First safety paragraph.\n\nSecond safety paragraph." in document.segments[0].content
    assert document.segments[1].source_locator == "section:Recovery"
    assert "Recovery requires code ZX-81." in document.segments[1].content


@dataclass
class _FakePage:
    text: str

    def extract_text(self) -> str:
        return self.text


class _FakeReader:
    def __init__(self) -> None:
        self.pages = [
            _FakePage("Page one contains the Alpha procedure."),
            _FakePage("Page two contains the Beta recovery code."),
        ]


def test_pdf_parser_preserves_page_numbers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(parsing_module, "PdfReader", lambda _: _FakeReader())

    document = parse_uploaded_document_structured("manual.pdf", b"fake-pdf")

    assert [segment.page_number for segment in document.segments] == [1, 2]
    assert [segment.source_locator for segment in document.segments] == [
        "page:1",
        "page:2",
    ]
    assert document.segments[0].content == "Page one contains the Alpha procedure."
    assert document.segments[1].content == "Page two contains the Beta recovery code."
    assert "Page one" in document.content
    assert "Page two" in document.content
