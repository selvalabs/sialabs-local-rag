from __future__ import annotations

from pathlib import Path

import pytest

import sialabs_local_rag.database as database_module
from sialabs_local_rag.database import Database


def test_version_six_database_upgrades_and_backfills_default_collection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database = Database(f"sqlite:///{tmp_path / 'collections-upgrade.db'}")
    current_migrations = database_module.MIGRATIONS

    monkeypatch.setattr(database_module, "MIGRATIONS", current_migrations[:6])
    database.init_schema()
    assert database.schema_version() == 6

    with database.connect() as connection:
        connection.execute(
            """
            INSERT INTO documents (
                id, title, source_type, content_hash, total_chars,
                total_chunks, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "legacy-doc",
                "Legacy collection document",
                "manual",
                "legacy-collection-hash",
                20,
                0,
                "2026-01-01T00:00:00+00:00",
                "2026-01-01T00:00:00+00:00",
            ),
        )

    monkeypatch.setattr(database_module, "MIGRATIONS", current_migrations)
    database.init_schema()

    assert database.schema_version() == database_module.latest_schema_version()
    with database.connect() as connection:
        collection = connection.execute(
            "SELECT id, name, kind, root_path FROM collections WHERE id = 'default'"
        ).fetchone()
        source = connection.execute(
            """
            SELECT collection_id, document_id, relative_path, status
            FROM collection_sources
            WHERE document_id = 'legacy-doc'
            """
        ).fetchone()

    assert collection is not None
    assert collection["name"] == "Local base"
    assert collection["kind"] == "manual"
    assert collection["root_path"] is None
    assert source is not None
    assert source["collection_id"] == "default"
    assert source["relative_path"] is None
    assert source["status"] == "active"
