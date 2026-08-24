# Testing

## Objective

Validate local application behavior in CI without requiring Ollama, a GPU,
downloaded models or an installed OCR runtime.

## Test layers

### Backend unit and service tests

- text/structure-aware chunking;
- vector math and provider/service orchestration;
- SQLite migrations and storage behavior;
- embedding-index lifecycle and local data retention;
- dense/hybrid retrieval and conversational retrieval;
- deterministic retrieval-quality and structure-sensitive evaluation;
- DOCX/PPTX/XLSX parsers using generated in-memory OOXML packages;
- optional OCR capability/error handling with mocked local runtimes.

### API tests

API coverage includes document creation, duplicate handling, chat/retrieval sources,
Markdown, multipage text PDF, DOCX, PPTX and XLSX ingestion, structured source
locators, unsupported files and actionable missing-OCR behavior.

### Frontend checks

- `npm audit --audit-level=high`;
- Vitest unit tests;
- TypeScript typecheck;
- production build.

Playwright keeps the two mock-driven UI tests and adds a deterministic integrated
E2E test. The integrated path exercises React → FastAPI → SQLite → hash retrieval
→ response with source. It uses the mock chat and hash embedding providers, so it
does not require Ollama or a GPU; the UI tests and the integrated test are reported
as separate kinds of evidence.

The backend and frontend also export/regenerate the OpenAPI artifacts and fail
when the generated files differ from the committed versions.

The Windows CI job runs the contract-focused Pester suite under
`scripts/tests`.

### Configuration checks

- Docker Compose configuration validation.

## Complete local validation

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate-local.ps1
```

The base validation path intentionally does **not** install OCR packages or require
Tesseract.

## Individual commands

Backend:

```powershell
cd backend
uv sync --dev
uv run ruff check .
uv run pytest
uv run mypy src
```

Backend with coverage:

```powershell
uv run --with pytest-cov pytest `
  --cov=sialabs_local_rag `
  --cov-report=term-missing `
  --cov-report=xml
```

Frontend:

```powershell
cd frontend
npm ci
npm audit --audit-level=high
npm run test
npm run typecheck
npm run generate:api
npm run build
```

Docker Compose:

```powershell
docker compose config
```

## Retrieval evaluation

The fixed repository-safe retrieval corpus lives under `backend/evaluation/`.

```powershell
cd backend
uv run python -m sialabs_local_rag.evaluation --provider hash --mode dense
uv run python -m sialabs_local_rag.evaluation --provider hash --mode hybrid
```

Real EmbeddingGemma evaluation is optional when Ollama is available locally.
See `RETRIEVAL_EVALUATION.md` for metrics and update rules.

## Office fixture strategy

Office parser tests do not store large binary documents in Git. Tests construct
minimal DOCX/PPTX/XLSX ZIP/XML packages in memory with exact marker values such as
`DOCX-77`, `PPTX-88` and `XLSX-99`.

The API tests then exercise the complete path:

1. upload generated Office bytes;
2. parse structure;
3. chunk and embed;
4. persist source metadata;
5. retrieve by exact evidence;
6. assert the expected section/slide/sheet/range citation.

This keeps fixtures inspectable, deterministic and repository-safe.

## Optional local OCR validation

Ordinary CI does not install Pillow, PyMuPDF, pytesseract or Tesseract. Instead,
unit tests inject small fake OCR/image/PDF runtimes and verify:

- image OCR creates an `image:*` locator;
- scanned-PDF OCR preserves page numbers/locators;
- a textless valid PDF routes to the OCR fallback;
- missing optional dependencies produce an actionable error;
- the HTTP API exposes missing OCR as `503` rather than a generic parse failure.

For a manual real OCR smoke test, install the optional Python packages:

```powershell
cd backend
uv pip install -r requirements-ocr.txt
```

Install Tesseract OCR locally and ensure the `tesseract` command is available on
`PATH`, then upload a small scanned PDF or image through the local API/UI.

Real OCR accuracy is environment/language dependent, so it is deliberately not a
mandatory deterministic CI gate.

## CI strategy

CI uses deterministic mock/hash providers and generated document fixtures. The
backend job runs Ruff, pytest with coverage, mypy and an OpenAPI export drift
check. The frontend job runs npm audit, Vitest, OpenAPI client generation,
TypeScript typecheck and a production build. A Windows job runs the Pester
contract suite. The container job also installs Chromium and runs the two
mock-driven UI tests plus the integrated React → FastAPI → SQLite → hash retrieval
→ response/source E2E path.

To run the browser suite locally, start the deterministic backend and frontend on
`http://127.0.0.1:8000` and `http://127.0.0.1:5173`, then run:

```powershell
cd frontend
npm run test:e2e
```

Coverage remains informational; no global percentage threshold is enforced yet.

## Current gaps

- Playwright browser binaries are not downloaded by ordinary dependency install;
  run `npx playwright install chromium` before the browser suite when needed.
- No enforced minimum coverage threshold.
- The retrieval corpus is intentionally small and project-specific.
- No load/sustained-latency benchmark.
- No mandatory real-Tesseract OCR accuracy benchmark in CI.
- No pixel-perfect Office layout/table reconstruction tests; those are outside the
  current ingestion scope.
