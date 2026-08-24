# ADR: retrieval scale decision

## Status

Benchmark harness added; vector-index decision pending measured results from the
target machine.

## Decision

Keep the transparent SQLite plus brute-force dense search as the default until
the versioned scale benchmark shows a concrete bottleneck. The benchmark covers
1,000, 5,000, 10,000, 25,000 and 50,000 synthetic chunks and records ingestion,
database size, query embedding, cold/warm dense retrieval and warm hybrid
retrieval timings.

The corpus uses deterministic hash embeddings, so results are a local regression
signal rather than a production performance claim. A future vector extension
must provide a migration and brute-force fallback before replacing this path.
