# Security and Privacy

## Local-first principle

Document content remains in the user's local environment by default. The application does not require an external LLM API for its primary local AI path.

## Persisted data

The local SQLite database stores:

- document metadata;
- text chunks;
- embeddings serialized as JSON;
- chat questions and answers used for local traceability;
- lightweight source references for chat traces, such as document/chunk identifiers and scores.

New chat trace metadata does **not** duplicate the retrieved chunk text. Schema migration version 3 removes the `content` field from source metadata persisted by older versions while preserving lightweight source identifiers.

The browser keeps conversational continuity in `localStorage`, but persists only message `id`, `role` and displayed message text. Detailed `ChatResponse` objects and retrieved source excerpts are kept in memory for the current browser session and are not serialized into the persistent chat-history key.

Anyone with access to the SQLite database file or the user's browser profile may be able to read the remaining locally persisted content. SQLite storage is not encrypted by the application.

## Deletion semantics

Deletion behavior is intentionally explicit:

- **Clear chat** (`DELETE /api/chat/history`) removes persisted backend chat traces. The frontend Clear chat action also removes the browser chat history.
- **Delete document** removes the document and its chunks through SQLite cascade behavior and clears persisted backend chat traces, because generated answers may contain facts derived from the deleted document. The frontend also clears its local conversation state after a successful document deletion.
- **Reset embedding index** removes indexed documents/chunks, clears the embedding signature and clears backend chat traces.
- **Full local data reset** (`DELETE /api/local-data`) removes documents, chunks, the embedding-index signature and backend chat traces.

If the backend is unavailable while the user presses Clear chat, the frontend still removes its local browser history and reports the backend error. Backend traces then remain until the clear operation succeeds or the local database is reset/deleted.

### Guarded full local reset

The full local-data reset endpoint is intentionally harder to invoke than normal deletion operations:

- it accepts requests only from a loopback client (`127.0.0.1` or `::1` in normal runtime);
- it requires the explicit header `X-Confirm-Local-Data-Reset: delete-all`;
- it is not exposed as a routine UI action.

This is defense in depth for a destructive local operation, not a substitute for authentication if the API is exposed beyond localhost.

## Public repository safety

The public repository is intended to include source code, documentation, deterministic demo fixtures and configuration examples only.

It should not include:

- real user documents;
- local SQLite databases;
- generated uploads;
- real `.env` files;
- API keys, tokens or credentials;
- downloaded Ollama model files;
- local release artifacts or installer output.

Ollama models are external local dependencies and are not bundled in the repository.

## Data that must not be committed

- real `.env` files;
- tokens or API keys;
- customer or personal documents;
- database dumps containing private content;
- downloaded model files;
- generated uploads or local runtime artifacts.

## Security boundary

The current application is designed for trusted local use. It does not provide:

- authentication;
- per-user authorization;
- encrypted local database storage;
- tenant or workspace isolation;
- user-specific retention policies;
- hardened public deployment defaults.

The launcher, frontend and backend flows are intended to run on `localhost` or `127.0.0.1`. Do not expose the application, launcher, backend API or Ollama directly to the public internet without authentication, network controls and a deployment-specific security review.

## File handling limitations

- Upload size is limited by the backend.
- Supported extensions are explicitly allow-listed.
- PDFs are processed only for extractable text.
- OCR, image extraction and complex table reconstruction are not supported.
- Uploaded content and retrieved text must be treated as untrusted data when constructing model prompts.

## Recommended hardening for broader deployment

- Place the application behind an authenticated reverse proxy.
- Add authorization for document and administrative endpoints.
- Add request rate limits and structured audit logs.
- Define backup, deletion and retention procedures.
- Encrypt sensitive storage where required.
- Add automated secret scanning and dependency monitoring.
