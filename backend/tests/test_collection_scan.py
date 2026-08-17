from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest

from sialabs_local_rag.collection_scan import CollectionScanner
from sialabs_local_rag.collection_store import CollectionStore
from sialabs_local_rag.database import Database
from sialabs_local_rag.providers import HashEmbeddingProvider
from sialabs_local_rag.storage import Storage


class CountingHashEmbeddingProvider:
    name = "hash"
    model = "hash-bow-128"

    def __init__(self) -> None:
        self.inner = HashEmbeddingProvider()
        self.calls = 0
        self.texts_embedded = 0

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        self.calls += 1
        self.texts_embedded += len(texts)
        return await self.inner.embed(texts)


def _build_scanner(
    tmp_path: Path,
) -> tuple[CollectionScanner, CollectionStore, CountingHashEmbeddingProvider]:
    database = Database(f"sqlite:///{tmp_path / 'collections.db'}")
    database.init_schema()
    storage = Storage(database)
    provider = CountingHashEmbeddingProvider()
    return (
        CollectionScanner(
            database=database,
            storage=storage,
            embedding_provider=provider,
            chunk_size=300,
            chunk_overlap=40,
        ),
        CollectionStore(database),
        provider,
    )


@pytest.mark.asyncio
async def test_second_identical_scan_does_not_reembed(tmp_path: Path) -> None:
    scanner, collections, provider = _build_scanner(tmp_path)
    folder = tmp_path / "knowledge"
    folder.mkdir()
    (folder / "alpha.md").write_text(
        "# Alpha\n\nALPHA-COLLECTION-11 is the indexed safety code.",
        encoding="utf-8",
    )
    (folder / "beta.txt").write_text(
        "BETA-COLLECTION-22 is the indexed recovery code.",
        encoding="utf-8",
    )
    collection = collections.register_folder("Knowledge", folder)

    first = await scanner.scan(collection.id)
    calls_after_first = provider.calls
    second = await scanner.scan(collection.id)

    assert first.added == 2
    assert first.errors == 0
    assert calls_after_first == 2
    assert second.unchanged == 2
    assert second.added == 0
    assert second.changed == 0
    assert second.errors == 0
    assert provider.calls == calls_after_first


@pytest.mark.asyncio
async def test_changed_file_reembeds_only_that_source_and_dry_run_is_read_only(
    tmp_path: Path,
) -> None:
    scanner, collections, provider = _build_scanner(tmp_path)
    folder = tmp_path / "work"
    folder.mkdir()
    alpha = folder / "alpha.txt"
    beta = folder / "beta.txt"
    alpha.write_text("Alpha version one with CODE-A1.", encoding="utf-8")
    beta.write_text("Beta remains unchanged with CODE-B1.", encoding="utf-8")
    collection = collections.register_folder("Work", folder)
    await scanner.scan(collection.id)
    initial_calls = provider.calls

    alpha.write_text("Alpha version two with CODE-A2 and changed content.", encoding="utf-8")
    dry_run = await scanner.scan(collection.id, dry_run=True)

    assert dry_run.changed == 1
    assert dry_run.unchanged == 1
    assert provider.calls == initial_calls
    assert collections.list_sources(collection.id)["alpha.txt"].content_hash != ""

    applied = await scanner.scan(collection.id)

    assert applied.changed == 1
    assert applied.unchanged == 1
    assert applied.orphan_documents_deleted == 1
    assert provider.calls == initial_calls + 1


@pytest.mark.asyncio
async def test_missing_file_can_be_marked_and_removed_from_active_index(
    tmp_path: Path,
) -> None:
    scanner, collections, _ = _build_scanner(tmp_path)
    folder = tmp_path / "missing"
    folder.mkdir()
    source_path = folder / "source.txt"
    source_path.write_text("MISSING-CODE-31 is initially indexed.", encoding="utf-8")
    collection = collections.register_folder("Missing", folder, missing_policy="mark")
    await scanner.scan(collection.id)

    source_path.unlink()
    result = await scanner.scan(collection.id)
    source = collections.list_sources(collection.id)["source.txt"]

    assert result.missing == 1
    assert result.orphan_documents_deleted == 1
    assert source.status == "missing"
    assert source.document_id is None


@pytest.mark.asyncio
async def test_identical_content_across_collections_reuses_existing_document(
    tmp_path: Path,
) -> None:
    scanner, collections, provider = _build_scanner(tmp_path)
    first_folder = tmp_path / "first"
    second_folder = tmp_path / "second"
    first_folder.mkdir()
    second_folder.mkdir()
    shared_text = "SHARED-COLLECTION-44 has identical content in two local folders."
    (first_folder / "shared.txt").write_text(shared_text, encoding="utf-8")
    (second_folder / "copy.txt").write_text(shared_text, encoding="utf-8")
    first_collection = collections.register_folder("First", first_folder)
    second_collection = collections.register_folder("Second", second_folder)

    first = await scanner.scan(first_collection.id)
    calls_after_first = provider.calls
    second = await scanner.scan(second_collection.id)

    assert first.added == 1
    assert second.added == 1
    assert second.reused == 1
    assert provider.calls == calls_after_first
    with collections.database.connect() as connection:
        document_count = connection.execute("SELECT COUNT(*) AS count FROM documents").fetchone()
        source_count = connection.execute(
            "SELECT COUNT(*) AS count FROM collection_sources WHERE relative_path IS NOT NULL"
        ).fetchone()
    assert document_count is not None and int(document_count["count"]) == 1
    assert source_count is not None and int(source_count["count"]) == 2
