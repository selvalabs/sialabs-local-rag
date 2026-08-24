# Installer and release artifact flow

This document defines the packaging flow for installable or distributable artifacts.

It is intentionally outside the runtime application. The app can keep evolving through normal feature branches, while artifacts are built only after a version is considered stable enough to package.

Release quality requirements are defined in [`RELEASE_READINESS.md`](RELEASE_READINESS.md). Packaging must not bypass that gate.

## Golden rule

Build installable artifacts from a clean, synchronized and validated `main` commit with the intended version tag. Do not package a loose feature branch or bypass a failed knowledge-engine evaluation.

Recommended sequence:

~~~text
feature branch
  -> pull request
  -> CI
  -> merge to main
  -> clean + synchronized main
  -> version tag on intended commit
  -> release preflight + deterministic RAG evaluation
  -> package artifacts
  -> manual artifact smoke test
  -> GitHub Release
~~~

## Artifact types

| Stage | Artifact | Status |
| --- | --- | --- |
| PWA | Static frontend app shell archive | Supported by this flow |
| Windows local app | Launcher/backend/frontend shortcut flow | Existing local-app path |
| Desktop | Tauri desktop installer | Reserved for a future desktop milestone |
| Mobile | Local-network companion app | Future scope |
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

## Windows local-app flow

The existing one-click/shortcut-oriented Windows setup is documented in [`../installer/windows/README.md`](../installer/windows/README.md).

That flow remains the source of truth for its app preparation and shortcut behavior. The release-quality gate in this document and `RELEASE_READINESS.md` determines **when a validated commit is eligible to be distributed**; it does not replace the Windows packaging implementation.

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
v0.3.1
v0.3.1
v0.5.0
~~~

Release candidates can use:

~~~text
v0.3.1-rc.1
~~~

For a production release preflight, the version tag must exist and point to the exact validated `HEAD` commit.

## Local preflight

Run from the repository root:

~~~powershell
powershell -ExecutionPolicy Bypass -File .\scripts\release-preflight.ps1 -Version v0.3.1 -BuildPwaArchive
~~~

The preflight:

- refuses to package from a dirty git working tree;
- requires `main` by default;
- fetches and verifies that local `main` matches `origin/main` before artifact creation;
- verifies that the supplied version tag points to `HEAD`;
- runs the existing local lint/test/typecheck/build validation suite;
- runs deterministic dense RAG evaluation with the hash provider;
- runs deterministic hybrid RAG evaluation with the hash provider;
- verifies the working tree is still clean after validation/build steps;
- optionally creates a PWA archive under `dist/release/<version>/`.

Use `-AllowNonMain` only for intentional packaging dry runs. It is not sufficient evidence for a production release.

See [`RELEASE_READINESS.md`](RELEASE_READINESS.md) for the complete core-quality and manual release checklist.

## Output convention

Generated release artifacts should go under:

~~~text
dist/release/<version>/
~~~

This directory is ignored by git through the existing `dist/` ignore rule.

Example:

~~~text
dist/release/v0.3.1/sialabs-local-rag-pwa-v0.3.1.zip
~~~

## Validation checklist before packaging

- `main` is clean and synchronized with `origin/main`.
- Release tag exists and points to the intended commit.
- CI passed for the intended commit.
- Local validation suite passed.
- Dense and hybrid deterministic RAG evaluations passed.
- PWA install behavior was manually tested when relevant.
- Windows local-app startup/shortcut behavior was manually tested when relevant.
- Backend unavailable state was manually tested when relevant.
- No private document, database, chat, environment secret or model data is included in artifacts.

## GitHub Release checklist

For each release:

- attach generated artifacts
- mention the source tag and commit
- mention what was validated
- mention known limitations
- mention whether the artifact is PWA-only, Windows local-app flow or a future native desktop artifact

## Security boundary

Localhost-only use does not require authentication in the MVP.

If the backend is exposed beyond localhost, including local-network mobile access, use a separate security issue for pairing or local access tokens before treating the artifact as safe for shared-network use.
