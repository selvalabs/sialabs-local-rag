# Demo Guide

This guide provides a reproducible local path for running, inspecting and validating SoberanIA Labs Local RAG.

## 1. Start the backend

From the repository root:

~~~powershell
cd backend
uv sync --dev
uv run uvicorn sialabs_local_rag.main:app --reload --host 0.0.0.0 --port 8000
~~~

Expected endpoints:

- API: `http://localhost:8000`
- Swagger/OpenAPI: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

## 2. Start the frontend

Open another terminal:

~~~powershell
cd frontend
npm ci
npm run dev
~~~

Open `http://localhost:5173`.

## 3. Seed a reproducible document

Open a third terminal from the repository root:

~~~powershell
powershell -ExecutionPolicy Bypass -File .\scripts\seed-demo.ps1
~~~

The script checks API health, posts `examples/sialabs-demo-context.md` to `/api/documents` and prints the indexed document metadata.

## 4. Ask questions

Try:

~~~text
What is SoberanIA Labs Local RAG?
~~~

~~~text
How are documents and embeddings stored?
~~~

~~~text
How does the application return grounded sources?
~~~

~~~text
What is the difference between Ollama mode and lightweight validation mode?
~~~

The answer should include one or more sources from the seeded document.

## 5. Run repository validation

~~~powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate-local.ps1
~~~

Expected checks:

- backend lint and formatting checks pass;
- backend tests pass;
- backend typecheck passes;
- frontend typecheck passes;
- frontend production build passes;
- Docker Compose configuration is valid.

## 6. Run with Ollama

Copy `.env.example` to `.env`, then configure:

~~~env
LLM_PROVIDER=ollama
EMBEDDING_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=gemma4:e2b
OLLAMA_EMBED_MODEL=embeddinggemma
~~~

Make sure Ollama is running and the configured models are installed. Validate direct model requests with:

~~~powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check-ollama.ps1 -RunSmokeRequests
~~~

## What the demo validates

- document ingestion and parsing;
- chunking and local persistence;
- embedding generation;
- cosine-similarity retrieval;
- answer generation with retrieved context;
- source attribution;
- provider and model metadata;
- deterministic repository validation.

## PDF upload

Use a PDF that contains selectable text, not a scanned image. Upload it through the file upload card, wait for indexing and ask a question about its content.

OCR for scanned PDFs is not supported.
