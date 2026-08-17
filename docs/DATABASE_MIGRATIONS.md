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
- Migration execution and the version update run in one SQLite transaction. A
  failed migration is rolled back before startup reports an error.

Released migrations are append-only. New schema changes must add a new ordered
migration instead of rewriting older migration definitions.

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

Creates and backfills the optional `chunks_fts` table and synchronization triggers
when SQLite FTS5 is available. If FTS5 is unavailable, the application remains
usable through dense retrieval and retries FTS setup on later startup.

### Version 5 — chunk source metadata

Adds nullable source-location fields to `chunks`:

- `page_number` for page-aware sources such as PDFs;
- `section_title` for heading-aware sources such as Markdown;
- `source_locator` for a compact stable locator such as `page:2` or
  `section:Recovery`.

Existing chunks remain valid and receive `NULL` values. No embedding reindex is
required because the stored vector/content columns are not rewritten.

The migration checks the existing `chunks` columns before each additive `ALTER
TABLE`, making the nullable metadata upgrade safe if a database schema has already
acquired one or more of these columns while its version marker still needs repair.
An explicit v4-to-v5 upgrade test verifies that existing chunk content survives and
metadata starts null.

## Backup before important upgrades

The application is local-first, so the SQLite file is the user's data store. Before
an upgrade that changes stored data or performs a destructive migration:

1. Stop the local backend so no writes are in progress.
2. Find the SQLite path configured by `DATABASE_URL`.
3. Copy the database file to a separate backup location.
4. Start the upgraded application and allow migrations to complete.
5. Keep the backup until indexed documents and chat/data behavior have been
   validated.

## Failure behavior

If startup reports a schema migration error:

- do not repeatedly modify the database by hand;
- keep the original database and any backup unchanged;
- record the application version and full migration error;
- restore the backup if a destructive migration was involved;
- use a fresh database only when losing the existing local index is acceptable.

Embedding incompatibility is not a schema migration failure. If
`GET /api/index/status` reports `legacy` or `incompatible`, use the explicit index
reset/re-ingestion workflow documented in `docs/API.md`.

## Developer workflow

When adding a schema change:

1. Add a new `Migration` entry with the next integer version.
2. Keep previously released migrations immutable.
3. Make the migration safe for the immediately previous supported schema.
4. Add an upgrade test using a representative older schema/database state.
5. Add a rollback test when the migration contains more than trivial additive DDL.
6. Run the complete backend quality gates before merge.

The current schema version can be inspected programmatically with
`Database.schema_version()`.
