from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from sialabs_local_rag.collection_scan import CollectionScanner
from sialabs_local_rag.collection_store import CollectionStore
from sialabs_local_rag.database import Database
from sialabs_local_rag.providers import create_embedding_provider
from sialabs_local_rag.settings import Settings
from sialabs_local_rag.storage import Storage


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage trusted local folder collections for SoberanIA Labs Local RAG."
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    register = subcommands.add_parser("register", help="Register a trusted local folder.")
    register.add_argument("--name", required=True)
    register.add_argument("--path", type=Path, required=True)
    register.add_argument(
        "--missing-policy",
        choices=("mark", "remove"),
        default="mark",
        help="What a later rescan does when a previously indexed file disappears.",
    )

    subcommands.add_parser("list", help="List registered local collections.")

    scan = subcommands.add_parser("scan", help="Explicitly rescan a registered folder.")
    scan.add_argument("collection_id")
    scan.add_argument("--dry-run", action="store_true")
    scan.add_argument(
        "--missing-policy",
        choices=("mark", "remove"),
        default=None,
        help="Override the collection policy for this scan only.",
    )
    return parser


def _open_store(settings: Settings) -> tuple[Database, Storage, CollectionStore]:
    database = Database(settings.database_url)
    database.init_schema()
    storage = Storage(database)
    return database, storage, CollectionStore(database)


async def _run(args: argparse.Namespace) -> int:
    settings = Settings()
    database, storage, collections = _open_store(settings)

    if args.command == "register":
        record = collections.register_folder(
            name=str(args.name),
            root_path=Path(args.path),
            missing_policy=str(args.missing_policy),
        )
        print(f"Registered collection {record.id}: {record.name}")
        print(f"Folder: {record.root_path}")
        print(f"Missing-file policy: {record.missing_policy}")
        print(f"Next: python -m sialabs_local_rag.collection_cli scan {record.id}")
        return 0

    if args.command == "list":
        for record in collections.list_collections():
            active, missing, errors = collections.collection_counts(record.id)
            location = record.root_path or "(manual/default collection)"
            print(
                f"{record.id}\t{record.name}\t{record.kind}\t"
                f"active={active} missing={missing} errors={errors}\t{location}"
            )
        return 0

    if args.command == "scan":
        scanner = CollectionScanner(
            database=database,
            storage=storage,
            embedding_provider=create_embedding_provider(settings),
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        result = await scanner.scan(
            str(args.collection_id),
            dry_run=bool(args.dry_run),
            missing_policy=(
                str(args.missing_policy) if args.missing_policy is not None else None
            ),
        )
        mode = "DRY RUN" if result.dry_run else "APPLIED"
        print(f"Collection scan: {mode}")
        print(f"collection={result.collection_id} policy={result.missing_policy}")
        print(
            " ".join(
                [
                    f"discovered={result.discovered}",
                    f"added={result.added}",
                    f"changed={result.changed}",
                    f"reused={result.reused}",
                    f"unchanged={result.unchanged}",
                    f"missing={result.missing}",
                    f"errors={result.errors}",
                    f"orphan_docs_deleted={result.orphan_documents_deleted}",
                ]
            )
        )
        return 0 if result.errors == 0 else 2

    return 2


def main() -> int:
    args = build_parser().parse_args()
    return asyncio.run(_run(args))


if __name__ == "__main__":
    raise SystemExit(main())
