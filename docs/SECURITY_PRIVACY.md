# Security and Privacy

## Local-first principle

Document content remains in the user's local environment by default. The primary
application path does not require an external LLM, embedding API, Office parser or
OCR service.

## Persisted data

The local SQLite database stores document metadata, extracted text chunks,
embeddings, lightweight source-location metadata and local chat traces.

Source metadata can include page, section, slide, sheet and cell-range locators.
New chat trace metadata does **not** duplicate retrieved chunk text. The browser
persists only lightweight conversation messages, not detailed retrieved-source
objects.

Anyone with access to the SQLite database or browser profile may be able to read
remaining locally persisted content. SQLite storage is not encrypted by the app.

## Deletion semantics

- **Clear chat** removes backend traces and browser chat history.
- **Delete document** removes the document/chunks and clears backend chat traces.
- **Reset embedding index** removes indexed documents/chunks, embedding signature
  and backend chat traces.
- **Full local data reset** removes documents, chunks, embedding signature and
  backend chat traces.

The destructive full-reset endpoint accepts loopback clients only in normal runtime
and requires `X-Confirm-Local-Data-Reset: delete-all`.

## Public repository safety

The repository may contain source code, deterministic generated test fixtures,
document-format XML fixtures and configuration examples. It must not contain real
user/customer documents, local databases, credentials, downloaded models or local
OCR output from private documents.

## Security boundary

The application is designed for trusted local use. It does not provide built-in
multi-user authentication, per-user authorization, encrypted database storage,
tenant isolation or hardened public-deployment defaults.

Do not expose the backend, launcher or Ollama directly to the public internet
without authentication, network controls and a deployment-specific security
review.

## File handling and untrusted documents

Uploaded content is untrusted data. Supported file extensions are allow-listed and
the backend enforces a 10 MB request limit.

Retrieved document text is also treated as untrusted data. The answer prompt
delimits each source and instructs the local model not to follow commands found
inside it or disclose system instructions. This reduces prompt-injection impact;
it does not make arbitrary document content trustworthy or claim immunity.

### OOXML Office packages

DOCX, PPTX and XLSX are ZIP-based OOXML packages and are parsed locally with the
Python standard library. The parsers read XML parts directly and do not execute
macros or embedded code.

To reduce resource-exhaustion risk from compressed packages, the parsers enforce
bounds including:

- at most 5,000 ZIP entries;
- at most 50 MB total uncompressed package data;
- at most 20,000 DOCX paragraphs;
- at most 200 PPTX slides;
- at most 100 XLSX sheets;
- at most 50,000 non-empty XLSX cells.

Complex embedded objects, macros, arbitrary package relationships and pixel-perfect
Office rendering are not executed or reproduced.

### PDF and OCR

Selectable PDF text is extracted locally with the base dependency path. Text PDFs
are limited to 100 pages per upload.

If a valid PDF contains no selectable text, the application may use the optional
local OCR capability. Image uploads also require this optional capability. OCR is
**never silently sent to a cloud service**.

Optional OCR requires local Python packages from `backend/requirements-ocr.txt`
and a local Tesseract executable. Scanned-PDF OCR is limited to 50 pages. OCR text
is then processed through the same local chunk/index pipeline as other extracted
text.

If OCR dependencies or Tesseract are unavailable, the API returns an actionable
error instead of falling back to a remote provider.

OCR is inherently imperfect. Extracted OCR text must be treated as untrusted and
potentially inaccurate input, especially before using it for high-stakes decisions.

## Prompt/data boundary

Retrieved text and conversation content are data, not instructions with higher
privilege than the application's system policy. Conversation history is explicitly
labeled as non-evidence; factual claims should be grounded in retrieved sources.

## Recommended hardening for broader deployment

- Place the application behind an authenticated reverse proxy.
- Add authorization for document and administrative endpoints.
- Add rate limits and structured audit logs.
- Define backup, deletion and retention procedures.
- Encrypt sensitive storage where required.
- Add dependency/secret scanning.
- Consider sandboxing or process isolation for hostile document-processing
  workloads before accepting uploads from untrusted remote users.
