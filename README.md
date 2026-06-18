# SIALabs Local RAG

Aplicação **local-first** para consulta de documentos com RAG, IA local via Ollama/Gemma e armazenamento em SQLite.

O projeto foi desenhado como peça de portfólio técnico para demonstrar:

- desenvolvimento full stack com React, TypeScript, Python e FastAPI;
- construção de APIs REST com validação, testes e documentação;
- fluxo RAG com ingestão, chunking, embeddings, busca semântica e resposta com fontes;
- soberania de dados: modo local com SQLite e modelos executados via Ollama;
- disciplina operacional com issue, branch, Conventional Commits, PR, CI e validação local;
- comunicação técnica para recrutamento por meio de documentação, arquitetura e evidências.

## Stack

| Camada | Tecnologia |
| --- | --- |
| Frontend | React, TypeScript, Vite, CSS responsivo |
| Backend | FastAPI, Pydantic, SQLite, httpx |
| IA local | Ollama API, modelo de chat configurável, embeddings configuráveis |
| Testes | pytest, FastAPI TestClient |
| Qualidade | Ruff, mypy, TypeScript build |
| Infra | Docker Compose, GitHub Actions |

## Modos de execução

O backend suporta dois modos:

1. **Modo demo/CI**, sem modelo externo:
   - `LLM_PROVIDER=mock`
   - `EMBEDDING_PROVIDER=hash`
   - útil para testes, CI, entrevistas e validação rápida.

2. **Modo local AI**, usando Ollama:
   - `LLM_PROVIDER=ollama`
   - `EMBEDDING_PROVIDER=ollama`
   - `OLLAMA_CHAT_MODEL=gemma4`
   - `OLLAMA_EMBED_MODEL=embeddinggemma`

O modo demo existe para garantir que o projeto seja avaliável mesmo quando o recrutador não tiver GPU, Ollama ou modelos baixados.

## Execução local

### Backend

```powershell
cd backend
uv sync --dev
uv run uvicorn sialabs_local_rag.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```powershell
cd frontend
npm ci
npm run dev
```

Acesse:

- Frontend: `http://localhost:5173`
- API: `http://localhost:8000`
- Swagger/OpenAPI: `http://localhost:8000/docs`

## Execução com Ollama

Instale e inicie o Ollama localmente. Depois baixe os modelos desejados:

```powershell
ollama pull gemma4
ollama pull embeddinggemma
```

Copie o arquivo de ambiente:

```powershell
copy .env.example .env
```

Ajuste:

```env
LLM_PROVIDER=ollama
EMBEDDING_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=gemma4
OLLAMA_EMBED_MODEL=embeddinggemma
```

Suba backend e frontend normalmente.

## Funcionalidades do MVP

- Criar documento por texto colado.
- Fazer upload de `.txt`, `.md` ou `.markdown`.
- Quebrar conteúdo em chunks com overlap.
- Gerar embeddings por hash local ou Ollama.
- Persistir documentos e chunks em SQLite.
- Buscar chunks semanticamente por similaridade de cosseno.
- Gerar resposta contextualizada com fontes.
- Listar e remover documentos.
- Expor healthcheck e configuração pública segura.

## Validação

Backend:

```powershell
cd backend
uv run ruff check . --fix
uv run ruff check .
uv run pytest
uv run mypy src
```

Frontend:

```powershell
cd frontend
npm ci
npm run typecheck
npm run build
```

Repositório:

```powershell
git status --short
git diff --stat
```

## Fluxo GitHub sugerido

Esta entrega deve entrar como o primeiro PR do projeto:

- Issue: `feat(app): bootstrap local RAG MVP`
- Branch: `feat/bootstrap-local-rag`
- Commit: `feat(app): bootstrap local RAG MVP`
- PR: `feat(app): bootstrap local RAG MVP`

O corpo da issue está em `issues/001-bootstrap-local-rag-mvp.md` e o corpo sugerido do PR está em `docs/pr/001-bootstrap-local-rag-mvp.md`.

## Documentação principal

- `docs/ARCHITECTURE.md`
- `docs/API.md`
- `docs/LOCAL_AI.md`
- `docs/SECURITY_PRIVACY.md`
- `docs/TESTING.md`
- `docs/RECRUITER_EVIDENCE.md`
- `docs/GITHUB_WORKFLOW.md`
- `docs/ROADMAP.md`

## Limitações conhecidas do MVP

- A busca vetorial usa SQLite + cálculo em Python, suficiente para portfólio e datasets pequenos.
- Não há autenticação, pois o app é local-first e não deve ser exposto publicamente sem camada adicional.
- O parser inicial aceita texto, Markdown e arquivos UTF-8 simples. PDF pode entrar em issue futura.
- O provider `hash` não substitui embeddings reais; ele existe para teste determinístico e demo sem dependências externas.

## Licença

MIT. Ver `LICENSE`.

<!-- DEMO_SECTION_START -->
## Demo

A reproducible local demo is documented in `docs/DEMO.md`.

It includes:

- sample content in `examples/sialabs-demo-context.md`;
- a seed script in `scripts/seed-demo.ps1`;
- suggested demo questions;
- validation steps;
- optional Ollama mode.

Quick seed command, after starting the backend:

~~~powershell
powershell -ExecutionPolicy Bypass -File .\scripts\seed-demo.ps1
~~~
<!-- DEMO_SECTION_END -->

<!-- OLLAMA_SMOKE_TEST_SECTION_START -->
## Ollama smoke test

The optional local AI mode can be validated with `docs/OLLAMA_SMOKE_TEST.md`.

It includes:

- checking the local Ollama API;
- listing installed local models;
- verifying configured chat and embedding models;
- optionally running direct chat and embedding smoke requests;
- switching the app between mock/hash mode and Ollama mode.

Quick check command:

~~~powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check-ollama.ps1
~~~
<!-- OLLAMA_SMOKE_TEST_SECTION_END -->
