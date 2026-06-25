# Windows one-click app flow

This is the first installer step for SIALabs Local RAG.

It does not yet produce a signed `.exe` installer. Instead, it adds the Windows startup and shortcut flow that the future installer will call.

## What the current flow does

- Prepares the backend environment with `uv sync`.
- Installs frontend dependencies when needed.
- Builds `frontend/dist`.
- Creates a desktop shortcut named `SIALabs Local RAG`.
- The shortcut starts the local launcher.
- The launcher starts the backend.
- A static local frontend server starts on `127.0.0.1:4182`.
- The browser opens the app URL.

## External dependencies for now

The MVP expects these to already be installed:

- Python 3.12+
- uv
- Node.js/npm
- Ollama
- Ollama models:
  - `gemma4:e2b`
  - `embeddinggemma`

## Prepare the app

From the repository root:

```powershell
.\scripts\install-windows-app.ps1
```

This builds the frontend and creates the desktop shortcut.

## Start the app

Use either the desktop shortcut or run:

```powershell
.\scripts\start-local-app.ps1
```

The script starts:

```text
http://127.0.0.1:8765  launcher
http://127.0.0.1:8000  backend
http://127.0.0.1:4182  frontend
```

Then it opens:

```text
http://127.0.0.1:4182
```

## Future installer

The future `.exe` installer should wrap this flow:

1. install app files into a local app directory;
2. run setup/build steps or include prebuilt artifacts;
3. create the desktop/start-menu shortcut;
4. optionally register the launcher as a background service/startup process;
5. detect Ollama/model availability and guide model installation.
