# Release readiness checklist

This checklist is the quality gate for installer-facing or distributable releases of SIALabs Local RAG.

It does **not** define a second installer implementation. Artifact creation remains documented in [`INSTALLERS.md`](INSTALLERS.md), while the existing Windows local-app flow remains under [`../installer/windows/README.md`](../installer/windows/README.md).

## Knowledge-engine gate

The minimum reliability work that must be present in `main` before producing the next stable installer-facing release is:

- embedding compatibility and explicit reindex lifecycle;
- local data deletion semantics;
- deterministic retrieval evaluation harness;
- relevance gating measured against that evaluation.

The stronger knowledge-product layer is:

- hybrid dense + lexical retrieval;
- structure-aware ingestion and source locations;
- conversational retrieval separation.

Product expansion currently covered by the full regression suite includes:

- local folder collections and incremental indexing;
- richer Office formats and optional local OCR.

A future maintenance release does not need to reopen or reimplement these capabilities. Their behavior must remain protected by the current tests/evaluation on the release commit.

## Automated release preflight

From the repository root, on the intended release commit:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\release-preflight.ps1 -Version v0.3.1
```

For a PWA archive:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\release-preflight.ps1 `
  -Version v0.3.1 `
  -BuildPwaArchive
```

For an intentional packaging-branch dry run only:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\release-preflight.ps1 -AllowNonMain
```

`-AllowNonMain` is not valid evidence for a production release.

The production preflight requires:

1. a clean working tree;
2. the current branch to be `main`;
3. local `main` to match freshly fetched `origin/main`;
4. when `-Version` is supplied, that tag to exist and point to `HEAD`;
5. the complete local lint/test/typecheck/build validation suite;
6. deterministic dense retrieval evaluation using the hash provider;
7. deterministic hybrid retrieval evaluation using the hash provider;
8. a second clean-tree verification after validation/build steps;
9. successful artifact creation when requested.

Any failed step blocks packaging. Do not bypass a failed knowledge-engine gate by manually creating an archive.

## Release operator checklist

Before tagging/package creation:

- [ ] Required reliability capabilities above are represented in the current `main` history.
- [ ] The intended commit has green repository CI.
- [ ] No unrelated feature branch is being packaged.
- [ ] `git status` is clean.
- [ ] Local `main` is synchronized with `origin/main`.
- [ ] Release notes identify any user-visible retrieval, ingestion, migration or deletion changes.

On the release commit:

- [ ] Run `scripts/release-preflight.ps1` successfully.
- [ ] Confirm dense deterministic evaluation completes.
- [ ] Confirm hybrid deterministic evaluation completes.
- [ ] Confirm the full backend and frontend quality gates complete.
- [ ] Confirm the version tag points to the exact validated commit.

For the distributable artifact:

- [ ] Follow [`INSTALLERS.md`](INSTALLERS.md) rather than inventing another packaging path.
- [ ] For the current Windows local-app flow, follow [`../installer/windows/README.md`](../installer/windows/README.md).
- [ ] Inspect the artifact for accidental `.env`, SQLite, private document, chat or local model content.
- [ ] State that Ollama/model files remain external dependencies unless a later release explicitly changes that boundary.
- [ ] Smoke-test startup from the produced artifact/shortcut on a clean target environment appropriate to that artifact.
- [ ] Document known limitations and whether the artifact is PWA-only, Windows local-app flow, or a future native installer.

## What this gate does not do

This checklist does not:

- implement a new Windows installer;
- replace the current packaging architecture;
- migrate the app to Tauri;
- bundle Ollama or model weights;
- claim generated-answer quality is fully benchmarked by the retrieval evaluation.

The deterministic evaluation is a regression gate for retrieval behavior. Real-model smoke/evaluation remains a separate validation layer where Ollama is available.
