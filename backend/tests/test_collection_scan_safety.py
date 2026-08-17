from __future__ import annotations

import os
from pathlib import Path

import pytest

from sialabs_local_rag.collection_scan import CollectionScanner
from sialabs_local_rag.collection_store import CollectionStore
from sialabs_local_rag.database import Database
from sialabs_local_rag.providers import HashEmbeddingProvider
from sialabs_local_rag.storage import Storage


def _scanner(tmp_path: Path) -> tuple[CollectionScanner, CollectionStore]:
    database = Database(f"sqlite:///{tmp_path / 'safety.db'}")
    database.init_schema()
    storage = Storage(database)
    return (
        CollectionScanner(
            database=database,
            storage=storage,
            embedding_provider=HashEmbeddingProvider(),
            chunk_size=300,
            chunk_overlap=40,
        ),
        CollectionStore(database),
    )


@pytest.mark.asyncio
async def test_remove_policy_deletes_missing_source_record(tmp_path: Path) -> None:
    scanner, collections = _scanner(tmp_path)
    folder = tmp_path / "remove-policy"
    folder.mkdir()
    source_path = folder / "temporary.txt"
    source_path.write_text(
        "REMOVE-POLICY-61 is indexed before the source disappears.",
        encoding="utf-8",
    )
    collection = collections.register_folder(
        "Remove policy",
        folder,
        missing_policy="remove",
    )
    await scanner.scan(collection.id)

    source_path.unlink()
    result = await scanner.scan(collection.id)

    assert result.missing == 1
    assert result.orphan_documents_deleted == 1
    assert collections.list_sources(collection.id) == {}


@pytest.mark.asyncio
async def test_folder_scan_skips_symlinked_files(tmp_path: Path) -> None:
    if not hasattr(os, "symlink"):
        pytest.skip("Symlinks are unavailable on this platform.")

    scanner, collections = _scanner(tmp_path)
    root = tmp_path / "trusted"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (root / "inside.txt").write_text(
        "INSIDE-ONLY-72 belongs to the trusted collection.",
        encoding="utf-8",
    )
    outside_file = outside / "outside.txt"
    outside_file.write_text(
        "OUTSIDE-SYMLINK-73 must never be indexed through a link.",
        encoding="utf-8",
    )
    link = root / "linked-outside.txt"
    try:
        link.symlink_to(outside_file)
    except OSError:
        pytest.skip("This environment does not permit creating symlinks.")

    collection = collections.register_folder("Trusted", root)
    result = await scanner.scan(collection.id)
    sources = collections.list_sources(collection.id)

    assert result.discovered == 1
    assert result.added == 1
    assert result.errors == 0
    assert set(sources) == {"inside.txt"}
