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

Creates a document from pasted plain text.

```json
{
  "title": "Example document",
  "content": "First paragraph.\n\nSecond paragraph.",
  "source_type": "manual"
}
```

Plain-text ingestion preserves paragraph boundaries inside structured chunks when
the content fits the configured chunk size. Larger content prefers paragraph,
sentence and then word boundaries.

### `POST /api/documents/upload`

Uploads and indexes `.txt`, `.md`, `.markdown` or selectable-text `.pdf` files.
Maximum upload size is 1 MB.

The ingestion pipeline preserves source structure where the parser can recover it:

- Markdown headings define section boundaries. Returned sources may include
  `section_title` and a locator such as `section:Recovery`.
- PDF pages define hard chunking boundaries. Returned sources may include
  `page_number` and a locator such as `page:2`.
- Plain text preserves paragraph breaks but has no inferred page/section metadata.
- Chunks never intentionally cross a parsed Markdown section or PDF page boundary.

Chunk text includes a compact human-readable prefix such as `Section: Recovery` or
`Page 2`, while the API also exposes the location as structured fields.

PDF limitations remain:

- scanned PDFs are not processed with OCR;
- images are not extracted;
- tables are not reconstructed;
- password-protected, damaged or textless PDFs return a validation error.

OCR and richer Office/document layout support are tracked separately from this
structure-aware text ingestion path.

### `GET /api/documents`

Lists indexed documents.

### `DELETE /api/documents/{document_id}`

Deletes a document and its chunks and clears persisted backend chat history because
previous generated answers may derive from the deleted source.

### `POST /api/chat`

Queries the local document collection. The request separates the current
`question` from optional `conversation_context`; the response includes the backend
`retrieval_query` used for embedding/search.

Example:

```json
{
  "question": "What is its notice period?",
  "conversation_context": [
    {
      "role": "user",
      "content": "Explain the Cedar remote-work policy."
    }
  ],
  "top_k": 5
}
```

A retrieved source can now include location metadata:

```json
{
  "document_title": "Maintenance Manual",
  "chunk_index": 3,
  "page_number": null,
  "section_title": "Recovery",
  "source_locator": "section:Recovery",
  "score": 0.0324,
  "content": "Section: Recovery\n\n..."
}
```

For PDFs, `page_number` is 1-based. Fields remain `null` for legacy chunks or source
formats where that location type does not exist.

Conversation history is dialogue context, not factual evidence. Assistant-history
text is never copied into the embedding query, and factual answer claims must be
grounded in retrieved sources.

## Embedding compatibility and reindexing

The application never intentionally mixes vectors from different declared
embedding spaces. Legacy or incompatible indexes return `409 Conflict` with an
explicit reset/re-ingestion path.

Adding source metadata in schema version 5 does **not** require a reindex of old
vectors. Existing chunks remain valid with nullable page/section/locator fields.
Re-ingestion is only needed when the user wants historical documents to gain the
newly extractable structure metadata.

## Expected errors

| Status | Case |
| --- | --- |
| 400 | Full local-data reset confirmation header is missing or invalid |
| 403 | Full local-data reset is requested from a non-loopback client |
| 409 | Duplicate document or incompatible/legacy embedding index |
| 413 | Upload exceeds the size limit |
| 415 | Unsupported file extension |
| 422 | Invalid payload, non-UTF-8 text or invalid PDF |
| 503 | Ollama is unavailable or a provider request fails |
