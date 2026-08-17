from __future__ import annotations

from pathlib import Path

import pytest

import sialabs_local_rag.database as database_module
from sialabs_local_rag.database import Database


def test_version_four_database_upgrades_with_nullable_source_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database = Database(f"sqlite:///{tmp_path / 'metadata-upgrade.db'}")
    current_migrations = database_module.MIGRATIONS

    monkeypatch.setattr(database_module, "MIGRATIONS", current_migrations[:4])
    database.init_schema()
    assert database.schema_version() == 4

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
                "Legacy structured source",
                "manual",
                "legacy-structured-hash",
                20,
                1,
                "2026-01-01T00:00:00+00:00",
                "2026-01-01T00:00:00+00:00",
            ),
        )
        connection.execute(
            """
            INSERT INTO chunks (
                id, document_id, chunk_index, content,
                token_estimate, embedding_json, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "legacy-chunk",
                "legacy-doc",
                0,
                "Legacy chunk without source metadata.",
                9,
                "[1.0,0.0]",
                "2026-01-01T00:00:00+00:00",
            ),
        )

    monkeypatch.setattr(database_module, "MIGRATIONS", current_migrations)
    database.init_schema()

    assert database.schema_version() == database_module.latest_schema_version()
    with database.connect() as connection:
        row = connection.execute(
            """
            SELECT content, page_number, section_title, source_locator
            FROM chunks
            WHERE id = 'legacy-chunk'
            """
        ).fetchone()

    assert row is not None
    assert row["content"] == "Legacy chunk without source metadata."
    assert row["page_number"] is None
    assert row["section_title"] is None
    assert row["source_locator"] is None
