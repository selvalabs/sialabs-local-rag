from __future__ import annotations

from io import BytesIO
from zipfile import ZipFile

from fastapi.testclient import TestClient

_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
_P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
_S_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


def test_docx_upload_returns_heading_source_metadata(client: TestClient) -> None:
    upload = client.post(
        "/api/documents/upload",
        files={
            "file": (
                "manual.docx",
                _docx_fixture(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert upload.status_code == 201

    response = client.post(
        "/api/chat",
        json={"question": "Where is DOCX-77 documented?", "top_k": 3},
    )
    assert response.status_code == 200
    sources = response.json()["sources"]
    matching = [source for source in sources if "DOCX-77" in source["content"]]

    assert matching
    assert matching[0]["section_title"] == "Recovery"
    assert matching[0]["source_locator"] == "section:Recovery"


def test_pptx_upload_returns_slide_source_metadata(client: TestClient) -> None:
    upload = client.post(
        "/api/documents/upload",
        files={
            "file": (
                "deck.pptx",
                _pptx_fixture(),
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            )
        },
    )
    assert upload.status_code == 201

    response = client.post(
        "/api/chat",
        json={"question": "Which slide contains PPTX-88?", "top_k": 3},
    )
    assert response.status_code == 200
    matching = [
        source
        for source in response.json()["sources"]
        if "PPTX-88" in source["content"]
    ]

    assert matching
    assert matching[0]["slide_number"] == 2
    assert matching[0]["section_title"] == "Recovery"
    assert matching[0]["source_locator"] == "slide:2"


def test_xlsx_upload_returns_sheet_and_range_metadata(client: TestClient) -> None:
    upload = client.post(
        "/api/documents/upload",
        files={
            "file": (
                "finance.xlsx",
                _xlsx_fixture(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert upload.status_code == 201

    response = client.post(
        "/api/chat",
        json={"question": "What reserve is associated with XLSX-99?", "top_k": 3},
    )
    assert response.status_code == 200
    matching = [
        source
        for source in response.json()["sources"]
        if "XLSX-99" in source["content"]
    ]

    assert matching
    assert matching[0]["sheet_name"] == "Finance"
    assert matching[0]["cell_range"] == "A1:B2"
    assert matching[0]["source_locator"] == "sheet:Finance!A1:B2"


def _docx_fixture() -> bytes:
    document_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="{_W_NS}">
  <w:body>
    <w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>Overview</w:t></w:r></w:p>
    <w:p><w:r><w:t>General document introduction.</w:t></w:r></w:p>
    <w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>Recovery</w:t></w:r></w:p>
    <w:p><w:r><w:t>Use exact recovery code DOCX-77 before restart.</w:t></w:r></w:p>
  </w:body>
</w:document>"""
    return _zip_bytes({"word/document.xml": document_xml})


def _pptx_fixture() -> bytes:
    return _zip_bytes(
        {
            "ppt/slides/slide1.xml": _slide_xml("Overview", "PPTX-ONE introduction"),
            "ppt/slides/slide2.xml": _slide_xml(
                "Recovery",
                "Use exact code PPTX-88 during recovery",
            ),
        }
    )


def _xlsx_fixture() -> bytes:
    workbook = f"""<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="{_S_NS}" xmlns:r="{_R_NS}">
  <sheets><sheet name="Finance" sheetId="1" r:id="rId1"/></sheets>
</workbook>"""
    relationships = f"""<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="{_REL_NS}">
  <Relationship Id="rId1" Target="worksheets/sheet1.xml"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"/>
</Relationships>"""
    worksheet = f"""<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="{_S_NS}">
  <sheetData>
    <row r="1">
      <c r="A1" t="inlineStr"><is><t>Code</t></is></c>
      <c r="B1" t="inlineStr"><is><t>Reserve</t></is></c>
    </row>
    <row r="2">
      <c r="A2" t="inlineStr"><is><t>XLSX-99</t></is></c>
      <c r="B2" t="inlineStr"><is><t>10 percent</t></is></c>
    </row>
  </sheetData>
</worksheet>"""
    return _zip_bytes(
        {
            "xl/workbook.xml": workbook,
            "xl/_rels/workbook.xml.rels": relationships,
            "xl/worksheets/sheet1.xml": worksheet,
        }
    )


def _slide_xml(title: str, body: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<p:sld xmlns:p="{_P_NS}" xmlns:a="{_A_NS}">
  <p:cSld><p:spTree>
    <p:sp>
      <p:nvSpPr><p:nvPr><p:ph type="title"/></p:nvPr></p:nvSpPr>
      <p:txBody><a:p><a:r><a:t>{title}</a:t></a:r></a:p></p:txBody>
    </p:sp>
    <p:sp>
      <p:nvSpPr><p:nvPr/></p:nvSpPr>
      <p:txBody><a:p><a:r><a:t>{body}</a:t></a:r></a:p></p:txBody>
    </p:sp>
  </p:spTree></p:cSld>
</p:sld>"""


def _zip_bytes(files: dict[str, str]) -> bytes:
    output = BytesIO()
    with ZipFile(output, "w") as archive:
        for path, content in files.items():
            archive.writestr(path, content)
    return output.getvalue()
