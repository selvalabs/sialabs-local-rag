from __future__ import annotations

import json
from pathlib import Path

import pytest

from sialabs_local_rag.evaluation import (
    format_human_report,
    load_corpus,
    load_questions,
    run_evaluation,
)
from sialabs_local_rag.providers import HashEmbeddingProvider

_EVALUATION_DIR = Path(__file__).resolve().parents[1] / "evaluation"


@pytest.mark.asyncio
async def test_hash_evaluation_matches_recorded_baseline() -> None:
    corpus = load_corpus(_EVALUATION_DIR / "corpus.json")
    questions = load_questions(_EVALUATION_DIR / "questions.json")
    report = await run_evaluation(corpus, questions, HashEmbeddingProvider())

    baseline = json.loads((_EVALUATION_DIR / "baseline-hash.json").read_text(encoding="utf-8"))

    assert report.corpus_version == baseline["corpus_version"]
    assert report.question_version == baseline["question_version"]
    assert report.embedding_provider == baseline["embedding_provider"]
    assert report.embedding_model == baseline["embedding_model"]

    recorded_metrics = baseline["metrics"]
    actual_metrics = report.metrics.model_dump()
    assert actual_metrics.keys() == recorded_metrics.keys()
    for metric, expected in recorded_metrics.items():
        assert actual_metrics[metric] == pytest.approx(expected), metric


@pytest.mark.asyncio
async def test_baseline_exposes_known_multi_chunk_and_no_answer_gaps() -> None:
    report = await run_evaluation(
        load_corpus(_EVALUATION_DIR / "corpus.json"),
        load_questions(_EVALUATION_DIR / "questions.json"),
        HashEmbeddingProvider(),
    )
    results = {result.id: result for result in report.queries}

    atlas = results["atlas-multi-evidence"]
    assert atlas.document_recall_at_k == 1.0
    assert atlas.evidence_recall_at_k == 0.5
    assert atlas.success is False
    assert [source.document_title for source in atlas.retrieved] == [
        "Atlas Reactor Procedure",
        "Atlas Training Bulletin",
    ]

    negative = results["negative-apollo"]
    assert negative.no_answer_expected is True
    assert negative.no_answer_observed is False
    assert negative.success is False


@pytest.mark.asyncio
async def test_evaluation_report_has_human_and_machine_readable_forms() -> None:
    report = await run_evaluation(
        load_corpus(_EVALUATION_DIR / "corpus.json"),
        load_questions(_EVALUATION_DIR / "questions.json"),
        HashEmbeddingProvider(),
    )

    human = format_human_report(report)
    machine = report.model_dump(mode="json")

    assert "Document hit@1" in human
    assert "Negative no-answer accuracy" in human
    assert "atlas-multi-evidence" in human
    assert machine["metrics"]["total_queries"] == 8
    assert len(machine["queries"]) == 8
