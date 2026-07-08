# Security Policy

SoberanIA Labs Local RAG is a local-first reference implementation for trusted local use.

## Supported security boundary

The current project is designed to run on `localhost` / `127.0.0.1` with local SQLite storage and local Ollama runtime access.

It is not hardened for public internet exposure and does not currently provide authentication, per-user authorization, encrypted local database storage or multi-tenant isolation.

## Public repository safety

This repository should contain source code, documentation, deterministic demo fixtures and configuration examples only.

Do not commit:

- real `.env` files;
- API keys, tokens or credentials;
- customer or personal documents;
- local SQLite databases or database dumps;
- generated uploads;
- downloaded Ollama model files;
- release artifacts generated under local `dist/` directories.

## Reporting issues

For non-sensitive security hardening tasks, open a GitHub issue with enough technical context to reproduce the concern.

Do not include private documents, API keys, credentials, database dumps or personal data in public issues.

For the full project-specific privacy and security notes, see [`docs/SECURITY_PRIVACY.md`](docs/SECURITY_PRIVACY.md).
