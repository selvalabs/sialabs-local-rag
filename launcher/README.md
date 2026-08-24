# SIALabs Local Launcher

The local launcher is a small helper process for local development and Windows installer/startup work.

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

The normal Windows app flow starts this launcher through `scripts/start-local-app.ps1`, so manual launcher startup is not required for everyday shortcut use.

## Endpoints

```text
GET  /health
GET  /status
GET  /logs/backend
POST /backend/start
POST /backend/stop
POST /backend/restart
```

There is no generic command-execution endpoint.

## Frontend control panel

The React app mounts `LauncherPanel.tsx`, which uses the fixed launcher API to:

- show launcher/backend/Ollama status;
- start, stop and restart a launcher-managed backend;
- read the bounded backend log tail;
- continue showing the app even when the optional launcher is offline.

This keeps the existing manual-terminal workflow available while providing the control surface required by the Windows local-app path.

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

When `SIALABS_LAUNCHER_TOKEN` is set, POST requests must additionally include:

```text
X-SIALabs-Launcher-Token: <token>
```

The token is defense in depth, not the only browser mutation guard.

## Browser mutation guard

State-changing launcher actions reject browser requests when either condition is true:

- the request has an `Origin` outside the explicit local frontend allowlist;
- the browser reports `Sec-Fetch-Site: cross-site`.

Trusted local frontend origins such as `http://127.0.0.1:4182` remain allowed. Local automation such as the PowerShell startup scripts sends no browser `Origin`/`Sec-Fetch-Site` headers and remains supported.

This protects the localhost control API from ordinary cross-site browser POST/CSRF attempts even when `SIALABS_LAUNCHER_TOKEN` is not configured. When a token is configured, both provenance and token checks apply.

## Safety boundaries

- The launcher binds to `127.0.0.1` by default.
- CORS response access is allowlisted to known local frontend origins.
- Browser mutation requests are checked for trusted local provenance.
- An optional launcher token can add a second mutation guard.
- It does not expose a generic command execution endpoint.
- It only exposes fixed runtime actions.
- Stop/restart only controls the backend process started by the launcher.
- Backend log memory is bounded to the most recent 500 lines.
- Existing manual terminal workflows still work without the launcher.

Do not expose the launcher outside loopback without a separate authentication/network security design.
