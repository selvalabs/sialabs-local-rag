# Local Setup

## Prerequisites

- Git
- Python 3.12+
- `uv`
- Node.js 22+
- Docker, optional
- Ollama, optional for real local AI

## Backend

From the repository root:

```powershell
cd backend
uv sync --dev
uv run uvicorn sialabs_local_rag.main:app --reload --host 0.0.0.0 --port 8000
```

The API is available at `http://localhost:8000` and OpenAPI documentation at `http://localhost:8000/docs`.

## Frontend

Open another terminal from the repository root:

```powershell
cd frontend
npm ci
npm run dev
```

Open `http://localhost:5173`.

## Environment configuration

Copy the example file before changing runtime providers:

```powershell
copy .env.example .env
```

The `.env` file is local configuration and must not be committed.

## Docker Compose

```powershell
copy .env.example .env
docker compose up --build
```

When the optional Ollama profile is configured locally:

```powershell
docker compose --profile llm up --build
```

## Quick manual check

1. Open `http://localhost:5173`.
2. Index the sample text or upload a supported document.
3. Ask a question about the indexed content.
4. Confirm that the answer includes retrieved sources.

A reproducible sample document can be seeded with:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\seed-demo.ps1
```

## Reset local data

Stop the backend before deleting local data:

```powershell
Remove-Item -Recurse -Force .\data
```

The backend recreates its local database on the next start.
