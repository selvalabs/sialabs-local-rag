# SoberanIA Labs Local RAG — Demo Context

SoberanIA Labs Local RAG is a local-first application for private document question answering. It indexes document content locally, retrieves relevant chunks for each question and returns answers together with their sources.

The application accepts pasted text and uploads of `.txt`, `.md`, `.markdown` and text-based `.pdf` files. PDFs must contain extractable text; scanned images are not processed with OCR.

The backend is built with Python, FastAPI and Pydantic. The frontend uses React, Vite and TypeScript. Documents, chunks and embeddings are stored in SQLite.

The RAG pipeline follows these steps:

1. parse and normalize document content;
2. split the content into overlapping chunks;
3. generate an embedding for each chunk;
4. store chunks and embeddings locally;
5. embed the user's question;
6. rank chunks with cosine similarity;
7. send retrieved context to the chat provider;
8. return the answer with source metadata.

In Ollama mode, the application uses locally installed chat and embedding models. Validated models include `gemma3:4b`, `gemma4:e2b` and `embeddinggemma`.

A lightweight mock/hash mode is available for automated tests and CI. It validates the application pipeline deterministically but does not represent real semantic retrieval or model quality.

The current application is intended for trusted local use. It does not include authentication, multi-user authorization, OCR, large-scale vector search or production hardening for public exposure.

Suggested questions:

- What is SoberanIA Labs Local RAG?
- Which file types can it index?
- How are documents and embeddings stored?
- How does retrieval work?
- How are sources returned with an answer?
- What is the difference between Ollama mode and lightweight validation mode?
