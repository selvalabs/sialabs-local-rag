# Local folder collections

Collections let one local SQLite index be queried as separate trusted workspaces
without duplicating embeddings for identical document content.

The initial implementation is deliberately **explicit**, not a background watcher:
you register a trusted folder locally, run an initial scan, and rescan when you want
the index refreshed.

## Security boundary

Filesystem paths are accepted only by the local collection CLI. The HTTP API does
not expose a `POST /collections` path-registration endpoint and does not return
registered `root_path` values.

The browser/API can see safe collection identifiers, names, source counts and last
scan time, then submit a `collection_id` to chat. It cannot ask the backend to read
an arbitrary path.

## Register a folder

From `backend/` on Windows PowerShell:

```powershell
uv run python -m sialabs_local_rag.collection_cli register `
  --name "Project docs" `
  --path "C:\Users\you\Documents\project-docs"
```

Linux/macOS shell:

```bash
uv run python -m sialabs_local_rag.collection_cli register \
  --name "Project docs" \
  --path "$HOME/Documents/project-docs"
```

The folder must already exist. Registration stores the resolved local path only in
the local SQLite database and returns a collection ID.

A registered root path is unique. Registering the same resolved folder twice is
rejected rather than creating ambiguous duplicate workspaces.

## Initial scan

Run the collection ID returned by registration:

```powershell
uv run python -m sialabs_local_rag.collection_cli scan <collection-id>
```

The scanner recursively considers supported document formats:

- TXT;
- Markdown;
- selectable-text PDF;
- DOCX;
- PPTX;
- XLSX.

A scanned PDF that requires OCR uses the optional local OCR capability when it is
installed. If OCR is unavailable, that source is recorded as an explicit error; the
scanner does not send the document to a remote OCR service.

Image files are not included in folder scans in this stage. They remain available
through explicit upload when optional OCR is installed.

## Incremental rescans

The scanner hashes raw file bytes before parsing or embedding them.

On a later scan:

- unchanged SHA-256 → source is touched as active, **no parse and no embedding**;
- new file → parsed/indexed and attached to the collection;
- changed file → only that source is reprocessed;
- identical parsed content already indexed elsewhere → the existing document/vector
  index is reused instead of embedding another copy;
- unreadable/invalid source → marked `error` with a local diagnostic;
- disappeared source → handled by the configured missing-file policy.

A document is deleted only after no active collection source still references it.
This allows identical content to be shared safely across multiple collections.

## Dry run

Preview discovered changes without parsing, embedding or mutating the database:

```powershell
uv run python -m sialabs_local_rag.collection_cli scan <collection-id> --dry-run
```

The summary reports discovered, added, changed, reused, unchanged, missing and error
counts. A dry run leaves collection/source timestamps and vector data unchanged.

## Removed-file policy

Registration defaults to:

```text
--missing-policy mark
```

`mark` keeps the source record for visibility but removes it from active retrieval.
Its former document is deleted only if nothing else actively references that
document.

To remove the source record entirely when a file disappears:

```powershell
uv run python -m sialabs_local_rag.collection_cli register `
  --name "Ephemeral docs" `
  --path "C:\docs\ephemeral" `
  --missing-policy remove
```

A one-off scan may override the stored policy:

```powershell
uv run python -m sialabs_local_rag.collection_cli scan <collection-id> `
  --missing-policy remove
```

## List local collections

```powershell
uv run python -m sialabs_local_rag.collection_cli list
```

The trusted CLI includes each collection's local path. In contrast,
`GET /api/collections` intentionally returns only safe metadata:

- ID and display name;
- `manual` or `folder` kind;
- active/missing/error counts;
- last scan timestamp.

## Query one collection

The chat API accepts an optional collection ID:

```json
{
  "question": "What does this workspace say about recovery?",
  "collection_id": "<collection-id>",
  "top_k": 5
}
```

Collection filtering happens **before ranking** in both retrieval channels:

- dense cosine candidates are read only from active documents in that collection;
- FTS5 lexical candidates use the same active collection constraint;
- RRF therefore cannot reintroduce a chunk from a different workspace.

Returned sources and the chat response echo the selected `collection_id` for
inspection.

Omitting `collection_id` preserves the existing full-base behavior and may search
all indexed documents.

## Default collection

Schema migration v7 creates the built-in collection:

```text
default — Local base
```

Existing documents are backfilled into it. Documents added through paste or normal
file upload are attached to `default` automatically.

Folder-scanned documents are attached to their registered folder collection and
are not silently added to `default`.

## Limits and non-goals

The first folder-collection implementation intentionally does **not** include:

- continuous filesystem watching;
- remote/network filesystem registration through HTTP;
- cloud drive sync;
- automatic periodic rescans;
- vector duplication per collection.

Current scanner safety bounds include at most 5,000 supported files per scan and a
10 MB per-file limit, in addition to the parser-specific PDF/Office/OCR bounds.
Symlinks are skipped.

A later watcher/daemon should reuse the same hash/source registry instead of
creating a second indexing lifecycle.
