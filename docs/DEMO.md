# Demo Guide

This guide demonstrates the current local product and its engineering evidence without requiring private documents.

## 1. Start deterministic local services

Backend:

```powershell
$env:LLM_PROVIDER = "mock"
$env:EMBEDDING_PROVIDER = "hash"
cd backend
uv sync --dev
uv run uvicorn sialabs_local_rag.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd frontend
npm ci
npm run dev
```

Open http://127.0.0.1:5173.

## 2. Seed synthetic material

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\seed-demo.ps1
```

Use synthetic Markdown as the baseline, then demonstrate representative PDF, DOCX, PPTX and XLSX fixtures when available. Optional image/OCR fixtures require the local OCR dependencies described in docs/TESTING.md.

## 3. Product walkthrough

Show these scenes in order:

1. Health and collection: confirm the API is reachable, select a collection and show active/missing/error counters.
2. Heterogeneous ingestion: upload or seed documents from different supported formats and wait for index status ready.
3. Grounded answer: ask a question whose evidence comes from a specific page, section, slide, sheet or cell range; expand the structured source card and its source ID.
4. Exact-term rescue: ask for a code or identifier that benefits from the FTS5 lexical channel; show hybrid mode and channel metadata.
5. Follow-up: ask a short follow-up and show that typed conversation context is separate from retrieved evidence.
6. No-answer: ask about an absent fact and show the relevance gate refusing to invent a source.
7. Index lifecycle: show the index health/reindex state and reset semantics.
8. Engineering evidence: open the evaluation report, case study and local validation output.

Example questions:

```text
What decision is documented on the recovery procedure?
Which exact code appears in the operations notes?
What was the deadline for that item?
What is a fact that is not present in these documents?
```

## 4. Ollama variant

```powershell
ollama pull gemma4:e2b
ollama pull embeddinggemma
$env:LLM_PROVIDER = "ollama"
$env:EMBEDDING_PROVIDER = "ollama"
$env:OLLAMA_BASE_URL = "http://127.0.0.1:11434"
$env:OLLAMA_CHAT_MODEL = "gemma4:e2b"
$env:OLLAMA_EMBED_MODEL = "embeddinggemma"
```

Run the same walkthrough and state clearly that model latency and answer quality depend on local hardware and model state.

## 5. Validation evidence

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate-local.ps1
```

For retrieval evidence, compare dense and hybrid evaluation reports and include category metrics, locators and no-answer outcomes. For capture guidance, use docs/DEMO_PACK.md. Do not use real client or personal documents.
