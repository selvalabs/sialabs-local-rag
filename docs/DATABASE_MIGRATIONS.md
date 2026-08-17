# SQLite schema migrations

SoberanIA Labs Local RAG uses a small built-in migration runner for its local SQLite
database. The goal is to keep upgrades explicit and testable without adding a
server-oriented migration framework to a single-user local application.

## How schema versioning works

The database stores one row in `schema_version`. Each application migration has an
integer version and runs in ascending order during application startup.

- A fresh database starts at version `0` and receives every known migration.
- A pre-vNext database containing the original `documents`, `chunks` and
  `chat_messages` tables is adopted as schema version `1`.
- A database with only part of that legacy schema is rejected instead of being
  guessed or silently repaired.
- A database whose version is newer than the running application is rejected.
- Migration execution and version updates run transactionally.

Released migrations are append-only. New schema changes add a new ordered
migration instead of rewriting older definitions.

## Current migrations

### Version 1 — baseline local RAG schema

Creates or adopts the original `documents`, `chunks`, `chat_messages` tables and
chunk indexes.

### Version 2 — embedding index metadata

Adds the singleton `embedding_index` table containing provider, model, vector
dimension and timestamps. Legacy chunks are not assigned guessed embedding
metadata; incompatible/unknown indexes require explicit reset and re-ingestion.

### Version 3 — sanitize persisted chat source metadata

Removes copied source `content` values from existing chat metadata while preserving
lightweight source identifiers. New chat records follow the same policy.

### Version 4 — optional FTS5 retrieval index

Creates/backfills the optional `chunks_fts` table and synchronization triggers when
SQLite FTS5 is available. If FTS5 is unavailable, the application stays usable via
dense retrieval and retries FTS setup on later startup.

### Version 5 — page/section source metadata

Adds nullable source-location fields to `chunks`:

- `page_number`;
- `section_title`;
- `source_locator`.

Existing chunks remain valid with `NULL` values. No embedding reindex is required.
The migration checks existing columns before each additive `ALTER TABLE`, so a
partially newer-shaped schema can recover safely.

### Version 6 — richer Office source metadata

Adds nullable source-location fields used by richer document formats:

- `slide_number` for PPTX sources;
- `sheet_name` for XLSX sources;
- `cell_range` for bounded spreadsheet blocks.

The migration uses the same idempotent per-column check as version 5. Existing
page/section locators and chunk content remain unchanged, and old embeddings remain
valid because vectors and indexed content are not rewritten.

A v5-to-v6 upgrade test verifies that existing content and version-5 metadata
survive and that new slide/sheet/range fields begin as `NULL`.

## Backup before important upgrades

The SQLite file is the user's local data store. Before an important upgrade:

1. Stop the local backend so no writes are in progress.
2. Find the SQLite path configured by `DATABASE_URL`.
3. Copy the database file to a separate backup location.
4. Start the upgraded application and allow migrations to complete.
5. Keep the backup until indexed documents and local behavior have been validated.

## Failure behavior

If startup reports a schema migration error:

- do not repeatedly modify the database by hand;
- keep the original database and backup unchanged;
- record the application version and migration error;
- restore a backup if a destructive migration was involved;
- use a fresh database only when losing the existing local index is acceptable.

Embedding incompatibility is separate from schema migration. If
`GET /api/index/status` reports `legacy` or `incompatible`, use the explicit index
reset/re-ingestion workflow documented in `docs/API.md`.

## Developer workflow

When adding a schema change:

1. Add the next integer `Migration` entry.
2. Keep previously released migrations immutable.
3. Make the migration safe for the immediately previous supported schema.
4. Add a representative upgrade test.
5. Add rollback coverage when the migration is more than trivial additive DDL.
6. Run the complete backend quality gates before merge.

The current schema version can be inspected with `Database.schema_version()`.
