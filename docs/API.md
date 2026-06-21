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

### `POST /api/documents`

Creates a document from pasted text.

```json
{
  "title": "Example document",
  "content": "Text with enough content for indexing.",
  "source_type": "manual"
}
```

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

The response includes:

- generated answer;
- retrieved sources;
- similarity scores;
- provider and model metadata;
- latency in milliseconds.

## Expected errors

| Status | Case |
| --- | --- |
| 409 | Duplicate document |
| 413 | Upload exceeds the size limit |
| 415 | Unsupported file extension |
| 422 | Invalid payload, non-UTF-8 text or invalid PDF |
| 503 | Ollama is unavailable or a provider request fails |
