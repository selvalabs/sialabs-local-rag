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
    assert report.retrieval_mode == "dense"
    assert report.retrieval_min_score == pytest.approx(baseline["retrieval_min_score"])

    recorded_metrics = baseline["metrics"]
    actual_metrics = report.metrics.model_dump()
    assert actual_metrics.keys() == recorded_metrics.keys()
    for metric, expected in recorded_metrics.items():
        assert actual_metrics[metric] == pytest.approx(expected), metric


@pytest.mark.asyncio
async def test_hybrid_evaluation_is_no_worse_than_dense_baseline() -> None:
    corpus = load_corpus(_EVALUATION_DIR / "corpus.json")
    questions = load_questions(_EVALUATION_DIR / "questions.json")
    provider = HashEmbeddingProvider()

    dense = await run_evaluation(corpus, questions, provider, retrieval_mode="dense")
    hybrid = await run_evaluation(corpus, questions, provider, retrieval_mode="hybrid")

    assert hybrid.metrics.document_hit_at_1 >= dense.metrics.document_hit_at_1
    assert (
        hybrid.metrics.document_hit_at_requested_k
        >= dense.metrics.document_hit_at_requested_k
    )
    assert (
        hybrid.metrics.macro_document_recall_at_requested_k
        >= dense.metrics.macro_document_recall_at_requested_k
    )
    assert (
        hybrid.metrics.macro_evidence_recall_at_requested_k
        >= dense.metrics.macro_evidence_recall_at_requested_k
    )
    assert hybrid.metrics.mean_reciprocal_rank >= dense.metrics.mean_reciprocal_rank
    assert hybrid.metrics.query_success_rate >= dense.metrics.query_success_rate


@pytest.mark.asyncio
async def test_baseline_captures_atlas_improvement_and_remaining_no_answer_gap() -> None:
    report = await run_evaluation(
        load_corpus(_EVALUATION_DIR / "corpus.json"),
        load_questions(_EVALUATION_DIR / "questions.json"),
        HashEmbeddingProvider(),
    )
    results = {result.id: result for result in report.queries}

    atlas = results["atlas-multi-evidence"]
    assert atlas.document_recall_at_k == 1.0
    assert atlas.evidence_recall_at_k == 1.0
    assert atlas.success is True
    assert [source.document_title for source in atlas.retrieved] == [
        "Atlas Reactor Procedure",
        "Atlas Reactor Procedure",
    ]
    assert [source.chunk_index for source in atlas.retrieved] == [0, 1]

    negative = results["negative-apollo"]
    assert negative.no_answer_expected is True
    assert negative.no_answer_observed is False
    assert negative.success is False


@pytest.mark.asyncio
async def test_evaluation_can_sweep_minimum_score() -> None:
    report = await run_evaluation(
        load_corpus(_EVALUATION_DIR / "corpus.json"),
        load_questions(_EVALUATION_DIR / "questions.json"),
        HashEmbeddingProvider(),
        minimum_score=0.25,
    )

    assert report.retrieval_min_score == 0.25
    assert all(
        source.score >= 0.25
        for result in report.queries
        for source in result.retrieved
    )


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
    assert "Retrieval mode" in human
    assert "Minimum dense score" in human
    assert "Negative no-answer accuracy" in human
    assert "atlas-multi-evidence" in human
    assert machine["retrieval_mode"] == "dense"
    assert machine["retrieval_min_score"] == 0.0
    assert machine["metrics"]["total_queries"] == 8
    assert len(machine["queries"]) == 8
