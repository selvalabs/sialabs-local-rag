# Real Ollama Validation

This document records the first real local-model validation for SIALabs Local RAG.

## Validation date

2026-06-18

## Local runtime

- Runtime: Ollama
- Base URL: http://localhost:11434
- Chat model: gemma3:4b
- Embedding model: embeddinggemma

## Models installed

~~~powershell
ollama pull gemma3:4b
ollama pull embeddinggemma
~~~

The first attempted embedding model name, embeddinggemma3, did not exist. The correct model used for validation was embeddinggemma.

## Smoke-test command

~~~powershell
$env:OLLAMA_CHAT_MODEL = "gemma3:4b"
$env:OLLAMA_EMBED_MODEL = "embeddinggemma"

powershell -ExecutionPolicy Bypass -File .\scripts\check-ollama.ps1 -RunSmokeRequests
~~~

## Result summary

The smoke test confirmed:

- Ollama API was reachable at http://localhost:11434;
- local models were listed successfully;
- gemma3:4b was found as the chat model;
- embeddinggemma was found as the embedding model;
- direct /api/chat smoke request succeeded;
- direct /api/embed smoke request succeeded;
- the script ended with "Ollama smoke test passed".

## Observed output

~~~text
Ollama smoke test
Base URL: http://localhost:11434
Chat model: gemma3:4b
Embedding model: embeddinggemma

Checking Ollama API...
Available local models:
- embeddinggemma:latest
- gemma3:4b

Chat model found: gemma3:4b
Embedding model found: embeddinggemma

Running chat smoke request...
Chat response:
Yes, the local model is now running.

Running embedding smoke request...
Embedding response received. Embedding arrays: 1

Ollama smoke test passed.
~~~

## Portfolio relevance

This validation proves that the project can run beyond mock mode.

The repository now demonstrates:

- CI-friendly mock/hash mode;
- local Ollama runtime path;
- real Gemma chat model validation;
- real local embedding model validation;
- reproducible script-based local AI smoke test.

## Limitations

This validation does not benchmark performance, GPU usage, answer quality or long-document retrieval quality.

Those can be covered in future issues.