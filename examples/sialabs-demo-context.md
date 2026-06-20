# SoberanIA Labs Local RAG — Demo Context

SoberanIA Labs Local RAG is a local-first portfolio project created to demonstrate applied AI, full stack development, API design, local data ownership and reproducible engineering workflow.

The application allows a user to ingest text or Markdown documents, split the content into chunks, generate embeddings, store everything locally in SQLite and ask questions through a retrieval-augmented generation flow.

The project supports two execution modes.

In demo mode, the application uses deterministic hash embeddings and a mock language model response. This makes the project easy to validate in CI, interviews and machines without local AI models installed.

In local AI mode, the application can use Ollama as a local model runtime. The chat model and embedding model are configurable through environment variables, allowing the system to run with local open-weight models when available.

The architecture is intentionally simple and inspectable. The backend is built with FastAPI, Pydantic and SQLite. The frontend is built with React, Vite and TypeScript. The repository includes Docker Compose, GitHub Actions, tests, documentation and a controlled GitHub workflow based on issues, branches, pull requests and CI.

This project demonstrates practical skills in backend development, frontend development, REST APIs, data modeling, local AI integration, RAG pipelines, documentation, testing, Docker and GitHub-based delivery.

The main product idea is to give users a private local assistant for their own knowledge base, without requiring documents to be sent to a cloud LLM provider.

Suggested demo questions:

- What is SoberanIA Labs Local RAG?
- Which technologies are used in this project?
- Why does the project support mock/hash mode?
- How does the local AI mode work?
- What skills does this project demonstrate?
- Why is this project relevant for a portfolio?
