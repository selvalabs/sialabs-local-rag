# Validation

## Scope

This document records execution paths verified for the public showcase snapshot. It distinguishes deterministic regression evidence, local container evidence and optional real-model smoke runs. It does not claim enterprise readiness or universal RAG quality.

## Validated paths

| Path | Runtime | Result |
| --- | --- | --- |
| Repository validation | Mock chat + hash embeddings | Backend tests, Ruff, Mypy, OpenAPI export, frontend audit/tests/typecheck/build and Compose checks pass |
| Text/Markdown/PDF/Office/image paths | Application pipeline | Parsing, bounded chunking, storage and source metadata are covered by tests |
| Dense and hybrid evaluation | Hash provider | Versioned corpus reports document/evidence recall, MRR, category metrics and no-answer accuracy |
| Retrieval scale benchmark | Hash provider | Versioned local Windows measurements for 1k, 5k, 10k, 25k and 50k chunks; use as a machine-specific decision aid |
| Browser UI checks | Deterministic local stack | Two mock-driven Playwright UI tests cover the workspace shell and a mocked ingest/chat interaction |
| Integrated browser E2E | Mock chat + hash embeddings + SQLite | Playwright covers React → FastAPI → SQLite → hash retrieval → response with source; this CI path does not require Ollama or a GPU |
| Ollama chat/embedding smoke | Local Ollama | Optional direct model checks when configured models are installed |
| Full local RAG | Ollama/Gemma + EmbeddingGemma | Optional environment-dependent ingestion, retrieval, answer and source-attribution path |
| Container build | Pinned Docker images | Backend and frontend images build with frozen lockfiles and non-root runtime identities |

## Deterministic validation

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate-local.ps1
```

The deterministic path does not require Ollama or downloaded model files. The retrieval corpus lives under backend/evaluation/; run dense and hybrid reports directly with:

```powershell
cd backend
uv run python -m sialabs_local_rag.evaluation --provider hash --mode dense
uv run python -m sialabs_local_rag.evaluation --provider hash --mode hybrid
```

Reports expose aggregate and category metrics, including document hit@1, evidence recall, MRR, query success and negative no-answer accuracy. The corpus is a project regression benchmark, not a universal benchmark.

The scale harness and the latest local result are versioned at
`backend/benchmarks/retrieval_scale.py` and
`backend/benchmarks/results/retrieval-scale-local.json`. The result records the
machine metadata and is not a latency SLO for other environments.

## Optional Ollama validation

```powershell
$env:OLLAMA_CHAT_MODEL = "gemma4:e2b"
$env:OLLAMA_EMBED_MODEL = "embeddinggemma"
powershell -ExecutionPolicy Bypass -File .\scripts\check-ollama.ps1 -RunSmokeRequests
```

A real-model run depends on local hardware, model availability and warm/cold state. Its latency is evidence for that environment, not a general performance claim.

## Confirmed boundaries

- local SQLite data is not encrypted at rest;
- no public deployment or multi-user authorization is validated;
- optional OCR depends on local packages and Tesseract;
- Playwright browser execution is checked in CI and locally when a browser is installed; the mock-driven UI tests and integrated E2E are distinct evidence paths;
- the integrated E2E validates the application wiring and deterministic source return, not universal answer quality or production-scale performance;
- deterministic hash evaluation is not semantic embedding quality;
- retrieval and retrieval-scale reports do not grade generated LLM groundedness universally.
