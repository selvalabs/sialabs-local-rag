# Groundedness and citation regression

The repository includes a deterministic harness for a narrow question: does
each answer claim overlap with retrieved source text, and does a claim carry an
explicit source ID such as `[S1]`? It is intentionally not an LLM judge and
does not claim general answer quality.

Run it with:

```powershell
cd backend
uv run python scripts/run_groundedness_evaluation.py `
  --json-output evaluation/groundedness-citation-regression.json
```

The fixture contains a grounded cited claim, an unsupported claim next to a
grounded claim, and a safe refusal.

| Metric | Result |
| --- | ---: |
| Mean grounded-claim ratio | 0.8333 |
| Mean citation coverage | 0.8333 |
| Cases with unsupported claims | 1 |

This is a regression signal for source/evidence boundaries. Semantic entailment,
answer completeness and model hallucination remain outside its scope.
