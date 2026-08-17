from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from sialabs_local_rag.chunking import chunk_parsed_segments
from sialabs_local_rag.collection_store import (
    CollectionPathError,
    CollectionStore,
)
from sialabs_local_rag.database import Database
from sialabs_local_rag.ocr import OcrUnavailableError
from sialabs_local_rag.parsing import (
    DocumentParsingError,
    ParsedDocument,
    parse_uploaded_document_structured,
)
from sialabs_local_rag.providers import EmbeddingProvider, ProviderError
from sialabs_local_rag.schemas import DocumentResponse
from sialabs_local_rag.source_metadata import persist_chunk_source_metadata
from sialabs_local_rag.storage import ChunkInput, Storage

_FOLDER_SCAN_EXTENSIONS = {
    ".txt",
    ".md",
    ".markdown",
    ".pdf",
    ".docx",
    ".pptx",
    ".xlsx",
}
_MAX_FOLDER_FILES = 5_000
_MAX_FOLDER_FILE_BYTES = 10_000_000


@dataclass(frozen=True)
class CollectionScanResult:
    collection_id: str
    dry_run: bool
    missing_policy: str
    discovered: int
    added: int
    changed: int
    reused: int
    unchanged: int
    missing: int
    errors: int
    orphan_documents_deleted: int


