# Installer and release artifact flow

This document defines the packaging flow for installable or distributable artifacts.

It is intentionally outside the runtime application. The app can keep evolving through normal feature branches, while artifacts are built only after a version is considered stable enough to package.

## Golden rule

Build installable artifacts from a clean version tag, not from a loose feature branch.

Recommended sequence:

~~~text
feature branch
  -> pull request
  -> CI
  -> manual validation
  -> merge to main
  -> clean main
  -> version tag
  -> release preflight
  -> package artifacts
  -> GitHub Release
~~~

## Artifact types

| Stage | Artifact | Status |
| --- | --- | --- |
| PWA | Static frontend app shell archive | Supported by this flow |
| Desktop | Tauri desktop installer | Planned under #37 |
| Mobile | Local-network companion app | Planned under #38 |
| Model runtime | Ollama and model files | External dependency, not bundled |

## PWA app shell artifact

The PWA artifact is a static frontend build archive. It contains the installable browser app shell, icons, manifest and service worker.

It does not contain:

- private documents
- chat history
- SQLite data
- backend Python runtime
- Ollama
- model files

The service worker is expected to cache static frontend assets only. It must not cache API responses or private document data.

## Native desktop artifacts

Native desktop installers are intentionally not part of the PWA stage.

They should be introduced after the Tauri desktop shell exists. At that point, this flow should be extended to produce platform-specific artifacts such as Linux, Windows or macOS installers.

The preferred shape is:

~~~text
Tauri desktop shell
  -> bundled React frontend
  -> local backend strategy
  -> Ollama detected as external service
  -> generated installer artifact
~~~

## Versioning

Use semantic version tags:

~~~text
v0.3.0
v0.4.0
v0.5.0
~~~

Release candidates can use:

~~~text
v0.4.0-rc.1
~~~

## Local preflight

Run from the repository root:

~~~powershell
powershell -ExecutionPolicy Bypass -File .\scripts\release-preflight.ps1 -Version v0.3.0 -BuildPwaArchive
~~~

The preflight should:

- refuse to run from a dirty git working tree
- require `main` by default
- run the existing local validation suite
- build the frontend
- optionally create a PWA archive under `dist/release/<version>/`

Use `-AllowNonMain` only for dry runs on packaging branches.

## Output convention

Generated release artifacts should go under:

~~~text
dist/release/<version>/
~~~

This directory is ignored by git through the existing `dist/` ignore rule.

Example:

~~~text
dist/release/v0.3.0/sialabs-local-rag-pwa-v0.3.0.zip
~~~

## Validation checklist before packaging

- `main` is clean and synced with `origin/main`.
- Release tag exists and points to the intended commit.
- CI passed for the intended commit.
- Local validation suite passed.
- PWA install behavior was manually tested when relevant.
- Backend unavailable state was manually tested when relevant.
- No private document, database or chat data is included in artifacts.

## GitHub Release checklist

For each release:

- attach generated artifacts
- mention the source tag
- mention what was validated
- mention known limitations
- mention whether the artifact is PWA-only or native desktop

## Security boundary

Localhost-only use does not require authentication in the MVP.

If the backend is exposed beyond localhost, including local-network mobile access, use a separate security issue for pairing or local access tokens before treating the artifact as safe for shared-network use.
