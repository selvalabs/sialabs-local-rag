from __future__ import annotations

from collections.abc import Sequence
from math import sqrt


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    """Return cosine similarity for two numeric vectors."""

    if len(left) != len(right) or not left:
        return 0.0

    dot_product = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = sqrt(sum(value * value for value in left))
    right_norm = sqrt(sum(value * value for value in right))

    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0

    return dot_product / (left_norm * right_norm)


def normalize_vector(vector: Sequence[float]) -> list[float]:
    """Return a normalized copy of a vector."""

    norm = sqrt(sum(value * value for value in vector))
    if norm == 0.0:
        return [0.0 for _ in vector]
    return [value / norm for value in vector]
