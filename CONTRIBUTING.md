# Contributing

## Development workflow

1. Open or reference an issue with one focused outcome.
2. Create an independent branch from `main`.
3. Write or update local tests before implementation when behavior changes.
4. Run the relevant backend/frontend/container checks locally.
5. Keep commits focused and describe the user-visible or operational effect.
6. Open a pull request only after the local gates are green.

The project is local-first. Do not add real user documents, databases, `.env`
files, API keys, downloaded models or OCR output to commits.

## Local checks

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate-local.ps1
cd frontend
npm run test
npm run typecheck
npm run build
```

For container changes, also run `docker compose config` and the relevant image
builds. For browser changes, run the Playwright smoke test after installing the
Chromium binary locally.

## Commit and review expectations

Keep unrelated refactors out of feature branches. Document intentional
limitations and update the relevant security, testing or release documentation.
Reviewers should be able to reproduce the claimed result from the commit and
its local commands.
