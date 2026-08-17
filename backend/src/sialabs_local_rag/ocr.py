from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from io import BytesIO
from typing import Any

from sialabs_local_rag.parsing import (
    DocumentParsingError,
    ParsedDocument,
    ParsedSegment,
)

_MAX_OCR_PDF_PAGES = 50
_OCR_SCALE = 2.0


class OcrUnavailableError(RuntimeError):
    """Raised when optional local OCR dependencies/runtime are unavailable."""


@dataclass(frozen=True)
class OcrRuntime:
    image_module: Any
    pytesseract: Any
    fitz: Any | None = None


def ocr_image_document(raw_content: bytes, filename: str) -> ParsedDocument:
    runtime = _load_ocr_runtime(require_pdf=False)
    try:
        image = runtime.image_module.open(BytesIO(raw_content))
        text = str(runtime.pytesseract.image_to_string(image)).strip()
        close = getattr(image, "close", None)
        if callable(close):
            close()
    except Exception as exc:
        raise DocumentParsingError(
            "Image OCR failed. Verify that the image is readable and Tesseract supports its language."
        ) from exc

    if not text:
        raise DocumentParsingError("Local OCR completed but did not detect text in the image.")
    return ParsedDocument(
        content=text,
        segments=(
            ParsedSegment(
                content=text,
                source_locator=f"image:{filename}",
            ),
        ),
    )


def ocr_pdf_document(raw_content: bytes) -> ParsedDocument:
    runtime = _load_ocr_runtime(require_pdf=True)
    assert runtime.fitz is not None

    try:
        document = runtime.fitz.open(stream=raw_content, filetype="pdf")
    except Exception as exc:
        raise DocumentParsingError("Scanned PDF could not be opened for local OCR.") from exc

    page_count = int(document.page_count)
    if page_count > _MAX_OCR_PDF_PAGES:
        document.close()
        raise DocumentParsingError(
            f"Scanned PDF exceeds the local OCR limit of {_MAX_OCR_PDF_PAGES} pages."
        )

    segments: list[ParsedSegment] = []
    try:
        matrix = runtime.fitz.Matrix(_OCR_SCALE, _OCR_SCALE)
        for page_index in range(page_count):
            page = document.load_page(page_index)
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            image = runtime.image_module.open(BytesIO(pixmap.tobytes("png")))
            text = str(runtime.pytesseract.image_to_string(image)).strip()
            close = getattr(image, "close", None)
            if callable(close):
                close()
            if not text:
                continue
            page_number = page_index + 1
            segments.append(
                ParsedSegment(
                    content=text,
                    page_number=page_number,
                    source_locator=f"page:{page_number}",
                )
            )
    except Exception as exc:
        raise DocumentParsingError(
            "Scanned PDF OCR failed while rendering or recognizing a page."
        ) from exc
    finally:
        document.close()

    if not segments:
        raise DocumentParsingError("Local OCR completed but did not detect text in the PDF.")
    return ParsedDocument(
        content="\n\n".join(segment.content for segment in segments),
        segments=tuple(segments),
    )


def _load_ocr_runtime(require_pdf: bool) -> OcrRuntime:
    try:
        image_module = import_module("PIL.Image")
        pytesseract = import_module("pytesseract")
        fitz = import_module("fitz") if require_pdf else None
    except ModuleNotFoundError as exc:
        raise OcrUnavailableError(
            "Local OCR is optional and is not installed. From backend/, run "
            "`uv sync --extra ocr`, install the local Tesseract OCR executable, "
            "then restart the backend."
        ) from exc

    try:
        pytesseract.get_tesseract_version()
    except Exception as exc:
        raise OcrUnavailableError(
            "Python OCR packages are installed, but the local Tesseract executable "
            "is unavailable. Install Tesseract OCR and ensure it is on PATH."
        ) from exc

    return OcrRuntime(
        image_module=image_module,
        pytesseract=pytesseract,
        fitz=fitz,
    )
