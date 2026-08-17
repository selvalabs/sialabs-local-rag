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
chunks, removes the stored embedding signature and clears persisted backend chat
traces because answers may contain facts derived from the removed documents.

### `DELETE /api/chat/history`

Deletes all persisted backend chat trace records. New chat records keep the
question, answer, runtime metadata and lightweight source identifiers, but do not
copy retrieved chunk text into `metadata_json`.

The frontend Clear chat action calls this endpoint and also removes the browser
conversation history.

### `DELETE /api/local-data`

Performs a destructive reset of the app's persisted local knowledge data:

- documents;
- chunks;
- embedding-index signature;
- backend chat traces.

The endpoint is deliberately guarded. In normal runtime the request must originate
from a loopback client and must include:

```text
X-Confirm-Local-Data-Reset: delete-all
```

This endpoint is not intended as a public or routine remote administration API.

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

Deletes a document and its associated chunks. A successful deletion also clears
persisted backend chat history so generated answers derived from the deleted
source are not retained as an undocumented secondary copy.

The frontend clears its local conversation state after a successful document
deletion as well.

### `POST /api/chat`

Queries the local document collection. The contract separates three concepts:

- `question` is the user's current intent and is preserved as the original chat
  question;
- `conversation_context` contains recent dialogue turns and is optional;
- `retrieval_query` is produced by the backend and returned in the response for
  evaluation/debugging.

Example follow-up request:

```json
{
  "question": "What is its notice period?",
  "conversation_context": [
    {
      "role": "user",
      "content": "Explain the Cedar remote-work policy."
    },
    {
      "role": "assistant",
      "content": "The previous answer is available as dialogue context."
    }
  ],
  "top_k": 5
}
```

Standalone questions use the current question directly as the retrieval query.
For short/referential follow-ups, the deterministic backend resolver may prepend
the latest relevant user turn. Assistant-generated history is never copied into
the embedding query.

Conversation context remains available to the answer-generation prompt for dialogue
continuity, but it is explicitly labeled as non-evidence. Factual claims must come
from retrieved document sources; prior assistant text must not be treated as a
source of truth.

A response includes:

- generated answer;
- retrieved sources;
- provider and model metadata;
- derived `retrieval_query`;
- retrieval top K;
- latency in milliseconds.

Before retrieval, the application verifies that the configured embedding
provider/model matches the persisted index signature. After creating the query
embedding, the vector dimension is checked as well.

Retrieved source content is returned to the active client so it can be inspected,
but it is not duplicated into new backend chat trace metadata. The frontend also
does not serialize the detailed response/source objects into persistent browser
chat history.

## Conversational retrieval behavior

The follow-up resolver is intentionally deterministic and cheap. It does not add a
mandatory second LLM call.

Representative behavior:

- a standalone topic switch such as `Explain Harbor finance reserve requirements.`
  remains exactly that retrieval query even after a Cedar conversation;
- a referential follow-up such as `What is its notice period?` can use the latest
  user question as an anchor;
- misleading or incorrect assistant-history text is excluded from the retrieval
  query;
- if there is no previous user message to resolve a reference, the current question
  remains standalone rather than guessing an anchor.

This separation prevents generated assistant prose from silently changing what is
embedded while preserving enough recent dialogue for follow-up continuity.

## Embedding compatibility and reindexing

The application never intentionally mixes vectors from different declared
embedding spaces.

If indexed chunks were created before embedding metadata existed, or if the
configured provider/model/dimension is incompatible with the stored index,
document ingestion and chat return `409 Conflict` with a reindex instruction.

Safe recovery is explicit:

1. Back up the local SQLite database if the existing index matters.
2. Call `GET /api/index/status` to inspect the reason.
3. Call `DELETE /api/index` only when you accept removing the indexed documents and associated chat traces.
4. Re-ingest the source documents using the current embedding configuration.

The application does not silently reconstruct/re-embed old documents because the
current schema does not preserve every original uploaded file in a lossless form.

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
