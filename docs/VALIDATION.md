# Validation

## Scope

This document summarizes the validated execution paths for SoberanIA Labs Local RAG. It records what was confirmed without claiming performance, retrieval quality or production readiness beyond the tested scope.

## Validated paths

| Path | Runtime | Result |
| --- | --- | --- |
| Repository validation | Mock chat + hash embeddings | Backend lint, tests, typecheck, frontend typecheck/build and Docker Compose configuration pass |
| Text and Markdown ingestion | Application pipeline | Document parsing, chunking, storage and retrieval validated |
| Text-based PDF ingestion | Application pipeline | Extractable text is parsed and indexed; invalid and unreadable PDFs are rejected |
| Ollama chat smoke test | `gemma3:4b` | Direct local chat request succeeded |
| Ollama embedding smoke test | `embeddinggemma` | Direct local embedding request succeeded |
| Full local RAG flow with Gemma 3 | `gemma3:4b` + `embeddinggemma` | Ingestion, embeddings, retrieval, answer generation and source attribution succeeded |
| Gemma 4 chat smoke test | `gemma4:e2b` | Direct local chat request succeeded |
| Full local RAG flow with Gemma 4 | `gemma4:e2b` + `embeddinggemma` | Ingestion, local embeddings, retrieval, Gemma 4 answer generation and source attribution succeeded |

The Gemma 3 local validations were performed on June 18, 2026. The Gemma 4 full RAG validation was performed on June 22, 2026.

## Repository validation

Run the complete deterministic validation suite:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate-local.ps1
```

This path does not require Ollama or downloaded model files.

## Ollama smoke validation

Configure model names if necessary, then run:

```powershell
$env:OLLAMA_CHAT_MODEL = "gemma4:e2b"
$env:OLLAMA_EMBED_MODEL = "embeddinggemma"

powershell -ExecutionPolicy Bypass -File .\scripts\check-ollama.ps1 -RunSmokeRequests
```

The script verifies that:

- the Ollama API is reachable;
- configured models are installed;
- a direct chat request succeeds;
- a direct embedding request succeeds.

## Full local RAG validation

The complete application path has been validated with both `gemma3:4b` and `gemma4:e2b`, using `embeddinggemma` for local embeddings:

1. start the backend with Ollama providers;
2. create or seed a document;
3. generate local document embeddings;
4. submit a RAG question;
5. retrieve relevant chunks;
6. generate an Ollama answer;
7. return source attribution.

## Gemma 4 full RAG validation

The Gemma 4 validation used:

- chat provider: `ollama`;
- chat model: `gemma4:e2b`;
- embedding provider: `ollama`;
- embedding model: `embeddinggemma`;
- validation document title: `Gemma 4 full RAG validation 20260622-095209`;
- validation document size: 545 characters;
- validation document chunks: 1;
- returned provider: `ollama`;
- returned model: `gemma4:e2b`;
- returned sources: 5;
- top returned source: the Gemma 4 validation document;
- top source score: `0.667577`;
- observed latency: `44698 ms`.

The answer correctly referenced local SQLite storage, `embeddinggemma` embeddings, cosine-similarity retrieval and Gemma 4 answer generation through Ollama.

## Confirmed boundaries

- Gemma 4 full RAG validation used a controlled manually created document in an existing local database.
- Additional lower-scored sources from previously indexed documents were also returned, but the highest-scored source was the intended validation document.
- The observed Gemma 4 latency is a single local run, not a benchmark.
- PDF validation covers extractable text only.
- Mock/hash validation confirms application control flow, not semantic answer quality.
- Model latency and memory use depend on local hardware.
- No load, retrieval-quality or answer-quality benchmark is claimed.
- No public deployment or multi-user security validation is claimed.
