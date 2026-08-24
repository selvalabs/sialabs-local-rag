# EmbeddingGemma threshold sweep

This report calibrates the dense-score gate used by hybrid retrieval against the versioned evaluation corpus (`corpus_version=1`, `question_version=2`). It was run locally on 2026-08-24 with Ollama `embeddinggemma` and hybrid retrieval.

Command:

```powershell
cd backend
uv run python scripts/run_threshold_sweep.py `
  --provider ollama `
  --mode hybrid `
  --thresholds 0,0.05,0.1,0.15,0.2,0.25,0.3,0.35,0.4,0.45,0.5 `
  --json-output evaluation/threshold-sweep-embeddinggemma.json
```

The selection rule maximizes query success rate, then negative no-answer accuracy, then evidence recall; the lowest threshold breaks final ties.

| Minimum score | Query success | No-answer accuracy | Evidence recall | Document recall |
| ---: | ---: | ---: | ---: | ---: |
| 0.00 | 0.8947 | 0.0000 | 1.0000 | 1.0000 |
| 0.05 | 0.8947 | 0.0000 | 1.0000 | 1.0000 |
| 0.10 | 0.8947 | 0.0000 | 1.0000 | 1.0000 |
| 0.15 | 0.8947 | 0.0000 | 1.0000 | 1.0000 |
| 0.20 | 0.9474 | 0.5000 | 1.0000 | 1.0000 |
| **0.25** | **1.0000** | **1.0000** | **1.0000** | **1.0000** |
| 0.30–0.50 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

The calibrated default is **0.25**. This is a corpus-specific regression decision, not a universal semantic threshold; new corpora, embedding models or retrieval weights require a new sweep. The machine-readable report is checked in at `backend/evaluation/threshold-sweep-embeddinggemma.json`, with the deterministic hash-provider control at `backend/evaluation/threshold-sweep-hash.json`.
