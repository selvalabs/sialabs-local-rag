from __future__ import annotations

from sialabs_local_rag.vector_math import cosine_similarity, normalize_vector


def test_cosine_similarity_for_identical_vectors() -> None:
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0


def test_cosine_similarity_for_mismatched_dimensions_returns_zero() -> None:
    assert cosine_similarity([1.0], [1.0, 2.0]) == 0.0


def test_normalize_vector_preserves_zero_vector() -> None:
    assert normalize_vector([0.0, 0.0]) == [0.0, 0.0]
