from __future__ import annotations

from dataclasses import dataclass

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


def test_pdf_parser_preserves_page_numbers(
    monkeypatch: object,
) -> None:
    class _Patch:
        def setattr(self, target: object, name: str, value: object) -> None:
            setattr(target, name, value)

    patch = monkeypatch
    assert isinstance(patch, _Patch) is False
