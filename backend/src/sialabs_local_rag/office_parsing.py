from __future__ import annotations

import re
from io import BytesIO
from pathlib import PurePosixPath
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

from sialabs_local_rag.parsing import (
    DocumentParsingError,
    ParsedDocument,
    ParsedSegment,
)

_MAX_PACKAGE_ENTRIES = 5_000
_MAX_UNCOMPRESSED_BYTES = 50_000_000
_MAX_DOCX_PARAGRAPHS = 20_000
_MAX_PPTX_SLIDES = 200
_MAX_XLSX_SHEETS = 100
_MAX_XLSX_CELLS = 50_000
_MAX_XLSX_ROWS_PER_SEGMENT = 25

_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
_P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
_S_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"

_W = {"w": _W_NS}
_P = {"p": _P_NS, "a": _A_NS, "r": _R_NS}
_S = {"s": _S_NS, "r": _R_NS}
_SLIDE_NUMBER_RE = re.compile(r"slide(\d+)\.xml$")


def parse_docx_document(raw_content: bytes) -> ParsedDocument:
    with _open_ooxml_package(raw_content, "DOCX") as archive:
        root = _read_xml(archive, "word/document.xml", "DOCX")
        styles = _read_word_style_names(archive)
        paragraphs = root.findall(".//w:body/w:p", _W)
        if len(paragraphs) > _MAX_DOCX_PARAGRAPHS:
            raise DocumentParsingError(
                f"DOCX exceeds the local limit of {_MAX_DOCX_PARAGRAPHS} paragraphs."
            )

        segments: list[ParsedSegment] = []
        all_paragraphs: list[str] = []
        current_heading: str | None = None
        current_body: list[str] = []
        current_start = 1
        last_paragraph_number = 0

        def flush(end_paragraph: int) -> None:
            nonlocal current_body, current_start
            body = "\n\n".join(current_body).strip()
            if not body and not current_heading:
                current_body = []
                return
            content = body or current_heading or ""
            if current_heading:
                locator = f"section:{current_heading}"
            else:
                locator = f"paragraphs:{current_start}-{max(current_start, end_paragraph)}"
            segments.append(
                ParsedSegment(
                    content=content,
                    section_title=current_heading,
                    source_locator=locator,
                )
            )
            current_body = []

        for paragraph_number, paragraph in enumerate(paragraphs, start=1):
            text = _word_paragraph_text(paragraph).strip()
            if not text:
                continue
            last_paragraph_number = paragraph_number
            all_paragraphs.append(text)
            heading = _word_heading_title(paragraph, text, styles)
            if heading is not None:
                flush(paragraph_number - 1)
                current_heading = heading
                current_start = paragraph_number
                continue
            if not current_body:
                current_start = paragraph_number if current_heading is None else current_start
            current_body.append(text)

        flush(last_paragraph_number)

    if not all_paragraphs:
        raise DocumentParsingError("DOCX did not contain extractable text.")
    return ParsedDocument(
        content="\n\n".join(all_paragraphs),
        segments=tuple(segments or [ParsedSegment(content="\n\n".join(all_paragraphs))]),
    )


def parse_pptx_document(raw_content: bytes) -> ParsedDocument:
    with _open_ooxml_package(raw_content, "PPTX") as archive:
        slide_paths = _pptx_slide_paths(archive)
        if len(slide_paths) > _MAX_PPTX_SLIDES:
            raise DocumentParsingError(
                f"PPTX exceeds the local limit of {_MAX_PPTX_SLIDES} slides."
            )

        segments: list[ParsedSegment] = []
        full_text: list[str] = []
        for slide_number, path in enumerate(slide_paths, start=1):
            root = _read_xml(archive, path, "PPTX")
            title = _pptx_slide_title(root)
            texts = [
                (node.text or "").strip()
                for node in root.findall(".//a:t", _P)
                if (node.text or "").strip()
            ]
            if not texts:
                continue
            content = "\n".join(texts)
            full_text.append(f"Slide {slide_number}\n{content}")
            segments.append(
                ParsedSegment(
                    content=content,
                    slide_number=slide_number,
                    section_title=title,
                    source_locator=f"slide:{slide_number}",
                )
            )

    if not segments:
        raise DocumentParsingError("PPTX did not contain extractable text.")
    return ParsedDocument(content="\n\n".join(full_text), segments=tuple(segments))


