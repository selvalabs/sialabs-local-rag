from __future__ import annotations

from io import BytesIO
from pathlib import Path

from pypdf import PdfReader

SUPPORTED_UPLOAD_EXTENSIONS = {".txt", ".md", ".markdown", ".pdf"}


class UnsupportedDocumentTypeError(ValueError):
    """Raised when the uploaded file extension is not supported."""


class DocumentParsingError(ValueError):
    """Raised when a supported file cannot be parsed into usable text."""


def parse_uploaded_document(filename: str, raw_content: bytes) -> str:
    extension = Path(filename).suffix.lower()

    if extension not in SUPPORTED_UPLOAD_EXTENSIONS:
        raise UnsupportedDocumentTypeError(
            "Only .txt, .md, .markdown and .pdf uploads are supported in this MVP."
        )

    if extension == ".pdf":
        return _extract_pdf_text(raw_content)

    return _decode_utf8_text(raw_content)


def _decode_utf8_text(raw_content: bytes) -> str:
    try:
        content = raw_content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DocumentParsingError("Uploaded file must be UTF-8 encoded.") from exc

    if not content.strip():
        raise DocumentParsingError("Uploaded document did not contain text.")

    return content


def _extract_pdf_text(raw_content: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(raw_content))
        text_parts: list[str] = []

        for page in reader.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                text_parts.append(page_text.strip())

    except Exception as exc:
        raise DocumentParsingError(
            "PDF could not be read. Password-protected or damaged PDFs are not supported."
        ) from exc

    content = "\n\n".join(text_parts).strip()

    if not content:
        raise DocumentParsingError(
            "PDF did not contain extractable text. OCR for scanned PDFs is out of scope "
            "for this MVP."
        )

    return content