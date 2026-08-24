from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from sialabs_local_rag.evaluation import (
    EvaluationCorpus,
    EvaluationQuestionSet,
    EvaluationReport,
    run_evaluation,
)
from sialabs_local_rag.providers import EmbeddingProvider
from sialabs_local_rag.retrieval import RetrievalMode


@dataclass(frozen=True)
class ThresholdSweepRow:
    minimum_score: float
    query_success_rate: float
    negative_no_answer_accuracy: float
    evidence_recall: float
    document_recall: float = 0.0


def choose_recommended_threshold(
    rows: Sequence[ThresholdSweepRow],
) -> ThresholdSweepRow:
    """Select the highest-quality cutoff with conservative no-answer tie-breaking."""

    if not rows:
        raise ValueError("Threshold sweep requires at least one row.")
    return max(
        rows,
        key=lambda row: (
            row.query_success_rate,
            row.negative_no_answer_accuracy,
            row.evidence_recall,
            -row.minimum_score,
        ),
    )


async def run_threshold_sweep(
    corpus: EvaluationCorpus,
    question_set: EvaluationQuestionSet,
    embedding_provider: EmbeddingProvider,
    thresholds: Sequence[float],
    retrieval_mode: RetrievalMode = "hybrid",
) -> tuple[list[EvaluationReport], ThresholdSweepRow]:
    """Run identical retrieval evaluations across minimum-score cutoffs."""

    reports = [
        await run_evaluation(
            corpus=corpus,
            question_set=question_set,
            embedding_provider=embedding_provider,
            minimum_score=threshold,
            retrieval_mode=retrieval_mode,
        )
        for threshold in thresholds
    ]
    rows = [
        ThresholdSweepRow(
            minimum_score=report.retrieval_min_score,
            query_success_rate=report.metrics.query_success_rate,
            negative_no_answer_accuracy=report.metrics.negative_no_answer_accuracy,
            evidence_recall=report.metrics.macro_evidence_recall_at_requested_k,
            document_recall=report.metrics.macro_document_recall_at_requested_k,
        )
        for report in reports
    ]
    return reports, choose_recommended_threshold(rows)
