# API

Interactive OpenAPI documentation is available at `http://localhost:8000/docs` while the backend is running.

## Endpoints

### `GET /health`

Checks API availability.

### `GET /api/config`

Returns non-sensitive runtime configuration such as provider/model, retrieval and
chunking settings. Secrets and private environment values are not returned.

### `GET /api/index/status`

Reports whether the persisted embedding index is compatible with the currently
configured embedding provider/model. Possible states are `empty`, `ready`,
`legacy` and `incompatible`.

### `DELETE /api/index`

Deletes indexed documents/chunks, embedding signature and persisted chat traces so
the collection can be re-ingested with another embedding configuration.

### `DELETE /api/chat/history`

Deletes persisted backend chat traces. New records keep lightweight source
metadata but do not copy retrieved chunk text into `metadata_json`.

### `DELETE /api/local-data`

Performs a destructive reset of documents, chunks, embedding signature and backend
chat traces. Normal runtime requires a loopback request and:

```text
X-Confirm-Local-Data-Reset: delete-all
```

### `POST /api/documents`

Creates a document from pasted plain text. Paragraph boundaries are preserved by
the structure-aware chunker.

### `POST /api/documents/upload`

Uploads and indexes local files up to **10 MB**. Supported extensions:

- `.txt`
- `.md`, `.markdown`
- `.pdf`
- `.docx`
- `.pptx`
- `.xlsx`
- `.png`, `.jpg`, `.jpeg`, `.tif`, `.tiff` when optional local OCR is installed

The ingestion pipeline keeps useful source structure instead of flattening every
format into one anonymous text stream.

#### Markdown

Markdown headings define section boundaries. Sources may include:

```json
{
  "section_title": "Recovery",
  "source_locator": "section:Recovery"
}
```

#### PDF

Selectable-text PDFs keep 1-based page boundaries. Sources may include:

```json
{
  "page_number": 2,
  "source_locator": "page:2"
}
```

Text PDFs are limited to 100 pages per upload. A valid PDF with no extractable text
falls back to the optional local OCR capability.

#### DOCX

DOCX is parsed directly from OOXML using the Python standard library. Heading-style
paragraphs become section boundaries; ordinary paragraphs remain grouped under
the current heading. No `python-docx` dependency is required.

#### PPTX

PPTX is parsed slide by slide. Sources can include:

```json
{
  "slide_number": 2,
  "section_title": "Recovery",
  "source_locator": "slide:2"
}
```

The parser preserves slide order and uses title placeholders when available.

#### XLSX

XLSX is represented as bounded row/cell blocks rather than blindly concatenating
the entire workbook. Sources can include:

```json
{
  "sheet_name": "Finance",
  "cell_range": "A1:B25",
  "source_locator": "sheet:Finance!A1:B25"
}
```

Cell values remain associated with their references in chunk text, for example
`A2=XLSX-99 | B2=10 percent`.

#### Optional local OCR

OCR is deliberately not part of the base installation or ordinary CI. From
`backend/`, install the optional Python packages with:

```powershell
uv pip install -r requirements-ocr.txt
```

Then install the **local Tesseract OCR executable** and ensure it is available on
`PATH`.

OCR supports image uploads and textless/scanned PDFs. Scanned-PDF OCR is limited to
50 pages and preserves page locators. If OCR packages or Tesseract are unavailable,
the upload returns `503` with an actionable setup message instead of silently using
a cloud service.

#### Office/package safety limits

OOXML parsers reject packages that exceed local safety bounds, including:

- 5,000 ZIP package entries;
- 50 MB total uncompressed OOXML content;
- 20,000 DOCX paragraphs;
- 200 PPTX slides;
- 100 XLSX sheets;
- 50,000 non-empty XLSX cells.

These limits complement the 10 MB HTTP upload limit and reduce local resource risk
from compressed document packages.

### `GET /api/documents`

Lists indexed documents.

### `DELETE /api/documents/{document_id}`

Deletes a document and its chunks and clears persisted backend chat history because
previous generated answers may derive from the deleted source.

### `POST /api/chat`

Queries the local document collection. The request separates the current
`question` from optional `conversation_context`; the response includes the backend
`retrieval_query` used for embedding/search.

A retrieved source may expose any applicable structured location fields:

```json
{
  "document_title": "Quarterly Finance.xlsx",
  "chunk_index": 3,
  "page_number": null,
  "section_title": null,
  "slide_number": null,
  "sheet_name": "Finance",
  "cell_range": "A1:B25",
  "source_locator": "sheet:Finance!A1:B25",
  "score": 0.0324,
  "content": "Sheet: Finance · Range A1:B25\n\n..."
}
```

Fields remain `null` when they do not apply or when legacy chunks predate the
metadata migration.

Conversation history is dialogue context, not factual evidence. Assistant-history
text is never copied into the embedding query, and factual answer claims must be
grounded in retrieved sources.

## Embedding compatibility and reindexing

Adding source metadata in schema versions 5 and 6 does **not** require an embedding
reindex. Existing chunks remain valid with nullable location fields. Re-ingestion is
only needed when historical documents should gain newly extractable page/section/
slide/sheet metadata.

## Expected errors

| Status | Case |
| --- | --- |
| 400 | Full local-data reset confirmation header is missing or invalid |
| 403 | Full local-data reset is requested from a non-loopback client |
| 409 | Duplicate document or incompatible/legacy embedding index |
| 413 | Upload exceeds the 10 MB local limit |
| 415 | Unsupported file extension |
| 422 | Supported file is malformed, unreadable or contains no usable text |
| 503 | Ollama fails, or optional local OCR/Tesseract is unavailable |
