from __future__ import annotations

from sialabs_local_rag.chunking import chunk_parsed_segments, normalize_structured_text
from sialabs_local_rag.parsing import ParsedSegment


def test_structured_normalization_preserves_paragraph_boundaries() -> None:
    normalized = normalize_structured_text(
        " First   paragraph.\n\n\n Second\tparagraph. "
    )

    assert normalized == "First paragraph.\n\nSecond paragraph."


def test_markdown_section_chunks_never_cross_section_boundaries() -> None:
    chunks = chunk_parsed_segments(
        [
            ParsedSegment(
                content=("Alpha safety rule. " * 30).strip(),
                section_title="Safety",
                source_locator="section:Safety",
            ),
            ParsedSegment(
                content=("Beta recovery rule. " * 30).strip(),
                section_title="Recovery",
                source_locator="section:Recovery",
            ),
        ],
        chunk_size=180,
        overlap=30,
    )

    safety = [chunk for chunk in chunks if chunk.section_title == "Safety"]
    recovery = [chunk for chunk in chunks if chunk.section_title == "Recovery"]

    assert len(safety) > 1
    assert len(recovery) > 1
    assert all("Section: Safety" in chunk.content for chunk in safety)
    assert all("Beta recovery" not in chunk.content for chunk in safety)
    assert all(chunk.source_locator == "section:Safety" for chunk in safety)
    assert all("Section: Recovery" in chunk.content for chunk in recovery)
    assert all("Alpha safety" not in chunk.content for chunk in recovery)
    assert all(chunk.source_locator == "section:Recovery" for chunk in recovery)


def test_pdf_page_chunks_keep_originating_page() -> None:
    chunks = chunk_parsed_segments(
        [
            ParsedSegment(
                content="Alpha procedure is documented on the first page.",
                page_number=1,
                source_locator="page:1",
            ),
            ParsedSegment(
                content="Beta procedure is documented on the second page.",
                page_number=2,
                source_locator="page:2",
            ),
        ],
        chunk_size=300,
        overlap=20,
    )

    assert len(chunks) == 2
    assert chunks[0].page_number == 1
    assert chunks[0].source_locator == "page:1"
    assert chunks[0].content.startswith("Page 1\n\n")
    assert "Beta procedure" not in chunks[0].content
    assert chunks[1].page_number == 2
    assert chunks[1].source_locator == "page:2"
    assert chunks[1].content.startswith("Page 2\n\n")
    assert "Alpha procedure" not in chunks[1].content