class CollectionScanner:
    def __init__(
        self,
        database: Database,
        storage: Storage,
        embedding_provider: EmbeddingProvider,
        chunk_size: int,
        chunk_overlap: int,
    ) -> None:
        self.database = database
        self.storage = storage
        self.embedding_provider = embedding_provider
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.collections = CollectionStore(database)

    async def scan(
        self,
        collection_id: str,
        *,
        dry_run: bool = False,
        missing_policy: str | None = None,
    ) -> CollectionScanResult:
        collection = self.collections.get_collection(collection_id)
        if collection.kind != "folder" or collection.root_path is None:
            raise CollectionPathError("Only registered folder collections can be rescanned.")

        policy = missing_policy or collection.missing_policy
        if policy not in {"mark", "remove"}:
            raise CollectionPathError("missing_policy must be 'mark' or 'remove'.")

        root = Path(collection.root_path).expanduser().resolve()
        if not root.exists() or not root.is_dir():
            raise CollectionPathError(f"Collection folder is unavailable: {root}")

        existing = self.collections.list_sources(collection_id)
        discovered_paths: set[str] = set()
        discovered = added = changed = reused = unchanged = errors = 0
        orphan_documents_deleted = 0

        for path in self._iter_supported_files(root):
            discovered += 1
            if discovered > _MAX_FOLDER_FILES:
                raise CollectionPathError(
                    f"Collection exceeds the local limit of {_MAX_FOLDER_FILES} supported files."
                )

            relative_path = path.relative_to(root).as_posix()
            discovered_paths.add(relative_path)
            stat = path.stat()
            file_size = int(stat.st_size)
            modified_ns = int(stat.st_mtime_ns)
            previous = existing.get(relative_path)

            if file_size > _MAX_FOLDER_FILE_BYTES:
                errors += 1
                if not dry_run:
                    raw_hash = _metadata_hash(file_size, modified_ns)
                    old_document = self.collections.record_source_error(
                        collection_id=collection_id,
                        relative_path=relative_path,
                        raw_content_hash=raw_hash,
                        file_size=file_size,
                        modified_ns=modified_ns,
                        error="File exceeds the 10 MB local collection-scan limit.",
                    )
                    if self.collections.delete_document_if_orphaned(old_document):
                        orphan_documents_deleted += 1
                continue

            try:
                raw_content = path.read_bytes()
            except OSError as exc:
                errors += 1
                if not dry_run:
                    old_document = self.collections.record_source_error(
                        collection_id=collection_id,
                        relative_path=relative_path,
                        raw_content_hash=_metadata_hash(file_size, modified_ns),
                        file_size=file_size,
                        modified_ns=modified_ns,
                        error=f"Could not read file: {exc}",
                    )
                    if self.collections.delete_document_if_orphaned(old_document):
                        orphan_documents_deleted += 1
                continue

            raw_hash = sha256(raw_content).hexdigest()
            if (
                previous is not None
                and previous.status == "active"
                and previous.document_id is not None
                and previous.content_hash == raw_hash
            ):
                unchanged += 1
                if not dry_run:
                    self.collections.touch_unchanged_source(
                        previous.id,
                        file_size=file_size,
                        modified_ns=modified_ns,
                    )
                continue

            is_change = previous is not None
            if dry_run:
                if is_change:
                    changed += 1
                else:
                    added += 1
                continue

            try:
                parsed = parse_uploaded_document_structured(path.name, raw_content)
                existing_document = self.collections.find_document_by_content(parsed.content)
                if existing_document is not None:
                    document = existing_document
                    reused += 1
                else:
                    document = await self._index_document(
                        title=path.name,
                        parsed=parsed,
                    )

                old_document = self.collections.upsert_file_source(
                    collection_id=collection_id,
                    relative_path=relative_path,
                    document_id=document.id,
                    raw_content_hash=raw_hash,
                    file_size=file_size,
                    modified_ns=modified_ns,
                )
                if self.collections.delete_document_if_orphaned(old_document):
                    orphan_documents_deleted += 1

                if is_change:
                    changed += 1
                else:
                    added += 1
            except (DocumentParsingError, OcrUnavailableError, ProviderError, ValueError) as exc:
                errors += 1
                old_document = self.collections.record_source_error(
                    collection_id=collection_id,
                    relative_path=relative_path,
                    raw_content_hash=raw_hash,
                    file_size=file_size,
                    modified_ns=modified_ns,
                    error=str(exc),
                )
                if self.collections.delete_document_if_orphaned(old_document):
                    orphan_documents_deleted += 1

        missing_sources = [
            source
            for relative_path, source in existing.items()
            if relative_path not in discovered_paths
        ]
        missing = len(missing_sources)
        if not dry_run:
            for source in missing_sources:
                old_document = self.collections.handle_missing_source(source, policy)
                if self.collections.delete_document_if_orphaned(old_document):
                    orphan_documents_deleted += 1
            self.collections.mark_collection_scanned(collection_id)

        return CollectionScanResult(
            collection_id=collection_id,
            dry_run=dry_run,
            missing_policy=policy,
            discovered=discovered,
            added=added,
            changed=changed,
            reused=reused,
            unchanged=unchanged,
            missing=missing,
            errors=errors,
            orphan_documents_deleted=orphan_documents_deleted,
        )

    async def _index_document(
        self,
        title: str,
        parsed: ParsedDocument,
    ) -> DocumentResponse:
        structured_chunks = chunk_parsed_segments(
            parsed.segments,
            chunk_size=self.chunk_size,
            overlap=self.chunk_overlap,
        )
        if not structured_chunks:
            raise DocumentParsingError("Document content did not produce any chunks.")

        self.storage.assert_embedding_compatible(
            provider=self.embedding_provider.name,
            model=self.embedding_provider.model,
        )
        embeddings = await self.embedding_provider.embed(
            [chunk.content for chunk in structured_chunks]
        )
        if len(embeddings) != len(structured_chunks):
            raise ProviderError("Embedding provider returned an unexpected number of vectors.")

        created = self.storage.create_document(
            title=title,
            source_type="folder",
            original_content=parsed.content,
            chunks=[
                ChunkInput(
                    index=index,
                    content=chunk.content,
                    embedding=embeddings[index],
                )
                for index, chunk in enumerate(structured_chunks)
            ],
            embedding_provider=self.embedding_provider.name,
            embedding_model=self.embedding_provider.model,
        )
        persist_chunk_source_metadata(self.database, created.id, structured_chunks)
        return created

    @staticmethod
    def _iter_supported_files(root: Path) -> Iterator[Path]:
        for path in sorted(root.rglob("*"), key=lambda item: item.as_posix().casefold()):
            if path.is_symlink() or not path.is_file():
                continue
            if path.suffix.casefold() not in _FOLDER_SCAN_EXTENSIONS:
                continue
            try:
                resolved = path.resolve()
                resolved.relative_to(root)
            except (OSError, ValueError):
                continue
            yield resolved


def _metadata_hash(file_size: int, modified_ns: int) -> str:
    return sha256(f"metadata:{file_size}:{modified_ns}".encode()).hexdigest()
