# Retrieval quality evaluation

SoberanIA Labs Local RAG includes a small repository-safe retrieval evaluation harness. Its purpose is to make retrieval changes measurable before they are accepted into the local knowledge engine.

This is a project regression benchmark, not an industry benchmark and not a claim about general RAG quality.

## What it measures

The harness evaluates fixed, pre-chunked documents so retrieval behavior can be compared independently from future chunking/parser changes.

The corpus intentionally contains confusable subjects:

- Orion operations vs. Orion astronomy;
- Harbor finance vs. Harbor weather;
- Cedar remote-work policy vs. Cedar botany;
- Atlas reactor procedure vs. Atlas training material.

It also contains:

- a multi-evidence Atlas question where two relevant chunks belong to the same document;
- a negative Apollo 11 question whose answer does not exist anywhere in the corpus.

Metrics include:

- document hit@1;
- document hit at each question's requested `top_k`;
- macro document recall at requested `top_k`;
- macro evidence recall at requested `top_k`;
- mean reciprocal rank (MRR);
- negative/no-answer accuracy;
- overall query success rate.

A positive query succeeds only when all expected documents and all expected evidence markers are recovered. A negative query succeeds only when retrieval returns no sources.

## Deterministic CI baseline

Run from `backend/`:

```powershell
uv run python -m sialabs_local_rag.evaluation --provider hash
```

Write a machine-readable report with:

```powershell
uv run python -m sialabs_local_rag.evaluation `
  --provider hash `
  --json-output .\evaluation\latest-hash-report.json
```

The deterministic baseline is stored in:

```text
backend/evaluation/baseline-hash.json
```

The backend pytest suite recomputes the hash-provider evaluation and compares its aggregate metrics with that recorded baseline.

### Current hash baseline

| Metric | Baseline |
| --- | ---: |
| Document hit@1 | 0.7143 |
| Document hit@requested-k | 1.0000 |
| Macro document recall@requested-k | 1.0000 |
| Macro evidence recall@requested-k | 0.9286 |
| MRR | 0.8333 |
| Negative no-answer accuracy | 0.0000 |
| Query success rate | 0.7500 |

These values are intentionally not presented as good semantic-model scores. Hash embeddings are deterministic test scaffolding.

The useful part of this baseline is that it records known behavior before retrieval changes:

1. The Apollo negative query still returns unrelated chunks because there is no relevance threshold.
2. The Atlas query recovers the correct document but only one of its two required evidence chunks at `top_k=2`, because the current retriever forces document diversity before selecting a second chunk from the same document.

Those are explicit regression targets for later retrieval work.

## Optional real EmbeddingGemma evaluation

When Ollama and the configured embedding model are available locally:

```powershell
$env:OLLAMA_EMBED_MODEL = "embeddinggemma"
uv run python -m sialabs_local_rag.evaluation --provider ollama
```

The Ollama path uses the same corpus, questions and metrics, but it is intentionally not required by CI. Hardware, local model availability and model/runtime revisions should not make ordinary repository validation nondeterministic.

A real-model report can be written with `--json-output` for before/after comparisons.

## How retrieval PRs should use the harness

For changes such as relevance gating, hybrid retrieval or query rewriting:

1. Run the deterministic baseline before the change.
2. Implement the retrieval change in its own branch.
3. Run the evaluator again.
4. Inspect both aggregate metrics and per-query rankings.
5. Run the optional Ollama/EmbeddingGemma evaluation when local runtime is available.
6. Update `baseline-hash.json` only when the changed deterministic behavior is intentional and justified in the PR.
7. Do not accept an aggregate improvement that hides a meaningful regression in an important individual query without documenting the trade-off.

The evaluation fixtures are deliberately small enough to review in Git. New failure cases should be added as concrete corpus/questions rather than hidden in ad-hoc local tests.

## What this does not measure

The current harness does not grade generated LLM answers. It measures retrieval only.

It also does not measure:

- cold-start or warm model latency;
- tokens per second;
- sustained-load performance;
- OCR/parser quality;
- general-domain semantic retrieval quality.

Performance benchmarking should separately distinguish cold model loading from warm repeated inference. Retrieval-quality metrics should not be mixed with model startup latency.
