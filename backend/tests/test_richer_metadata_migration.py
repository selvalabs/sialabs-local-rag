from __future__ import annotations

from pathlib import Path

import pytest

import sialabs_local_rag.database as database_module
from sialabs_local_rag.database import Database


def test_version_five_database_upgrades_with_nullable_richer_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database = Database(f"sqlite:///{tmp_path / 'richer-metadata-upgrade.db'}")
    current_migrations = database_module.MIGRATIONS

    monkeypatch.setattr(database_module, "MIGRATIONS", current_migrations[:5])
    database.init_schema()
    assert database.schema_version() == 5

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
                "Legacy source metadata",
                "manual",
                "legacy-richer-hash",
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
                token_estimate, embedding_json, created_at,
                page_number, section_title, source_locator
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "legacy-chunk",
                "legacy-doc",
                0,
                "Legacy chunk with v5 source metadata.",
                9,
                "[1.0,0.0]",
                "2026-01-01T00:00:00+00:00",
                3,
                "Legacy section",
                "page:3",
            ),
        )

    monkeypatch.setattr(database_module, "MIGRATIONS", current_migrations)
    database.init_schema()

    assert database.schema_version() == 6
    with database.connect() as connection:
        row = connection.execute(
            """
            SELECT
                content,
                page_number,
                section_title,
                source_locator,
                slide_number,
                sheet_name,
                cell_range
            FROM chunks
            WHERE id = 'legacy-chunk'
            """
        ).fetchone()

    assert row is not None
    assert row["content"] == "Legacy chunk with v5 source metadata."
    assert row["page_number"] == 3
    assert row["section_title"] == "Legacy section"
    assert row["source_locator"] == "page:3"
    assert row["slide_number"] is None
    assert row["sheet_name"] is None
    assert row["cell_range"] is None
