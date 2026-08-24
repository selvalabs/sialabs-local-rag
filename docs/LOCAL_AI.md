# Local AI

## Purpose

The application separates retrieval from answer generation. Ollama provides the real local AI runtime; deterministic providers support automated validation without downloaded models.

## Ollama mode

```env
LLM_PROVIDER=ollama
EMBEDDING_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_CHAT_MODEL=gemma4:e2b
OLLAMA_EMBED_MODEL=embeddinggemma
```

Pull models locally:

```powershell
ollama pull gemma4:e2b
ollama pull embeddinggemma
```

## Lightweight validation mode

```env
LLM_PROVIDER=mock
EMBEDDING_PROVIDER=hash
```

Hash embeddings and mock answers are deterministic regression tools. They do not represent real semantic retrieval or answer quality.

## Retrieval modes

- Dense: cosine similarity over stored embeddings.
- Lexical: SQLite FTS5 search for exact terms and identifiers.
- Hybrid: dense and lexical candidates combined with weighted reciprocal rank fusion (RRF).

Collections are applied before ranking so a question cannot retrieve from an inactive collection. The evaluator can compare dense and hybrid reports on the same corpus.

## Provider boundaries

- the embedding provider creates vectors for documents and questions;
- dense and FTS5 retrievers produce candidates;
- RRF combines channels and the relevance gate controls no-answer behavior;
- the chat provider receives retrieved evidence plus separately typed conversation context;
- the API returns source locators, channel metadata and runtime details.

## Operational guidance

- Keep Ollama and application ports on loopback.
- Verify models before starting Ollama mode.
- Treat local model quality, memory and latency as environment-dependent.
- Inspect returned source cards to determine whether an answer is grounded.
- Use docs/RETRIEVAL_EVALUATION.md for deterministic and optional real-model evaluation.
