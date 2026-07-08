# Security and Privacy

## Local-first principle

Document content remains in the user's local environment by default. The application does not require an external LLM API for its primary local AI path.

## Persisted data

The local SQLite database stores:

- document metadata;
- text chunks;
- embeddings serialized as JSON;
- chat questions and answers used for local traceability.

Anyone with access to the database file may be able to read this content.

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
