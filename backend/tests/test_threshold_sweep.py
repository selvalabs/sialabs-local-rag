from sialabs_local_rag.settings import Settings
from sialabs_local_rag.threshold_sweep import (
    ThresholdSweepRow,
    choose_recommended_threshold,
)


def test_threshold_selection_prefers_query_success_then_no_answer_accuracy() -> None:
    rows = [
        ThresholdSweepRow(
            minimum_score=0.0,
            query_success_rate=0.70,
            negative_no_answer_accuracy=0.50,
            evidence_recall=0.90,
        ),
        ThresholdSweepRow(
            minimum_score=0.25,
            query_success_rate=0.80,
            negative_no_answer_accuracy=0.80,
            evidence_recall=0.80,
        ),
        ThresholdSweepRow(
            minimum_score=0.50,
            query_success_rate=0.80,
            negative_no_answer_accuracy=0.90,
            evidence_recall=0.70,
        ),
    ]

    selected = choose_recommended_threshold(rows)

    assert selected.minimum_score == 0.50


def test_threshold_selection_rejects_empty_sweep() -> None:
    try:
        choose_recommended_threshold([])
    except ValueError as error:
        assert str(error) == "Threshold sweep requires at least one row."
    else:
        raise AssertionError("empty threshold sweep should fail")


def test_default_retrieval_gate_uses_embeddinggemma_calibration() -> None:
    assert Settings().retrieval_min_score == 0.25