def parse_xlsx_document(raw_content: bytes) -> ParsedDocument:
    with _open_ooxml_package(raw_content, "XLSX") as archive:
        workbook = _read_xml(archive, "xl/workbook.xml", "XLSX")
        relationships = _relationship_targets(
            archive,
            "xl/_rels/workbook.xml.rels",
            base_dir="xl",
        )
        shared_strings = _xlsx_shared_strings(archive)
        sheet_nodes = workbook.findall(".//s:sheets/s:sheet", _S)
        if len(sheet_nodes) > _MAX_XLSX_SHEETS:
            raise DocumentParsingError(
                f"XLSX exceeds the local limit of {_MAX_XLSX_SHEETS} sheets."
            )

        total_cells = 0
        segments: list[ParsedSegment] = []
        full_text: list[str] = []

        for sheet in sheet_nodes:
            sheet_name = sheet.attrib.get("name", "Sheet")
            relationship_id = sheet.attrib.get(f"{{{_R_NS}}}id")
            if not relationship_id or relationship_id not in relationships:
                continue
            sheet_root = _read_xml(archive, relationships[relationship_id], "XLSX")
            rows: list[tuple[int, list[tuple[str, str]]]] = []

            for row in sheet_root.findall(".//s:sheetData/s:row", _S):
                row_number = int(row.attrib.get("r", len(rows) + 1))
                cells: list[tuple[str, str]] = []
                for cell in row.findall("s:c", _S):
                    value = _xlsx_cell_value(cell, shared_strings)
                    if value == "":
                        continue
                    total_cells += 1
                    if total_cells > _MAX_XLSX_CELLS:
                        raise DocumentParsingError(
                            f"XLSX exceeds the local limit of {_MAX_XLSX_CELLS} non-empty cells."
                        )
                    reference = cell.attrib.get("r", f"R{row_number}")
                    cells.append((reference, value))
                if cells:
                    rows.append((row_number, cells))

            for start in range(0, len(rows), _MAX_XLSX_ROWS_PER_SEGMENT):
                block = rows[start : start + _MAX_XLSX_ROWS_PER_SEGMENT]
                if not block:
                    continue
                first_ref = block[0][1][0][0]
                last_ref = block[-1][1][-1][0]
                cell_range = first_ref if first_ref == last_ref else f"{first_ref}:{last_ref}"
                lines = [
                    f"Row {row_number}: "
                    + " | ".join(f"{reference}={value}" for reference, value in cells)
                    for row_number, cells in block
                ]
                content = "\n".join(lines)
                locator = f"sheet:{sheet_name}!{cell_range}"
                segments.append(
                    ParsedSegment(
                        content=content,
                        sheet_name=sheet_name,
                        cell_range=cell_range,
                        source_locator=locator,
                    )
                )
                full_text.append(f"Sheet {sheet_name} · {cell_range}\n{content}")

    if not segments:
        raise DocumentParsingError("XLSX did not contain extractable non-empty cells.")
    return ParsedDocument(content="\n\n".join(full_text), segments=tuple(segments))


def _open_ooxml_package(raw_content: bytes, label: str) -> ZipFile:
    try:
        archive = ZipFile(BytesIO(raw_content))
    except BadZipFile as exc:
        raise DocumentParsingError(f"{label} is not a valid OOXML package.") from exc

    infos = archive.infolist()
    if len(infos) > _MAX_PACKAGE_ENTRIES:
        archive.close()
        raise DocumentParsingError(
            f"{label} exceeds the local package-entry limit of {_MAX_PACKAGE_ENTRIES}."
        )
    if sum(info.file_size for info in infos) > _MAX_UNCOMPRESSED_BYTES:
        archive.close()
        raise DocumentParsingError(
            f"{label} expands beyond the {_MAX_UNCOMPRESSED_BYTES // 1_000_000} MB local limit."
        )
    return archive


def _read_xml(archive: ZipFile, path: str, label: str) -> ElementTree.Element:
    try:
        data = archive.read(path)
    except KeyError as exc:
        raise DocumentParsingError(f"{label} is missing required part {path}.") from exc
    try:
        return ElementTree.fromstring(data)
    except ElementTree.ParseError as exc:
        raise DocumentParsingError(f"{label} contains invalid XML in {path}.") from exc


def _word_paragraph_text(paragraph: ElementTree.Element) -> str:
    parts: list[str] = []
    for node in paragraph.iter():
        if node.tag == f"{{{_W_NS}}}t":
            parts.append(node.text or "")
        elif node.tag == f"{{{_W_NS}}}tab":
            parts.append("\t")
        elif node.tag in {f"{{{_W_NS}}}br", f"{{{_W_NS}}}cr"}:
            parts.append("\n")
    return "".join(parts)


