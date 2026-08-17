# API

Interactive OpenAPI documentation is available at `http://localhost:8000/docs` while the backend is running.

## Endpoints

### `GET /health`

Checks API availability.

### `GET /api/config`

Returns non-sensitive runtime configuration:

- chat provider and model;
- embedding provider and model;
- retrieval top K;
- chunk size and overlap.

Secrets and private environment values are not returned.

### `GET /api/index/status`

Reports whether the persisted embedding index is compatible with the currently
configured embedding provider/model.

Possible states:

- `empty` — there are no indexed chunks; the next ingestion may establish the
  current embedding signature;
- `ready` — persisted provider/model metadata matches the current configuration;
- `legacy` — chunks exist but predate embedding metadata, so compatibility cannot
  be proven;
- `incompatible` — indexed chunks were created with a different provider/model.

The response also includes the stored vector dimension when known and a
`reindex_required` flag.

### `DELETE /api/index`

Explicitly resets the document/vector index so documents can be re-ingested with a
new embedding configuration. The operation deletes indexed documents and their
chunks plus the stored embedding signature.

This endpoint does **not** clear persisted chat history. Chat persistence and
retention are tracked separately from the embedding-index lifecycle.

### `POST /api/documents`

Creates a document from pasted text.

```json
{
  "title": "Example document",
  "content": "Text with enough content for indexing.",
  "source_type": "manual"
}
```

The first successful ingestion into an empty index records the embedding
provider/model/vector dimension. Later ingestion must use the same embedding
space while indexed chunks remain.

### `POST /api/documents/upload`

Uploads and indexes a supported file. Accepted extensions:

- `.txt`
- `.md`
- `.markdown`
- `.pdf`

The maximum upload size is 1 MB.

Text and Markdown files must be UTF-8. For PDFs, the backend extracts selectable text and sends the extracted content through the same chunking and indexing pipeline.

PDF limitations:

- scanned PDFs are not processed with OCR;
- images are not extracted;
- tables are not reconstructed;
- password-protected, damaged or textless PDFs return a validation error.

### `GET /api/documents`

Lists indexed documents.

### `DELETE /api/documents/{document_id}`

Deletes a document and its associated chunks.

### `POST /api/chat`

Queries the local document collection.

```json
{
  "question": "Which technologies are used by this application?",
  "top_k": 5
}
```

Before retrieval, the application verifies that the configured embedding
provider/model matches the persisted index signature. After creating the query
embedding, the vector dimension is checked as well.

The response includes:

- generated answer;
- retrieved sources;
- similarity scores;
- provider and model metadata;
- latency in milliseconds.

## Embedding compatibility and reindexing

The application never intentionally mixes vectors from different declared
embedding spaces.

If indexed chunks were created before embedding metadata existed, or if the
configured provider/model/dimension is incompatible with the stored index,
document ingestion and chat return `409 Conflict` with a reindex instruction.

Safe recovery is explicit:

1. Back up the local SQLite database if the existing index matters.
2. Call `GET /api/index/status` to inspect the reason.
3. Call `DELETE /api/index` only when you accept removing the indexed documents.
4. Re-ingest the source documents using the current embedding configuration.

The application does not silently reconstruct/re-embed old documents because the
current schema does not preserve every original uploaded file in a lossless form.

## Expected errors

| Status | Case |
| --- | --- |
| 409 | Duplicate document or incompatible/legacy embedding index |
| 413 | Upload exceeds the size limit |
| 415 | Unsupported file extension |
| 422 | Invalid payload, non-UTF-8 text or invalid PDF |
| 503 | Ollama is unavailable or a provider request fails |
