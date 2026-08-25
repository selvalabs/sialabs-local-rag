# Technical case study: making local RAG reviewable

## Problem

The project needed to demonstrate a useful RAG workflow without requiring a
cloud account, while remaining honest about local storage, model quality and
scale limits. The public showcase therefore treats reproducibility and
evidence as product features, not only maintenance concerns.

## Public release provenance

Development history, intermediate branches and experiments are maintained in a
private engineering repository. This public repository is the curated,
sanitized showcase release: the source, documentation, reproducible validation
and CI configuration needed to review the released system are present here,
without publishing private development artifacts.

## Architecture and choices

The frontend is a React/Vite application backed by FastAPI, SQLite and an
optional Ollama runtime. Documents are parsed locally, chunked, embedded and
retrieved before the chat provider receives a grounded prompt. Hash embeddings
and a mock chat provider make the complete path deterministic in CI; Ollama and
Gemma remain an optional local quality path.

SQLite and transparent Python retrieval were retained because the target is a
single-user local application. The scale benchmark records when that trade-off
stops being appropriate instead of introducing a vector extension without
measurements.

## Reliability work

The implementation is organized as focused engineering changes. Local gates cover
frozen dependencies, container builds, API/OpenAPI contracts, deterministic RAG
evaluation, adversarial prompt framing, bounded uploads, browser smoke coverage,
accessibility checks and documented security boundaries.

The deterministic corpus is synthetic and versioned. It spans direct questions,
paraphrases, exact codes, multi-chunk and multi-document retrieval, follow-ups,
language changes, no-answer cases and topic switches. Its metrics are a project
regression signal, not a universal benchmark.

Groundedness and citation checks are also available as a deterministic lexical
regression harness. It reports claim support and explicit source-ID coverage,
while documenting that it is not a semantic LLM judge. See
[`evidence/groundedness-citation-regression.md`](evidence/groundedness-citation-regression.md).

## Security boundary

The application is designed for trusted local use. SQLite and browser-profile
data are not encrypted by the application, there is no multi-user
authentication, and the backend must not be exposed publicly without an
additional security layer. Uploaded and retrieved document text is treated as
untrusted data; upload bounds, browser mutation guards and prompt delimiters
reduce risk without claiming immunity.

## Reproduction

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate-local.ps1
cd backend
uv run python -m sialabs_local_rag.evaluation --provider hash --mode hybrid
cd ..\frontend
npm run test
npm run typecheck
npm run build
```

If a future release adds artifact signing or SBOM generation, those outputs
should be attached together with the exact local validation result for its tag.
