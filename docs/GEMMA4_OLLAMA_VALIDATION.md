# Gemma 4 Ollama Validation

This document records a real local Ollama smoke validation using Gemma 4.

## Validation date

2026-06-18

## Runtime

- Runtime: Ollama
- Base URL: http://localhost:11434
- Chat model: gemma4:e2b
- Embedding model: embeddinggemma

## Command executed

~~~powershell
$env:OLLAMA_CHAT_MODEL = "gemma4:e2b"
$env:OLLAMA_EMBED_MODEL = "embeddinggemma"

powershell -ExecutionPolicy Bypass -File .\scripts\check-ollama.ps1 -RunSmokeRequests
~~~

## Observed result

~~~text
Ollama smoke test
Base URL: http://localhost:11434
Chat model: gemma4:e2b
Embedding model: embeddinggemma

Checking Ollama API...
Available local models:
- embeddinggemma:latest
- gemma3:4b
- gemma4:e2b

Chat model found: gemma4:e2b
Embedding model found: embeddinggemma

Running chat smoke request...
Chat response:
The local model is running.

Running embedding smoke request...
Embedding response received. Embedding arrays: 1

Ollama smoke test passed.
~~~

## Result summary

The smoke test confirmed:

- Ollama API was reachable locally;
- gemma4:e2b was installed and detected;
- embeddinggemma was installed and detected;
- direct chat smoke request succeeded;
- direct embedding smoke request succeeded.

## Model positioning

The project now has two locally validated chat model options:

- gemma3:4b: validated lightweight local model;
- gemma4:e2b: validated newer Gemma 4 local model;
- embeddinggemma: validated local embedding model.

## Limitations

This validation only confirms direct Ollama chat and embedding API functionality.

It does not benchmark latency, memory usage, answer quality or full RAG E2E behavior with Gemma 4.

The full RAG E2E flow was previously validated with gemma3:4b and embeddinggemma.