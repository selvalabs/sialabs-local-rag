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

The current relevance-first retriever uses a conservative `0.0` minimum score in the deterministic baseline.

| Metric | Baseline |
| --- | ---: |
| Document hit@1 | 0.7143 |
| Document hit@requested-k | 1.0000 |
| Macro document recall@requested-k | 1.0000 |
| Macro evidence recall@requested-k | 1.0000 |
| MRR | 0.8333 |
| Negative no-answer accuracy | 0.0000 |
| Query success rate | 0.8750 |

Compared with the pre-relevance-first baseline, macro evidence recall improved from `0.9286` to `1.0000` and query success improved from `0.7500` to `0.8750`, while the other recorded aggregate metrics did not regress.

The concrete improvement is the Atlas case: the two strongest chunks both come from `Atlas Reactor Procedure`, so both required safeguards are now retrieved at `top_k=2`. The retriever no longer inserts a weaker second document merely to increase document diversity.

The remaining negative-query gap is different: deterministic hash embeddings produce positive collision scores for unrelated content, so the conservative `0.0` threshold does not reject the Apollo query. Hash mode is therefore useful for deterministic ranking regression tests but not for choosing a production semantic-model score cutoff.

## Relevance threshold sweeps

The evaluator accepts the same minimum-score concept used by the application:

```powershell
uv run python -m sialabs_local_rag.evaluation `
  --provider hash `
  --min-score 0.25
```

For a real semantic embedding model, run several values and compare positive recall against no-answer behavior rather than selecting a threshold from intuition.

## Optional real EmbeddingGemma evaluation

When Ollama and the configured embedding model are available locally:

```powershell
$env:OLLAMA_EMBED_MODEL = "embeddinggemma"
uv run python -m sialabs_local_rag.evaluation --provider ollama
```

Threshold sweep example:

```powershell
uv run python -m sialabs_local_rag.evaluation --provider ollama --min-score 0.20
uv run python -m sialabs_local_rag.evaluation --provider ollama --min-score 0.30
uv run python -m sialabs_local_rag.evaluation --provider ollama --min-score 0.40
```

These numbers are examples of values to test, not recommended EmbeddingGemma defaults. The chosen production cutoff should be based on observed retrieval results for the actual model/runtime and representative documents.

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
