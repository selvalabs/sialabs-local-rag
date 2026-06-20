# Recruiter Evidence Matrix

Este documento conecta funcionalidades do projeto a competências observáveis por recrutadores.

| Evidência no repositório | Competência demonstrada |
| --- | --- |
| `backend/src/sialabs_local_rag/api.py` | API REST, FastAPI, validação, tratamento de erro |
| `backend/src/sialabs_local_rag/service.py` | separação de regra de negócio e orquestração RAG |
| `backend/src/sialabs_local_rag/providers.py` | abstração de providers, integração com IA local, fallback de CI |
| `backend/src/sialabs_local_rag/storage.py` | persistência SQLite, modelagem simples, queries, serialização |
| `backend/tests/` | testes unitários e de API |
| `frontend/src/App.tsx` | UI funcional, estado React, integração com API |
| `frontend/src/api.ts` | cliente HTTP tipado |
| `.github/workflows/ci.yml` | CI, gates de qualidade, maturidade operacional |
| `docker-compose.yml` | empacotamento e execução reproduzível |
| `docs/` | comunicação técnica, arquitetura, segurança, setup |
| `issues/001...md` | planejamento por issue e escopo claro |

## Narrativa para entrevista

O projeto mostra uma aplicação full stack de IA aplicada que não depende obrigatoriamente de APIs externas. Ele separa claramente produto, backend, frontend, dados, IA e operação.

Pontos fortes para explicar:

- Por que existe modo mock/hash.
- Como o RAG é construído do zero sem LangChain.
- Quais limites do SQLite foram aceitos no MVP.
- Como evoluir para pgvector, Supabase ou Qdrant.
- Por que o histórico GitHub faz parte do portfólio.
- Como o CI garante qualidade sem depender de modelo local.

