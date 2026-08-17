# Testing

## Objective

Validate application behavior locally and in CI without requiring Ollama, a GPU or downloaded model files.

## Test layers

### Backend unit and service tests

- text normalization and chunking;
- vector normalization and cosine similarity;
- provider and service orchestration;
- local storage behavior;
- embedding-index lifecycle and local data retention;
- deterministic retrieval-quality baseline.

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

Backend with coverage:

```powershell
cd backend
uv run --with pytest-cov pytest --cov=sialabs_local_rag --cov-report=term-missing --cov-report=xml
```

This prints a terminal coverage summary and writes `backend/coverage.xml` for CI artifacts or later integration with coverage reporting services.

No minimum coverage threshold is enforced yet. The current goal is to make coverage visible before deciding a realistic threshold.

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

## Retrieval quality evaluation

The repository includes a fixed corpus, expected evidence and negative/no-answer cases under `backend/evaluation/`.

Deterministic CI-compatible run:

```powershell
cd backend
uv run python -m sialabs_local_rag.evaluation --provider hash
```

Optional real local embedding run:

```powershell
$env:OLLAMA_EMBED_MODEL = "embeddinggemma"
uv run python -m sialabs_local_rag.evaluation --provider ollama
```

The pytest suite recomputes the deterministic hash evaluation and compares it with the recorded baseline. This makes retrieval behavior changes explicit in future PRs.

See [`RETRIEVAL_EVALUATION.md`](RETRIEVAL_EVALUATION.md) for the corpus design, metrics, current baseline and update rules.

## CI strategy

CI uses deterministic mock/hash providers so validation does not depend on local hardware or downloaded model availability. Real Ollama execution is validated separately through explicit local smoke, end-to-end and retrieval-evaluation checks.

The backend CI job runs pytest with coverage and uploads `coverage.xml` as a workflow artifact. Coverage is informational for now and does not fail the build by percentage.

## Local AI validation

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check-ollama.ps1 -RunSmokeRequests
```

See [`VALIDATION.md`](VALIDATION.md) for the validated model combinations and scope.

## Current gaps

- No browser-driven end-to-end test suite.
- No enforced minimum coverage threshold.
- The retrieval evaluation corpus is intentionally small and project-specific, not a general benchmark.
- No load or sustained-latency benchmark.
- No automated OCR or scanned-PDF test path because OCR is unsupported.
