# E2E Ollama RAG Flow Validation

This document records the first end-to-end local Ollama RAG validation for SIALabs Local RAG.

## Validation date

2026-06-18

## Branch

test/e2e-ollama-rag-flow

## Goal

Validate the complete application flow using local Ollama models:

1. start backend in Ollama mode;
2. seed a demo document;
3. generate Ollama embeddings;
4. ask a RAG question;
5. receive an Ollama-generated answer;
6. confirm retrieved sources are returned.

## Backend configuration

The backend reported the following runtime configuration:

~~~json
{
  "app_name": "SIALabs Local RAG",
  "llm_provider": "ollama",
  "llm_model": "gemma3:4b",
  "embedding_provider": "ollama",
  "embedding_model": "embeddinggemma",
  "retrieval_top_k": 5,
  "chunk_size": 1200,
  "chunk_overlap": 180
}
~~~

## Models used

- Chat model: `gemma3:4b`
- Embedding model: `embeddinggemma`

## Seed command

~~~powershell
powershell -ExecutionPolicy Bypass -File .\scripts\seed-demo.ps1
~~~

## Seed result

The demo document was created successfully:

~~~json
{
  "id": "48ac355c-34c4-4d55-bd83-75d313765e51",
  "title": "SIALabs Local RAG Demo Context",
  "source_type": "demo-seed",
  "total_chars": 1927,
  "total_chunks": 2
}
~~~

## RAG query

~~~text
What is SIALabs Local RAG and what skills does it demonstrate?
~~~

## RAG result summary

The API returned:

- provider: `ollama`
- model: `gemma3:4b`
- retrieval_top_k: `5`
- sources returned: `2`
- source document: `SIALabs Local RAG Demo Context`
- latency_ms: `35973`

## Script issue found and fixed

During E2E validation, `scripts/seed-demo.ps1` failed on Windows PowerShell because `Get-Content -Raw` could serialize the content into JSON with PowerShell metadata such as `PSPath` and `PSParentPath`.

The script was updated to:

- resolve the file path with `Resolve-Path`;
- read content with `[System.IO.File]::ReadAllText(...)`;
- cast payload content explicitly as `[string]$content`.

This keeps the JSON payload compatible with the FastAPI contract, where `content` must be a string.

## Limitation observed

The Windows PowerShell console displayed mojibake for some accented characters and dash characters in the JSON output.

This did not block the E2E validation. The full app path succeeded:

- document ingestion;
- chunking;
- embedding generation;
- vector retrieval;
- Ollama chat generation;
- source attribution.

A future issue can improve encoding handling and demo text normalization if needed.

## Portfolio relevance

This validation demonstrates that SIALabs Local RAG is not only CI-testable with mock/hash providers, but also operational with real local AI models through Ollama.

The project now has evidence for:

- local-first RAG architecture;
- real local LLM integration;
- local embedding model integration;
- reproducible demo seeding;
- source-grounded answers;
- GitHub issue -> branch -> validation -> PR workflow.