# SIALabs Local Launcher

The local launcher is a small helper process for local development and future installer work.

It runs on `127.0.0.1:8765` and exposes a fixed set of safe runtime actions so the frontend can inspect and control the local backend without executing arbitrary operating-system commands from the browser.

## Start the launcher

From the repository root:

```powershell
python .\launcher\local_launcher.py
```

Or, if Python is only available through `py`:

```powershell
py .\launcher\local_launcher.py
```

The launcher prints the bind address and the backend directory it will use.

## Endpoints

```text
GET  /health
GET  /status
GET  /logs/backend
POST /backend/start
POST /backend/stop
POST /backend/restart
```

## Defaults

The launcher starts the backend from the repository `backend` directory using:

```text
uv run python -m uvicorn sialabs_local_rag.main:app --host 127.0.0.1 --port 8000
```

Default backend environment:

```text
LLM_PROVIDER=ollama
EMBEDDING_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_CHAT_MODEL=gemma4:e2b
OLLAMA_EMBED_MODEL=embeddinggemma
OLLAMA_NUM_CTX=4096
OLLAMA_TEMPERATURE=0.2
OLLAMA_KEEP_ALIVE=5m
```

## Optional environment variables

```text
SIALABS_LAUNCHER_HOST=127.0.0.1
SIALABS_LAUNCHER_PORT=8765
SIALABS_LAUNCHER_TOKEN=<optional local token>
SIALABS_BACKEND_DIR=<path to backend directory>
SIALABS_BACKEND_URL=http://127.0.0.1:8000
SIALABS_BACKEND_COMMAND=<custom fixed command>
SIALABS_OLLAMA_URL=http://127.0.0.1:11434
```

When `SIALABS_LAUNCHER_TOKEN` is set, POST requests must include:

```text
X-SIALabs-Launcher-Token: <token>
```

## Safety boundaries

- The launcher binds to `127.0.0.1` by default.
- It does not expose a generic command execution endpoint.
- It only exposes fixed runtime actions.
- Stop/restart only controls the backend process started by the launcher.
- Existing manual terminal workflows still work without the launcher.
