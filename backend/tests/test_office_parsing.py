from __future__ import annotations

from io import BytesIO
from zipfile import ZipFile

from sialabs_local_rag.office_parsing import (
    parse_docx_document,
    parse_pptx_document,
    parse_xlsx_document,
)

_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
_P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
_S_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


def build_docx_fixture() -> bytes:
    document_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="{_W_NS}">
  <w:body>
    <w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>Safety</w:t></w:r></w:p>
    <w:p><w:r><w:t>Use protective equipment during inspection.</w:t></w:r></w:p>
    <w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>Recovery</w:t></w:r></w:p>
    <w:p><w:r><w:t>Use exact recovery code DOCX-77 before restart.</w:t></w:r></w:p>
  </w:body>
</w:document>"""
    return _zip_bytes({"word/document.xml": document_xml})


def build_pptx_fixture() -> bytes:
    first_slide = _slide_xml("Overview", "PPTX-ONE general introduction")
    second_slide = _slide_xml("Recovery", "Use exact slide code PPTX-88 for recovery")
    return _zip_bytes(
        {
            "ppt/slides/slide1.xml": first_slide,
            "ppt/slides/slide2.xml": second_slide,
        }
    )


def build_xlsx_fixture() -> bytes:
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


def test_docx_preserves_heading_sections() -> None:
    document = parse_docx_document(build_docx_fixture())

    assert [segment.section_title for segment in document.segments] == [
        "Safety",
        "Recovery",
    ]
    assert document.segments[1].source_locator == "section:Recovery"
    assert "DOCX-77" in document.segments[1].content


def test_pptx_preserves_slide_numbers_and_titles() -> None:
    document = parse_pptx_document(build_pptx_fixture())

    assert [segment.slide_number for segment in document.segments] == [1, 2]
    assert document.segments[1].section_title == "Recovery"
    assert document.segments[1].source_locator == "slide:2"
    assert "PPTX-88" in document.segments[1].content


def test_xlsx_preserves_sheet_and_range_metadata() -> None:
    document = parse_xlsx_document(build_xlsx_fixture())

    assert len(document.segments) == 1
    segment = document.segments[0]
    assert segment.sheet_name == "Finance"
    assert segment.cell_range == "A1:B2"
    assert segment.source_locator == "sheet:Finance!A1:B2"
    assert "A2=XLSX-99" in segment.content
    assert "B2=10 percent" in segment.content


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
