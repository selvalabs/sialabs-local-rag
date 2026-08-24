# Public showcase demo pack

This pack defines the reproducible local capture for the public demo. It is
deliberately a checklist and source-of-truth script, not a claim that a visual
asset exists when it has not been captured and reviewed.

## Capture setup

Use a clean local data directory, then start:

```powershell
cd backend
uv run uvicorn sialabs_local_rag.main:app --host 127.0.0.1 --port 8000

# in another terminal
cd frontend
npm ci
npm run dev -- --host 127.0.0.1

# from the repository root
powershell -ExecutionPolicy Bypass -File .\scripts\seed-demo.ps1
```

Open `http://127.0.0.1:5173` and capture the following states:

1. empty local base with the local/mock status visible;
2. seeded document library showing document, chunk and character counts;
3. grounded answer with expanded source cards and source IDs;
4. runtime settings and the local API status panel;
5. dark theme and Portuguese language controls;
6. offline-installed shell after the service worker has cached the app shell.

## Expected evidence

- API health returns `status: ok` on `127.0.0.1:8000`;
- the seeded document is synthetic and contains no private data;
- answers expose source metadata without exposing hidden prompts or embeddings;
- the UI remains usable when the API is stopped, showing an actionable error;
- screenshots are reviewed for readable text, no secrets and no local filesystem
  paths before being added to a release artifact.

## Asset status

The repository currently has no committed screenshot or video asset from this
capture. The in-app browser was unavailable during the local capture attempt,
so no unverified placeholder is included. Once a browser is available, save
reviewed images under `docs/demo/` with stable names such as:

- `workspace-empty.png`;
- `workspace-grounded-answer.png`;
- `workspace-dark-pt.png`.

The demo pack is complete only after those assets are captured, inspected and
referenced from the README or release notes.
