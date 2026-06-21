# Testing

## Objective

Validate application behavior locally and in CI without requiring Ollama, a GPU or downloaded model files.

## Test layers

### Backend unit and service tests

- text normalization and chunking;
- vector normalization and cosine similarity;
- provider and service orchestration;
- local storage behavior.

### API tests

- health check;
- document creation and duplicate handling;
- chat responses with retrieved sources;
- Markdown upload;
- text-based PDF upload;
- unreadable PDF rejection;
- unsupported extension rejection.

### Frontend checks

- TypeScript typecheck;
- production build.

### Configuration checks

- Docker Compose configuration validation.

## Complete local validation

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate-local.ps1
```

The script performs backend dependency resolution, Ruff checks, pytest, mypy, frontend installation, TypeScript typecheck, frontend build and Docker Compose configuration validation.

## Individual commands

Backend:

```powershell
cd backend
uv sync --dev
uv run ruff check . --fix
uv run ruff check .
uv run pytest
uv run mypy src
```

Frontend:

```powershell
cd frontend
npm ci
npm run typecheck
npm run build
```

Docker Compose:

```powershell
docker compose config
```

## CI strategy

CI uses deterministic mock/hash providers so validation does not depend on local hardware or downloaded model availability. Real Ollama execution is validated separately through explicit local smoke and end-to-end checks.

## Local AI validation

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check-ollama.ps1 -RunSmokeRequests
```

See [`VALIDATION.md`](VALIDATION.md) for the validated model combinations and scope.

## Current gaps

- No browser-driven end-to-end test suite.
- No retrieval-quality benchmark dataset.
- No load or sustained-latency benchmark.
- No automated OCR or scanned-PDF test path because OCR is unsupported.
