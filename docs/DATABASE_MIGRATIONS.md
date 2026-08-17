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

This migration layer is intentionally small. Future changes that add embedding
metadata, richer source locations or collections should add a new ordered migration
instead of modifying old migrations in place.

## Backup before important upgrades

The application is local-first, so the SQLite file is the user's data store. Before
an upgrade that changes stored data or performs a destructive migration:

1. Stop the local backend so no writes are in progress.
2. Find the SQLite path configured by `DATABASE_URL`.
3. Copy the database file to a separate backup location.
4. Start the upgraded application and allow migrations to complete.
5. Keep the backup until indexed documents and chat/data behavior have been
   validated.

For the default relative database configuration, resolve the path from the working
directory used to start the backend.

## Failure behavior

If startup reports a schema migration error:

- do not repeatedly modify the database by hand;
- keep the original database and any backup unchanged;
- record the application version and full migration error;
- restore the backup if a destructive migration was involved;
- use a fresh database only when losing the existing local index is acceptable.

A migration failure should not leave a partially applied schema. Tests cover
transaction rollback and upgrade from the pre-vNext schema.

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
