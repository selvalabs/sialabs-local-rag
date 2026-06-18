# Demo Guide

This guide explains how to run a reproducible local demo of SIALabs Local RAG.

The goal is to make the project easy to evaluate in a portfolio review, interview or technical walkthrough.

## 1. Start the backend

From the repository root:

~~~powershell
cd backend
uv sync --dev
uv run uvicorn sialabs_local_rag.main:app --reload --host 0.0.0.0 --port 8000
~~~

Expected API URLs:

- API: http://localhost:8000
- Swagger/OpenAPI: http://localhost:8000/docs
- Healthcheck: http://localhost:8000/health

## 2. Start the frontend

Open another terminal:

~~~powershell
cd frontend
npm ci
npm run dev
~~~

Open:

~~~text
http://localhost:5173
~~~

## 3. Seed the demo document

Open a third terminal from the repository root:

~~~powershell
powershell -ExecutionPolicy Bypass -File .\scripts\seed-demo.ps1
~~~

Expected result:

- the script checks `/health`;
- posts `examples/sialabs-demo-context.md` to `/api/documents`;
- returns the created document metadata.

## 4. Ask demo questions

In the chat UI, try:

~~~text
What is SIALabs Local RAG?
~~~

~~~text
Which technologies are used in this project?
~~~

~~~text
Why does the project support mock/hash mode?
~~~

~~~text
How does the local AI mode work?
~~~

~~~text
What skills does this project demonstrate?
~~~

The answer should include sources from the seeded document.

## 5. Validate the repository

From the repository root:

~~~powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate-local.ps1
~~~

Expected result:

- backend lint passes;
- backend tests pass;
- backend typecheck passes;
- frontend typecheck passes;
- frontend build passes;
- Docker Compose config is valid.

## 6. Optional Ollama mode

The default demo uses mock/hash providers so it can run without local models.

To use Ollama, copy `.env.example` to `.env` and set:

~~~env
LLM_PROVIDER=ollama
EMBEDDING_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=gemma4
OLLAMA_EMBED_MODEL=embeddinggemma
~~~

Then make sure Ollama is running and the selected models are available.

## Portfolio talking points

This demo shows:

- full stack implementation;
- local-first product thinking;
- RAG pipeline design;
- API integration;
- SQLite persistence;
- deterministic CI-friendly providers;
- optional local model runtime;
- documentation and GitHub workflow discipline.

<!-- PDF_INGESTION_SECTION_START -->
## PDF upload demo

The demo can also be tested with a text-based PDF.

Use a PDF that contains selectable text, not a scanned image. Upload it through the file upload card and ask a question about its content.

Current limitation: OCR for scanned PDFs is intentionally out of scope for this MVP.
<!-- PDF_INGESTION_SECTION_END -->
