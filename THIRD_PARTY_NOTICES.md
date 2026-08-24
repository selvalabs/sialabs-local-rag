# Third-party notices

SIALabs Local RAG is distributed under the MIT license in `LICENSE`. Runtime
and development dependencies remain under their own licenses; their exact
resolved versions are recorded in `backend/uv.lock` and
`frontend/package-lock.json`.

Direct dependency families include:

- FastAPI, Pydantic, HTTPX, pypdf, python-multipart and Uvicorn;
- React, React DOM, TypeScript, Vite and the Vite React plugin;
- optional developer tooling: Ruff, mypy, pytest, Vitest, Testing Library,
  Playwright and openapi-typescript.

The project does not bundle Ollama or downloaded model weights. Ollama remains
an optional external local runtime, and its image is pinned in Compose when
used by the development stack.
