from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Sequence

from sialabs_local_rag.parsing import ParsedSegment

_WHITESPACE_RE = re.compile(r"\s+")
_INLINE_WHITESPACE_RE = re.compile(r"[\t\f\v ]+")
_BLANK_LINES_RE = re.compile(r"\n[ \t]*\n(?:[ \t]*\n)+")


@dataclass(frozen=True)
class StructuredChunk:
    content: str
    page_number: int | None = None
    section_title: str | None = None
    source_locator: str | None = None


def normalize_text(text: str) -> str:
    """Legacy normalization helper that collapses all whitespace."""

    return _WHITESPACE_RE.sub(" ", text).strip()


def normalize_structured_text(text: str) -> str:
    """Normalize line noise while preserving paragraph boundaries."""

    normalized_lines = [
        _INLINE_WHITESPACE_RE.sub(" ", line).strip()
        for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    ]
    normalized = "\n".join(normalized_lines).strip()
    return _BLANK_LINES_RE.sub("\n\n", normalized)


def estimate_tokens(text: str) -> int:
    """Cheap token estimate for operational metadata."""

    return max(1, len(text) // 4)


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 180) -> list[str]:
    """Split text into overlapping chunks using the legacy flat-text path."""

    normalized = normalize_text(text)
    if not normalized:
        return []

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")
    if overlap < 0:
        raise ValueError("overlap must be zero or positive")
    if overlap >= chunk_size:
        overlap = max(0, chunk_size // 4)

    chunks: list[str] = []
    start = 0
    text_length = len(normalized)

    while start < text_length:
        end = min(start + chunk_size, text_length)

        if end < text_length:
            min_boundary = start + int(chunk_size * 0.6)
            boundary = normalized.rfind(" ", min_boundary, end)
            if boundary > start:
                end = boundary

        segment = normalized[start:end].strip()
        if segment:
            chunks.append(segment)

        if end >= text_length:
            break

        start = max(0, end - overlap)
        while start < text_length and normalized[start].isspace():
            start += 1

    return chunks


def chunk_parsed_segments(
    segments: Sequence[ParsedSegment],
    chunk_size: int = 1200,
    overlap: int = 180,
) -> list[StructuredChunk]:
    """Chunk parsed source units without crossing page or section boundaries."""

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")
    if overlap < 0:
        raise ValueError("overlap must be zero or positive")
    if overlap >= chunk_size:
        overlap = max(0, chunk_size // 4)

    chunks: list[StructuredChunk] = []
    for segment in segments:
        normalized = normalize_structured_text(segment.content)
        if not normalized:
            continue

        prefix = _metadata_prefix(segment)
        payload_size = max(120, chunk_size - len(prefix) - (2 if prefix else 0))
        payload_overlap = min(overlap, max(0, payload_size // 4))

        for payload in _split_structured_block(
            normalized,
            chunk_size=payload_size,
            overlap=payload_overlap,
        ):
            content = f"{prefix}\n\n{payload}" if prefix else payload
            chunks.append(
                StructuredChunk(
                    content=content,
                    page_number=segment.page_number,
                    section_title=segment.section_title,
                    source_locator=segment.source_locator,
                )
            )

    return chunks


def _metadata_prefix(segment: ParsedSegment) -> str:
    labels: list[str] = []
    if segment.section_title:
        labels.append(f"Section: {segment.section_title}")
    if segment.page_number is not None:
        labels.append(f"Page {segment.page_number}")
    return " · ".join(labels)


def _split_structured_block(text: str, chunk_size: int, overlap: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        if end < text_length:
            end = _preferred_boundary(text, start, end, chunk_size)

        payload = text[start:end].strip()
        if payload:
            chunks.append(payload)

        if end >= text_length:
            break

        next_start = max(start + 1, end - overlap)
        while next_start < text_length and not text[next_start].isspace():
            next_start += 1
        while next_start < text_length and text[next_start].isspace():
            next_start += 1
        start = next_start

    return chunks


def _preferred_boundary(text: str, start: int, end: int, chunk_size: int) -> int:
    min_boundary = start + int(chunk_size * 0.6)

    paragraph_boundary = text.rfind("\n\n", min_boundary, end)
    if paragraph_boundary > start:
        return paragraph_boundary

    sentence_boundary = text.rfind(". ", min_boundary, end)
    if sentence_boundary > start:
        return sentence_boundary + 1

    word_boundary = text.rfind(" ", min_boundary, end)
    if word_boundary > start:
        return word_boundary

    return end
