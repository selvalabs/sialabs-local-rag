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
| Full local RAG flow | `gemma3:4b` + `embeddinggemma` | Ingestion, embeddings, retrieval, answer generation and source attribution succeeded |
| Gemma 4 chat smoke test | `gemma4:e2b` | Direct local chat request succeeded |

The local Ollama validations were performed on June 18, 2026.

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

The complete application path was validated with `gemma3:4b` and `embeddinggemma`:

1. start the backend with Ollama providers;
2. seed the demo document;
3. generate local document embeddings;
4. submit a RAG question;
5. retrieve relevant chunks;
6. generate an Ollama answer;
7. return source attribution.

## Confirmed boundaries

- `gemma4:e2b` was validated through direct Ollama smoke requests, not the full RAG flow.
- PDF validation covers extractable text only.
- Mock/hash validation confirms application control flow, not semantic answer quality.
- Model latency and memory use depend on local hardware.
- No load, retrieval-quality or answer-quality benchmark is claimed.
- No public deployment or multi-user security validation is claimed.
