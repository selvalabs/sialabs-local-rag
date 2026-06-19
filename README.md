# SIALabs Local RAG

Local-first RAG application for private document Q&A with FastAPI, React, SQLite and optional local AI through Ollama/Gemma.

This repository is a technical portfolio project. It demonstrates how to build, validate and document a small but complete AI product using a professional GitHub workflow.

## What this project demonstrates

- Full stack development with React, TypeScript, Python and FastAPI.
- REST API design with typed request/response contracts.
- Local-first data storage with SQLite.
- Retrieval-augmented generation with ingestion, chunking, embeddings, retrieval and source-grounded answers.
- Optional local AI runtime using Ollama, Gemma and EmbeddingGemma.
- CI-friendly mock/hash providers for deterministic tests.
- Engineering workflow with issues, branches, Conventional Commits, pull requests, CI and validation evidence.

## Current status

The MVP is implemented and validated.

Validated paths:

| Path | Status |
| --- | --- |
| Mock/hash mode for CI and demo | Validated |
| Text and Markdown ingestion | Validated |
| Text-based PDF ingestion | Validated |
| Ollama smoke test | Validated |
| Gemma 3 local runtime | Validated with `gemma3:4b` |
| Gemma 4 local runtime | Validated with `gemma4:e2b` |
| Full local Ollama RAG E2E flow | Validated with `gemma3:4b` + `embeddinggemma` |

This is not presented as a production SaaS. It is a local-first portfolio MVP focused on architecture, reproducibility, privacy and technical evidence.

## Evidence

| Evidence | Document |
| --- | --- |
| Recruiter-facing technical evidence | `docs/RECRUITER_EVIDENCE.md` |
| Architecture | `docs/ARCHITECTURE.md` |
| API contract | `docs/API.md` |
| Testing strategy | `docs/TESTING.md` |
| Security and privacy notes | `docs/SECURITY_PRIVACY.md` |
| Local AI design | `docs/LOCAL_AI.md` |
| Reproducible demo flow | `docs/DEMO.md` |
| Ollama smoke test | `docs/OLLAMA_SMOKE_TEST.md` |
| Real Ollama validation | `docs/REAL_OLLAMA_VALIDATION.md` |
| Full Ollama RAG E2E validation | `docs/E2E_OLLAMA_RAG_FLOW.md` |
| Gemma 4 validation | `docs/GEMMA4_OLLAMA_VALIDATION.md` |
| Roadmap | `docs/ROADMAP.md` |
| GitHub workflow | `docs/GITHUB_WORKFLOW.md` |

## Stack

| Layer | Technology |
| --- | --- |
| Frontend | React, TypeScript, Vite, responsive CSS |
| Backend | FastAPI, Pydantic, SQLite, httpx |
| RAG | chunking, embeddings, cosine similarity, source attribution |
| Local AI | Ollama, Gemma, EmbeddingGemma |
| Tests | pytest, FastAPI TestClient, TypeScript typecheck |
| Quality | Ruff, mypy, frontend build |
| Infra | Docker Compose, GitHub Actions |

## Execution modes

The backend supports two execution modes.

### 1. Mock/hash mode

Default mode for CI, quick demos and machines without Ollama:

~~~env
LLM_PROVIDER=mock
EMBEDDING_PROVIDER=hash
~~~

This keeps the project easy to validate without GPU, local models or internet access after dependencies are installed.

### 2. Local AI mode with Ollama

Validated local AI models:

~~~env
LLM_PROVIDER=ollama
EMBEDDING_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=gemma4:e2b
OLLAMA_EMBED_MODEL=embeddinggemma
~~~

Alternative lightweight validated chat model:

~~~env
OLLAMA_CHAT_MODEL=gemma3:4b
~~~

## Quick start without Ollama

Terminal 1 — backend:

~~~powershell
cd backend
uv sync --dev
uv run uvicorn sialabs_local_rag.main:app --reload --host 0.0.0.0 --port 8000
~~~

Terminal 2 — frontend:

~~~powershell
cd frontend
npm ci
npm run dev
~~~

Open:

- Frontend: `http://localhost:5173`
- API: `http://localhost:8000`
- Swagger/OpenAPI: `http://localhost:8000/docs`

## How to use the app

After the backend and frontend are running:

1. Open `http://localhost:5173` in the browser.
2. Create a document by pasting text, or upload a supported file.
3. Supported file types are `.txt`, `.md`, `.markdown` and text-based `.pdf`.
4. Wait for the document to be indexed into chunks.
5. Ask a question about the uploaded or seeded content.
6. Review the generated answer.
7. Inspect the retrieved sources returned with the answer.
8. Delete documents when they are no longer needed.

The app is designed for local use. Documents and chunks are stored locally in SQLite, and local AI mode can run through Ollama instead of a cloud LLM provider.

## Seed demo content

After starting the backend:

~~~powershell
powershell -ExecutionPolicy Bypass -File .\scripts\seed-demo.ps1
~~~

Suggested question:

~~~text
What is SIALabs Local RAG and what skills does it demonstrate?
~~~

## Run with Ollama and Gemma

Install and start Ollama locally.

Pull validated models:

~~~powershell
ollama pull gemma4:e2b
ollama pull gemma3:4b
ollama pull embeddinggemma
~~~

Run a direct Ollama smoke test:

~~~powershell
$env:OLLAMA_CHAT_MODEL = "gemma4:e2b"
$env:OLLAMA_EMBED_MODEL = "embeddinggemma"

powershell -ExecutionPolicy Bypass -File .\scripts\check-ollama.ps1 -RunSmokeRequests
~~~

Run the backend in Ollama mode:

~~~powershell
$env:LLM_PROVIDER = "ollama"
$env:EMBEDDING_PROVIDER = "ollama"
$env:OLLAMA_BASE_URL = "http://localhost:11434"
$env:OLLAMA_CHAT_MODEL = "gemma4:e2b"
$env:OLLAMA_EMBED_MODEL = "embeddinggemma"

cd backend
uv run uvicorn sialabs_local_rag.main:app --reload --host 0.0.0.0 --port 8000
~~~

## Features

- Create documents from pasted text.
- Upload `.txt`, `.md`, `.markdown` and text-based `.pdf` files.
- Split content into overlapping chunks.
- Generate deterministic hash embeddings for CI/demo mode.
- Generate local embeddings through Ollama in local AI mode.
- Store documents and chunks locally in SQLite.
- Retrieve relevant chunks using cosine similarity.
- Generate contextual answers with source attribution.
- List and delete documents.
- Expose healthcheck and safe public configuration endpoints.
- Run local validation through a single script.

## Validation

Full local validation:

~~~powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate-local.ps1
~~~

This runs:

- backend lock/sync;
- Ruff;
- pytest;
- mypy;
- frontend install;
- TypeScript typecheck;
- frontend build;
- Docker Compose config check.

Ollama validation:

~~~powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check-ollama.ps1 -RunSmokeRequests
~~~

## Known limitations

- SQLite plus Python similarity search is suitable for local demos and small datasets, not large-scale vector search.
- The app has no authentication because it is designed as a local-first MVP.
- It should not be exposed publicly without an additional security layer.
- PDF support is limited to extractable text.
- Scanned PDFs, OCR, image extraction and table reconstruction are out of scope for the MVP.
- Gemma 4 was validated through a direct Ollama smoke test, but the full RAG E2E validation was performed with `gemma3:4b`.
- No performance benchmark is claimed.

## License

MIT. See `LICENSE`.