def _read_word_style_names(archive: ZipFile) -> dict[str, str]:
    try:
        root = ElementTree.fromstring(archive.read("word/styles.xml"))
    except (KeyError, ElementTree.ParseError):
        return {}

    result: dict[str, str] = {}
    for style in root.findall("w:style", _W):
        style_id = style.attrib.get(f"{{{_W_NS}}}styleId")
        name = style.find("w:name", _W)
        if style_id and name is not None:
            result[style_id] = name.attrib.get(f"{{{_W_NS}}}val", style_id)
    return result


def _word_heading_title(
    paragraph: ElementTree.Element,
    text: str,
    style_names: dict[str, str],
) -> str | None:
    style = paragraph.find("w:pPr/w:pStyle", _W)
    if style is None:
        return None
    style_id = style.attrib.get(f"{{{_W_NS}}}val", "")
    style_name = style_names.get(style_id, style_id)
    if style_id.casefold().startswith("heading") or style_name.casefold().startswith("heading"):
        return text
    return None


def _pptx_slide_paths(archive: ZipFile) -> list[str]:
    try:
        presentation = ElementTree.fromstring(archive.read("ppt/presentation.xml"))
        relationships = _relationship_targets(
            archive,
            "ppt/_rels/presentation.xml.rels",
            base_dir="ppt",
        )
        ordered: list[str] = []
        for slide_id in presentation.findall(".//p:sldIdLst/p:sldId", _P):
            relationship_id = slide_id.attrib.get(f"{{{_R_NS}}}id")
            if relationship_id and relationship_id in relationships:
                ordered.append(relationships[relationship_id])
        if ordered:
            return ordered
    except (KeyError, ElementTree.ParseError, DocumentParsingError):
        pass

    paths = [
        name
        for name in archive.namelist()
        if name.startswith("ppt/slides/slide") and name.endswith(".xml")
    ]
    return sorted(paths, key=_pptx_slide_sort_key)


def _pptx_slide_sort_key(path: str) -> tuple[int, str]:
    match = _SLIDE_NUMBER_RE.search(path)
    return (int(match.group(1)) if match else 1_000_000, path)


def _pptx_slide_title(root: ElementTree.Element) -> str | None:
    for shape in root.findall(".//p:sp", _P):
        placeholder = shape.find("p:nvSpPr/p:nvPr/p:ph", _P)
        if placeholder is None:
            continue
        placeholder_type = placeholder.attrib.get("type", "")
        if placeholder_type not in {"title", "ctrTitle"}:
            continue
        texts = [
            (node.text or "").strip()
            for node in shape.findall(".//a:t", _P)
            if (node.text or "").strip()
        ]
        if texts:
            return " ".join(texts)
    return None


def _relationship_targets(
    archive: ZipFile,
    rels_path: str,
    base_dir: str,
) -> dict[str, str]:
    root = _read_xml(archive, rels_path, "OOXML")
    result: dict[str, str] = {}
    for relationship in root.findall(f"{{{_REL_NS}}}Relationship"):
        relationship_id = relationship.attrib.get("Id")
        target = relationship.attrib.get("Target")
        if relationship_id and target:
            result[relationship_id] = _resolve_package_target(base_dir, target)
    return result


def _resolve_package_target(base_dir: str, target: str) -> str:
    if target.startswith("/"):
        return target.lstrip("/")
    parts: list[str] = []
    for part in (PurePosixPath(base_dir) / target).parts:
        if part in {"", "."}:
            continue
        if part == "..":
            if parts:
                parts.pop()
            continue
        parts.append(part)
    return "/".join(parts)


def _xlsx_shared_strings(archive: ZipFile) -> list[str]:
    try:
        root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
    except (KeyError, ElementTree.ParseError):
        return []
    return [
        "".join((node.text or "") for node in item.findall(".//s:t", _S))
        for item in root.findall("s:si", _S)
    ]


def _xlsx_cell_value(cell: ElementTree.Element, shared_strings: list[str]) -> str:
    cell_type = cell.attrib.get("t", "")
    if cell_type == "inlineStr":
        return "".join((node.text or "") for node in cell.findall(".//s:t", _S)).strip()

    value_node = cell.find("s:v", _S)
    if value_node is None or value_node.text is None:
        return ""
    raw_value = value_node.text.strip()

    if cell_type == "s":
        try:
            index = int(raw_value)
        except ValueError:
            return raw_value
        if 0 <= index < len(shared_strings):
            return shared_strings[index]
        return raw_value
    if cell_type == "b":
        return "TRUE" if raw_value == "1" else "FALSE"
    return raw_value
