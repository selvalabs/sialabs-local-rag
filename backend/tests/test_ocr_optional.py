from __future__ import annotations

from io import BytesIO
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import sialabs_local_rag.ocr as ocr_module
import sialabs_local_rag.parsing as parsing_module
from sialabs_local_rag.ocr import OcrRuntime, OcrUnavailableError
from sialabs_local_rag.parsing import ParsedDocument, ParsedSegment


class _FakeImage:
    def close(self) -> None:
        return None


class _FakeImageModule:
    @staticmethod
    def open(_: BytesIO) -> _FakeImage:
        return _FakeImage()


class _FakeTesseract:
    @staticmethod
    def image_to_string(_: object) -> str:
        return "OCR-IMAGE-42 recognized locally"


class _FakePixmap:
    @staticmethod
    def tobytes(_: str) -> bytes:
        return b"fake-png"


class _FakePage:
    @staticmethod
    def get_pixmap(**_: object) -> _FakePixmap:
        return _FakePixmap()


class _FakePdfDocument:
    page_count = 2

    @staticmethod
    def load_page(_: int) -> _FakePage:
        return _FakePage()

    @staticmethod
    def close() -> None:
        return None


class _FakeFitz:
    @staticmethod
    def open(**_: object) -> _FakePdfDocument:
        return _FakePdfDocument()

    @staticmethod
    def Matrix(_: float, __: float) -> tuple[float, float]:
        return (2.0, 2.0)


def test_missing_ocr_packages_have_actionable_install_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_import(name: str) -> object:
        if name == "PIL.Image":
            raise ModuleNotFoundError("PIL")
        return SimpleNamespace()

    monkeypatch.setattr(ocr_module, "import_module", fake_import)

    with pytest.raises(OcrUnavailableError, match="requirements-ocr.txt"):
        ocr_module.ocr_image_document(b"fake-image", "scan.png")


def test_missing_ocr_capability_is_actionable_through_api(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unavailable(**_: object) -> OcrRuntime:
        raise OcrUnavailableError(
            "Local OCR is optional. Run `uv pip install -r requirements-ocr.txt`."
        )

    monkeypatch.setattr(ocr_module, "_load_ocr_runtime", unavailable)

    response = client.post(
        "/api/documents/upload",
        files={"file": ("scan.png", b"fake-image", "image/png")},
    )

    assert response.status_code == 503
    assert "requirements-ocr.txt" in response.json()["detail"]


def test_image_ocr_returns_image_locator(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = OcrRuntime(
        image_module=_FakeImageModule(),
        pytesseract=_FakeTesseract(),
    )
    monkeypatch.setattr(ocr_module, "_load_ocr_runtime", lambda **_: runtime)

    document = ocr_module.ocr_image_document(b"fake-image", "receipt.png")

    assert document.content == "OCR-IMAGE-42 recognized locally"
    assert document.segments[0].source_locator == "image:receipt.png"


def test_scanned_pdf_ocr_preserves_page_numbers(monkeypatch: pytest.MonkeyPatch) -> None:
    class _PageAwareTesseract:
        calls = 0

        @classmethod
        def image_to_string(cls, _: object) -> str:
            cls.calls += 1
            return f"OCR-PAGE-{cls.calls}"

    runtime = OcrRuntime(
        image_module=_FakeImageModule(),
        pytesseract=_PageAwareTesseract(),
        fitz=_FakeFitz(),
    )
    monkeypatch.setattr(ocr_module, "_load_ocr_runtime", lambda **_: runtime)

    document = ocr_module.ocr_pdf_document(b"fake-pdf")

    assert [segment.page_number for segment in document.segments] == [1, 2]
    assert [segment.source_locator for segment in document.segments] == [
        "page:1",
        "page:2",
    ]
    assert document.segments[1].content == "OCR-PAGE-2"


def test_textless_valid_pdf_routes_to_optional_ocr(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _TextlessPage:
        @staticmethod
        def extract_text() -> str:
            return ""

    class _TextlessReader:
        pages = [_TextlessPage()]

        def __init__(self, _: object) -> None:
            return None

    expected = ParsedDocument(
        content="OCR fallback text",
        segments=(
            ParsedSegment(
                content="OCR fallback text",
                page_number=1,
                source_locator="page:1",
            ),
        ),
    )
    monkeypatch.setattr(parsing_module, "PdfReader", _TextlessReader)
    monkeypatch.setattr(ocr_module, "ocr_pdf_document", lambda _: expected)

    parsed = parsing_module.parse_uploaded_document_structured("scan.pdf", b"fake")

    assert parsed == expected
