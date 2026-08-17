# Retrieval quality evaluation

SoberanIA Labs Local RAG includes a small repository-safe retrieval evaluation harness. Its purpose is to make retrieval changes measurable before they are accepted into the local knowledge engine.

This is a project regression benchmark, not an industry benchmark and not a claim about general RAG quality.

## What it measures

The primary harness evaluates fixed, pre-chunked documents so retrieval ranking can
be compared independently from parser/chunking changes. It covers confusable Orion,
Harbor, Cedar and Atlas subjects plus multi-evidence and no-answer cases.

Metrics include document hit@1/hit@k, document/evidence recall, MRR, no-answer
accuracy and overall query success.

## Deterministic dense CI baseline

Run from `backend/`:

```powershell
uv run python -m sialabs_local_rag.evaluation --provider hash --mode dense
```

The recorded deterministic baseline remains in:

```text
backend/evaluation/baseline-hash.json
```

| Metric | Baseline |
| --- | ---: |
| Document hit@1 | 0.7143 |
| Document hit@requested-k | 1.0000 |
| Macro document recall@requested-k | 1.0000 |
| Macro evidence recall@requested-k | 1.0000 |
| MRR | 0.8333 |
| Negative no-answer accuracy | 0.0000 |
| Query success rate | 0.8750 |

Hash embeddings are deterministic CI scaffolding and are not suitable for choosing
a semantic-model relevance threshold.

## Hybrid retrieval comparison

Run the same corpus with hybrid retrieval:

```powershell
uv run python -m sialabs_local_rag.evaluation --provider hash --mode hybrid
```

CI rejects regressions in hit@1, hit@k, document/evidence recall, MRR and query
success. A separate `ZX-81` exact-code fixture proves lexical rescue over a dense
ranking decoy.

If FTS5 is unavailable, hybrid retrieval falls back to dense. Dense-only operation
can be forced with `RETRIEVAL_MODE=dense`.

## Structure-sensitive evaluation

Structure-aware ingestion adds a second small fixture:

```text
backend/evaluation/structure-cases.json
```

Unlike the primary pre-chunked benchmark, these cases deliberately pass through the
real parser and structure-aware chunker before retrieval. A case succeeds only when
the retrieved source contains the expected evidence **and** the expected structured
location metadata.

The first case uses a Markdown maintenance manual with `Inspection` and `Recovery`
sections. Querying `RECOVER-77` must recover:

- `section_title = Recovery`;
- `source_locator = section:Recovery`;
- the expected `RECOVER-77` evidence.

This fixture is executed by pytest and complements, rather than replaces, the
stable dense ranking baseline. Parser/chunker changes therefore have a concrete
regression target without forcing unrelated changes to the historical ranking
metrics.

PDF page preservation is covered separately by a real two-page text-PDF API test:
a source originating on page 2 must return `page_number = 2` and
`source_locator = page:2`.

## Relevance threshold sweeps

The evaluator accepts a minimum dense score:

```powershell
uv run python -m sialabs_local_rag.evaluation `
  --provider hash `
  --mode dense `
  --min-score 0.25
```

For a semantic embedding model, compare several thresholds against both positive
recall and no-answer behavior rather than choosing a cutoff from intuition.

## Optional real EmbeddingGemma evaluation

When Ollama and the configured embedding model are available locally:

```powershell
$env:OLLAMA_EMBED_MODEL = "embeddinggemma"
uv run python -m sialabs_local_rag.evaluation --provider ollama --mode hybrid
```

The real-model path is intentionally optional in ordinary CI because hardware,
model availability and runtime revisions should not make repository validation
nondeterministic.

## How retrieval/ingestion PRs should use the harness

1. Keep the recorded dense baseline stable unless dense ranking intentionally changes.
2. Compare hybrid and dense metrics on the same corpus when retrieval changes.
3. Add concrete repository fixtures for newly discovered failure cases.
4. For parser/chunking changes, add structure-sensitive cases that assert source location as well as evidence.
5. Run optional EmbeddingGemma evaluation when the local runtime is available.
6. Do not accept aggregate improvements that hide meaningful per-query regressions.

## What this does not measure

The current harness does not grade generated LLM answers, model throughput, OCR,
complex table reconstruction or general-domain semantic quality. Performance and
OCR/layout benchmarks are tracked separately from retrieval-quality regression
metrics.
