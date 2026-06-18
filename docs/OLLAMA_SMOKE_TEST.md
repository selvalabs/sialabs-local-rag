# Ollama Smoke Test

This guide explains how to validate the optional local AI mode for SIALabs Local RAG.

The default project mode is `mock/hash`, which is used for CI, interviews and machines without local models. Ollama mode is optional and exists to demonstrate the local model runtime path.

## 1. Start from a clean branch

Expected branch:

~~~powershell
git branch --show-current
~~~

Expected output:

~~~text
feat/ollama-smoke-test
~~~

## 2. Install and start Ollama

Install Ollama using the official installer for your operating system.

After installation, make sure the local API is running:

~~~powershell
Invoke-RestMethod -Uri http://localhost:11434/api/tags -Method Get
~~~

If Ollama is running, the command returns a JSON object with local models.

## 3. Pull or configure models

The default `.env.example` uses:

~~~env
OLLAMA_CHAT_MODEL=gemma4
OLLAMA_EMBED_MODEL=embeddinggemma
~~~

If those model names are available in your Ollama installation, pull them:

~~~powershell
ollama pull gemma4
ollama pull embeddinggemma
~~~

If a model name is not available on your machine, choose another local model and update `.env` accordingly.

The project intentionally keeps model names configurable because local hardware and model availability can vary.

## 4. Configure local AI mode

Copy the example environment file:

~~~powershell
copy .env.example .env
~~~

Set:

~~~env
LLM_PROVIDER=ollama
EMBEDDING_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=gemma4
OLLAMA_EMBED_MODEL=embeddinggemma
~~~

Do not commit `.env`.

## 5. Run the Ollama check script

From the repository root:

~~~powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check-ollama.ps1
~~~

The script checks:

- whether the Ollama API is reachable;
- which local models are installed;
- whether the configured chat model is available;
- whether the configured embedding model is available.

To also run direct chat and embedding requests:

~~~powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check-ollama.ps1 -RunSmokeRequests
~~~

## 6. Run the app in Ollama mode

Start the backend:

~~~powershell
cd backend
uv sync --dev
uv run uvicorn sialabs_local_rag.main:app --reload --host 0.0.0.0 --port 8000
~~~

Start the frontend in another terminal:

~~~powershell
cd frontend
npm ci
npm run dev
~~~

Open:

~~~text
http://localhost:5173
~~~

## 7. Seed demo content

From the repository root:

~~~powershell
powershell -ExecutionPolicy Bypass -File .\scripts\seed-demo.ps1
~~~

Then ask questions from `docs/DEMO.md`.

## 8. Return to mock/hash mode

To return to default lightweight mode, set:

~~~env
LLM_PROVIDER=mock
EMBEDDING_PROVIDER=hash
~~~

Then restart the backend.

## Portfolio value

This smoke test shows that the project is not only a UI/API prototype. It also documents a practical path for running local AI, validating model availability and switching between CI-friendly mock mode and local model mode.