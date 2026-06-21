# Local AI

## Purpose

The application can run document retrieval and answer generation without an external model API. Ollama provides the real local AI runtime, while lightweight deterministic providers support automated validation.

## Ollama mode

```env
LLM_PROVIDER=ollama
EMBEDDING_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=gemma4:e2b
OLLAMA_EMBED_MODEL=embeddinggemma
```

Validated local models:

```powershell
ollama pull gemma4:e2b
ollama pull gemma3:4b
ollama pull embeddinggemma
```

- `gemma4:e2b`: validated through direct Ollama chat requests.
- `gemma3:4b`: validated through direct requests and the complete RAG flow.
- `embeddinggemma`: validated for local query and document embeddings.

Model names remain configurable because hardware capacity and installed model tags vary by environment.

## Lightweight validation mode

```env
LLM_PROVIDER=mock
EMBEDDING_PROVIDER=hash
```

This mode is intended for CI, automated tests and quick pipeline checks on machines without local models. Hash embeddings and mock answers are deterministic, but they do not represent real semantic retrieval or model quality.

## Provider boundaries

The backend keeps embedding and chat responsibilities separate:

- the embedding provider generates vectors for documents and questions;
- the retriever ranks stored chunks with cosine similarity;
- the chat provider receives the retrieved context and generates the answer;
- the API returns the answer together with source metadata.

## Operational guidance

- Do not expose the Ollama port publicly.
- Keep runtime model names in environment configuration.
- Verify available models before starting the backend in Ollama mode.
- Use retrieved sources to inspect whether an answer is grounded in indexed content.
- Treat local model availability, memory use and latency as environment-dependent.
