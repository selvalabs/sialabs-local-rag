from __future__ import annotations

from collections.abc import Sequence

from sialabs_local_rag.chunking import StructuredChunk
from sialabs_local_rag.database import Database
from sialabs_local_rag.schemas import SourceChunk


def persist_chunk_source_metadata(
    database: Database,
    document_id: str,
    chunks: Sequence[StructuredChunk],
) -> None:
    if not chunks:
        return

    with database.connect() as connection:
        connection.executemany(
            """
            UPDATE chunks
            SET
                page_number = ?,
                section_title = ?,
                slide_number = ?,
                sheet_name = ?,
                cell_range = ?,
                source_locator = ?
            WHERE document_id = ? AND chunk_index = ?
            """,
            [
                (
                    chunk.page_number,
                    chunk.section_title,
                    chunk.slide_number,
                    chunk.sheet_name,
                    chunk.cell_range,
                    chunk.source_locator,
                    document_id,
                    index,
                )
                for index, chunk in enumerate(chunks)
            ],
        )


def enrich_source_metadata(
    database: Database,
    sources: Sequence[SourceChunk],
) -> list[SourceChunk]:
    if not sources:
        return []

    chunk_ids = [source.chunk_id for source in sources]
    placeholders = ",".join("?" for _ in chunk_ids)
    with database.connect() as connection:
        rows = connection.execute(
            f"""
            SELECT
                id,
                page_number,
                section_title,
                slide_number,
                sheet_name,
                cell_range,
                source_locator
            FROM chunks
            WHERE id IN ({placeholders})
            """,  # noqa: S608 - placeholders are generated, values stay parameterized.
            chunk_ids,
        ).fetchall()

    metadata_by_id = {
        str(row["id"]): {
            "page_number": (
                int(row["page_number"]) if row["page_number"] is not None else None
            ),
            "section_title": (
                str(row["section_title"]) if row["section_title"] is not None else None
            ),
            "slide_number": (
                int(row["slide_number"]) if row["slide_number"] is not None else None
            ),
            "sheet_name": (
                str(row["sheet_name"]) if row["sheet_name"] is not None else None
            ),
            "cell_range": (
                str(row["cell_range"]) if row["cell_range"] is not None else None
            ),
            "source_locator": (
                str(row["source_locator"]) if row["source_locator"] is not None else None
            ),
        }
        for row in rows
    }

    return [
        source.model_copy(update=metadata_by_id.get(source.chunk_id, {}))
        for source in sources
    ]
