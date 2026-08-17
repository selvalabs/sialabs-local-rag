# Windows one-click app flow

This is the Windows local-app/shortcut MVP tracked by #49.

## MVP status

The **script + desktop shortcut MVP is complete**: one setup command prepares the local app, and the daily-use shortcut starts the launcher/backend/frontend flow and opens the app.

This milestone intentionally does **not** claim to provide a signed standalone `.exe` installer. A future native installer can wrap the validated runtime path below without creating a second startup architecture.

For **distribution/release work**, this document does not replace the quality gate. Before preparing a commit for distribution, follow [`../../docs/RELEASE_READINESS.md`](../../docs/RELEASE_READINESS.md) and the artifact flow in [`../../docs/INSTALLERS.md`](../../docs/INSTALLERS.md).

## What the current flow does

- Fails early when required Python/uv/npm tooling is unavailable.
- Prepares the backend environment with `uv sync` and rejects a non-zero dependency-sync result.
- Installs frontend dependencies when needed.
- Builds `frontend/dist` and verifies that the production build exists.
- If `-SkipFrontendBuild` is used, requires an existing production build rather than completing with a broken shortcut.
- Creates a desktop shortcut named `SIALabs Local RAG`.
- The shortcut starts the local launcher.
- The launcher starts the backend.
- A static local frontend server starts on `127.0.0.1:4182`.
- The browser opens the app URL.
- The mounted launcher panel can inspect launcher/backend/Ollama status, control the managed backend and show its bounded log tail.

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

This synchronizes the backend environment, builds the frontend and creates the desktop shortcut.

Optional preparation flags:

```powershell
# Reuse an already-built frontend/dist. The command fails if the build is missing.
.\scripts\install-windows-app.ps1 -SkipFrontendBuild

# Prepare dependencies/build without creating a shortcut.
.\scripts\install-windows-app.ps1 -NoShortcut
```

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

The script starts or verifies:

```text
http://127.0.0.1:8765  launcher
http://127.0.0.1:8000  backend
http://127.0.0.1:4182  frontend
```

Then it opens:

```text
http://127.0.0.1:4182
```

The launcher remains optional for the broader project: developers can still run the backend/frontend manually. The Windows shortcut path deliberately uses it so users do not need multiple terminal windows.

## Future native installer

A future `.exe`/`.msi` installer should reuse this completed MVP flow rather than create a competing runtime path:

1. install app files into an application directory;
2. run setup/build steps or include prebuilt artifacts;
3. create desktop/start-menu shortcuts;
4. optionally register the launcher as a background service/startup process;
5. detect Ollama/model availability and guide model installation;
6. add signing/uninstall/update behavior appropriate to a native package.

Those items are a later native-packaging milestone, not unfinished acceptance criteria for the #49 script/shortcut MVP.
