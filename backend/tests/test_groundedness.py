from sialabs_local_rag.groundedness import SourceEvidence, evaluate_answer


def test_grounded_answer_with_explicit_source_has_full_coverage() -> None:
    report = evaluate_answer(
        "The recovery window is 48 hours [S1].",
        [SourceEvidence(source_id="S1", content="The recovery window is 48 hours.")],
    )

    assert report.claim_count == 1
    assert report.grounded_claim_ratio == 1.0
    assert report.citation_coverage == 1.0
    assert report.unsupported_claims == ()


def test_unsupported_claim_is_reported_even_when_another_claim_is_grounded() -> None:
    report = evaluate_answer(
        "The recovery window is 48 hours [S1]. The budget is unlimited.",
        [SourceEvidence(source_id="S1", content="The recovery window is 48 hours.")],
    )

    assert report.claim_count == 2
    assert report.grounded_claim_ratio == 0.5
    assert report.citation_coverage == 0.5
    assert report.unsupported_claims == ("The budget is unlimited.",)


def test_refusal_without_claims_is_safe_and_does_not_require_citations() -> None:
    report = evaluate_answer(
        "I could not find that information in the indexed sources.",
        [SourceEvidence(source_id="S1", content="A recovery procedure.")],
    )

    assert report.claim_count == 0
    assert report.grounded_claim_ratio == 1.0
    assert report.citation_coverage == 1.0
