from __future__ import annotations

import re
from dataclasses import dataclass

_CITATION_RE = re.compile(r"\[S(\d+)\]|\bS(\d+)\b", re.IGNORECASE)
_TOKEN_RE = re.compile(r"[\wÀ-ÿ]+", re.UNICODE)
_REFUSAL_MARKERS = (
    "could not find",
    "not found in the indexed",
    "no relevant source",
    "não encontrei",
    "não há informação",
)


@dataclass(frozen=True)
class SourceEvidence:
    source_id: str
    content: str


@dataclass(frozen=True)
class GroundednessReport:
    claim_count: int
    grounded_claim_count: int
    cited_claim_count: int
    grounded_claim_ratio: float
    citation_coverage: float
    cited_source_ids: tuple[str, ...]
    unsupported_claims: tuple[str, ...]


def evaluate_answer(
    answer: str,
    sources: list[SourceEvidence],
) -> GroundednessReport:
    """Measure lexical support and explicit source-ID coverage for an answer.

    This is a deterministic regression signal, not a semantic judge. A claim is
    considered supported when at least two meaningful tokens overlap a source;
    a citation counts only when its cited source also supports that claim.
    """

    claims = [
        sentence
        for sentence in _split_sentences(answer)
        if _claim_tokens(sentence) and not _is_refusal(sentence)
    ]
    source_tokens = {
        source.source_id: _claim_tokens(source.content) for source in sources
    }
    grounded_claims = 0
    cited_claims = 0
    unsupported: list[str] = []
    cited_source_ids = sorted(set(_citation_ids(answer)))

    for claim in claims:
        claim_tokens = _claim_tokens(claim)
        supporting_ids = [
            source_id
            for source_id, tokens in source_tokens.items()
            if len(claim_tokens.intersection(tokens)) >= 2
        ]
        if not supporting_ids:
            unsupported.append(claim)
            continue
        grounded_claims += 1
        if set(supporting_ids).intersection(_citation_ids(claim)):
            cited_claims += 1

    claim_count = len(claims)
    if claim_count == 0:
        return GroundednessReport(
            claim_count=0,
            grounded_claim_count=0,
            cited_claim_count=0,
            grounded_claim_ratio=1.0,
            citation_coverage=1.0,
            cited_source_ids=tuple(cited_source_ids),
            unsupported_claims=(),
        )

    return GroundednessReport(
        claim_count=claim_count,
        grounded_claim_count=grounded_claims,
        cited_claim_count=cited_claims,
        grounded_claim_ratio=grounded_claims / claim_count,
        citation_coverage=cited_claims / claim_count,
        cited_source_ids=tuple(cited_source_ids),
        unsupported_claims=tuple(unsupported),
    )


def _split_sentences(text: str) -> list[str]:
    parts = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
    sentences: list[str] = []
    for part in parts:
        if sentences and re.fullmatch(r"(?:\[S\d+\]|S\d+)", part, re.IGNORECASE):
            sentences[-1] = f"{sentences[-1]} {part}"
        else:
            sentences.append(part)
    return sentences


def _citation_ids(text: str) -> list[str]:
    return [f"S{match[0] or match[1]}" for match in _CITATION_RE.findall(text)]


def _claim_tokens(text: str) -> set[str]:
    citations_removed = _CITATION_RE.sub(" ", text.casefold())
    return {
        token
        for token in _TOKEN_RE.findall(citations_removed)
        if len(token) >= 3
    }


def _is_refusal(text: str) -> bool:
    normalized = text.casefold()
    return any(marker in normalized for marker in _REFUSAL_MARKERS)
