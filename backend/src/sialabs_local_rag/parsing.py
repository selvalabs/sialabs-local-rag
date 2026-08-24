from __future__ import annotations

import re
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader

SUPPORTED_UPLOAD_EXTENSIONS = {
    ".txt",
    ".md",
    ".markdown",
    ".pdf",
    ".docx",
    ".pptx",
    ".xlsx",
    ".png",
    ".jpg",
    ".jpeg",
    ".tif",
    ".tiff",
}
_IMAGE_OCR_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}
_MAX_TEXT_PDF_PAGES = 100
_MARKDOWN_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")


class UnsupportedDocumentTypeError(ValueError):
    """Raised when the uploaded file extension is not supported."""


class DocumentParsingError(ValueError):
    """Raised when a supported file cannot be parsed into usable text."""


@dataclass(frozen=True)
class ParsedSegment:
    content: str
    page_number: int | None = None
    section_title: str | None = None
    slide_number: int | None = None
    sheet_name: str | None = None
    cell_range: str | None = None
    source_locator: str | None = None


@dataclass(frozen=True)
class ParsedDocument:
    content: str
    segments: tuple[ParsedSegment, ...]


def parse_uploaded_document(filename: str, raw_content: bytes) -> str:
    """Compatibility helper returning only the extracted document text."""

    return parse_uploaded_document_structured(filename, raw_content).content


def parse_uploaded_document_structured(filename: str, raw_content: bytes) -> ParsedDocument:
    extension = Path(filename).suffix.lower()

    if extension not in SUPPORTED_UPLOAD_EXTENSIONS:
        raise UnsupportedDocumentTypeError(
            "Supported uploads are TXT, Markdown, PDF, DOCX, PPTX, XLSX and "
            "optional-OCR PNG/JPG/TIFF images."
        )

    if extension == ".pdf":
        return _extract_pdf_document(raw_content)
    if extension == ".docx":
        from sialabs_local_rag.office_parsing import parse_docx_document

        return parse_docx_document(raw_content)
    if extension == ".pptx":
        from sialabs_local_rag.office_parsing import parse_pptx_document

        return parse_pptx_document(raw_content)
    if extension == ".xlsx":
        from sialabs_local_rag.office_parsing import parse_xlsx_document

        return parse_xlsx_document(raw_content)
    if extension in _IMAGE_OCR_EXTENSIONS:
        from sialabs_local_rag.ocr import ocr_image_document

        return ocr_image_document(raw_content, filename)

    content = _decode_utf8_text(raw_content)
    if extension in {".md", ".markdown"}:
        return parse_markdown_document(content)
    return parse_plain_text_document(content)


def parse_plain_text_document(content: str) -> ParsedDocument:
    cleaned = content.strip()
    if not cleaned:
        raise DocumentParsingError("Uploaded document did not contain text.")
    return ParsedDocument(
        content=cleaned,
        segments=(ParsedSegment(content=cleaned),),
    )


def parse_markdown_document(content: str) -> ParsedDocument:
    cleaned = content.strip()
    if not cleaned:
        raise DocumentParsingError("Uploaded document did not contain text.")

    segments: list[ParsedSegment] = []
    current_heading: str | None = None
    current_lines: list[str] = []

    def flush_section() -> None:
        nonlocal current_lines
        body = "\n".join(current_lines).strip()
        if body or current_heading:
            segment_content = body or current_heading or ""
            segments.append(
                ParsedSegment(
                    content=segment_content,
                    section_title=current_heading,
                    source_locator=(
                        f"section:{current_heading}" if current_heading else None
                    ),
                )
            )
        current_lines = []

    for line in cleaned.splitlines():
        match = _MARKDOWN_HEADING_RE.match(line.strip())
        if match:
            flush_section()
            current_heading = match.group(2).strip()
            continue
        current_lines.append(line)

    flush_section()
    if not segments:
        segments.append(ParsedSegment(content=cleaned))

    return ParsedDocument(content=cleaned, segments=tuple(segments))


def _decode_utf8_text(raw_content: bytes) -> str:
    try:
        content = raw_content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DocumentParsingError("Uploaded file must be UTF-8 encoded.") from exc

    if not content.strip():
        raise DocumentParsingError("Uploaded document did not contain text.")

    return content


def _extract_pdf_document(raw_content: bytes) -> ParsedDocument:
    try:
        reader = PdfReader(BytesIO(raw_content))
        if len(reader.pages) > _MAX_TEXT_PDF_PAGES:
            raise DocumentParsingError(
                f"PDF exceeds the local limit of {_MAX_TEXT_PDF_PAGES} pages."
            )

        segments: list[ParsedSegment] = []
        for page_number, page in enumerate(reader.pages, start=1):
            page_text = (page.extract_text() or "").strip()
            if not page_text:
                continue
            segments.append(
                ParsedSegment(
                    content=page_text,
                    page_number=page_number,
                    source_locator=f"page:{page_number}",
                )
            )
    except DocumentParsingError:
        raise
    except Exception as exc:
        raise DocumentParsingError(
            "PDF could not be read. Password-protected or damaged PDFs are not supported."
        ) from exc

    if not segments:
        from sialabs_local_rag.ocr import ocr_pdf_document

        return ocr_pdf_document(raw_content)

    content = "\n\n".join(segment.content for segment in segments)
    return ParsedDocument(content=content, segments=tuple(segments))
