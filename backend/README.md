# Backend — SIALabs Local RAG

API FastAPI responsável por ingestão de documentos, chunking, embeddings, recuperação semântica e geração de respostas com fontes.

## Rodar localmente

```powershell
uv sync --dev
uv run uvicorn sialabs_local_rag.main:app --reload --host 127.0.0.1 --port 8000
```

## Qualidade

```powershell
uv run ruff check . --fix
uv run ruff check .
uv run pytest
uv run mypy src
```

## Endpoints principais

- `GET /health`
- `GET /api/config`
- `POST /api/documents`
- `POST /api/documents/upload`
- `GET /api/documents`
- `DELETE /api/documents/{document_id}`
- `POST /api/chat`

## Providers

O backend usa providers intercambiáveis:

- `hash`: embeddings determinísticos locais para testes e CI.
- `mock`: resposta simulada para testes e CI.
- `ollama`: integração real com IA local.

Isso permite que o projeto seja avaliável em ambientes simples e, ao mesmo tempo, demonstre integração real com modelo local.
