from __future__ import annotations

import pytest

from sialabs_local_rag.chunking import chunk_text, normalize_text


def test_normalize_text_removes_repeated_whitespace() -> None:
    assert normalize_text(" SIALabs\n\nLocal\tRAG ") == "SIALabs Local RAG"


def test_chunk_text_returns_overlapping_chunks() -> None:
    text = " ".join(f"palavra{i}" for i in range(120))
    chunks = chunk_text(text, chunk_size=180, overlap=40)

    assert len(chunks) > 1
    assert all(chunk.strip() for chunk in chunks)
    assert "palavra0" in chunks[0]


def test_chunk_text_rejects_invalid_size() -> None:
    with pytest.raises(ValueError):
        chunk_text("texto válido", chunk_size=0)
