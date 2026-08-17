# Windows one-click app flow

This is the existing Windows local-app/shortcut flow for SIALabs Local RAG, tracked by #49.

It does not yet produce a signed `.exe` installer. Instead, it provides the Windows startup and shortcut behavior that a future installer can wrap.

For **distribution/release work**, this document does not replace the quality gate. Before preparing a commit for distribution, follow [`../../docs/RELEASE_READINESS.md`](../../docs/RELEASE_READINESS.md) and the artifact flow in [`../../docs/INSTALLERS.md`](../../docs/INSTALLERS.md).

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

Ollama and model files remain external dependencies and must not be silently bundled into a release artifact.

## Prepare the app for local use

From the repository root:

```powershell
.\scripts\install-windows-app.ps1
```

This builds the frontend and creates the desktop shortcut. It is useful for local setup and development validation.

Running this setup command by itself is **not** a production release qualification.

## Qualify a commit for distribution

On the intended, clean, synchronized `main` release commit, with the version tag pointing to `HEAD`, run the repository release preflight first:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\release-preflight.ps1 -Version v0.4.0
```

That preflight runs the ordinary quality suite plus deterministic dense and hybrid RAG evaluations and rechecks the release source state. A failed preflight blocks distribution; do not work around it by manually copying/building the Windows app flow.

After the release gate passes, use the packaging/setup steps defined here and in `docs/INSTALLERS.md` for the artifact being produced.

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

A future `.exe` installer should reuse this flow rather than create a competing runtime path:

1. install app files into a local app directory;
2. run setup/build steps or include prebuilt artifacts;
3. create the desktop/start-menu shortcut;
4. optionally register the launcher as a background service/startup process;
5. detect Ollama/model availability and guide model installation.

Native installer implementation remains outside the release-gating work in #61.
