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

## Deterministic dense CI baseline

Run from `backend/`:

```powershell
uv run python -m sialabs_local_rag.evaluation --provider hash --mode dense
```

Write a machine-readable report with:

```powershell
uv run python -m sialabs_local_rag.evaluation `
  --provider hash `
  --mode dense `
  --json-output .\evaluation\latest-hash-report.json
```

The deterministic dense baseline is stored in:

```text
backend/evaluation/baseline-hash.json
```

The backend pytest suite recomputes the hash-provider dense evaluation and compares its aggregate metrics with that recorded baseline.

### Current dense hash baseline

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

## Hybrid retrieval comparison

The application defaults to hybrid retrieval when SQLite FTS5 is available. Hybrid mode builds dense and lexical candidate pools independently and combines their ranks with weighted Reciprocal Rank Fusion (RRF).

Run the same repository evaluation in hybrid mode:

```powershell
uv run python -m sialabs_local_rag.evaluation --provider hash --mode hybrid
```

The CI test suite compares hybrid metrics against the recorded dense baseline and rejects regressions in:

- document hit@1;
- document hit@requested-k;
- macro document recall;
- macro evidence recall;
- MRR;
- overall query success rate.

A separate deterministic test covers the lexical-rescue case directly: a `ZX-81` exact-code query is constructed so dense ranking chooses a semantic decoy while FTS5 identifies the literal code; weighted RRF must promote the correct lexical document.

Hybrid source results include optional debugging metadata such as dense rank, lexical rank, dense score and fusion score. This metadata is intended for evaluation and diagnostics, not for answer prose.

If FTS5 is unavailable, hybrid retrieval falls back to the dense path. Dense-only behavior can also be forced with:

```text
RETRIEVAL_MODE=dense
```

## Relevance threshold sweeps

The evaluator accepts the same minimum-score concept used by the dense candidate pool:

```powershell
uv run python -m sialabs_local_rag.evaluation `
  --provider hash `
  --mode dense `
  --min-score 0.25
```

For a real semantic embedding model, run several values and compare positive recall against no-answer behavior rather than selecting a threshold from intuition. In hybrid mode, the threshold filters dense candidates; lexical candidates remain independently eligible for RRF fusion.

## Optional real EmbeddingGemma evaluation

When Ollama and the configured embedding model are available locally:

```powershell
$env:OLLAMA_EMBED_MODEL = "embeddinggemma"
uv run python -m sialabs_local_rag.evaluation --provider ollama --mode hybrid
```

Threshold sweep example:

```powershell
uv run python -m sialabs_local_rag.evaluation --provider ollama --mode hybrid --min-score 0.20
uv run python -m sialabs_local_rag.evaluation --provider ollama --mode hybrid --min-score 0.30
uv run python -m sialabs_local_rag.evaluation --provider ollama --mode hybrid --min-score 0.40
```

These numbers are examples of values to test, not recommended EmbeddingGemma defaults. The chosen production cutoff should be based on observed retrieval results for the actual model/runtime and representative documents.

The Ollama path uses the same corpus, questions and metrics, but it is intentionally not required by CI. Hardware, local model availability and model/runtime revisions should not make ordinary repository validation nondeterministic.

A real-model report can be written with `--json-output` for before/after comparisons.

## How retrieval PRs should use the harness

For changes such as relevance gating, hybrid retrieval or query rewriting:

1. Run the deterministic dense baseline before the change.
2. Implement the retrieval change in its own branch.
3. Run dense and candidate retrieval modes against the same corpus/questions.
4. Inspect both aggregate metrics and per-query rankings.
5. Run the optional Ollama/EmbeddingGemma evaluation when local runtime is available.
6. Update `baseline-hash.json` only when changed dense deterministic behavior is intentional and justified in the PR.
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
