from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Literal, cast

from sialabs_local_rag.evaluation import load_corpus, load_questions
from sialabs_local_rag.providers import ProviderError, create_embedding_provider
from sialabs_local_rag.settings import Settings
from sialabs_local_rag.threshold_sweep import run_threshold_sweep


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sweep retrieval score gates with a deterministic or Ollama embedding provider."
    )
    parser.add_argument("--provider", choices=("hash", "ollama"), default="hash")
    parser.add_argument("--mode", choices=("dense", "hybrid"), default="hybrid")
    parser.add_argument(
        "--thresholds",
        default="0,0.05,0.1,0.15,0.2,0.25,0.3,0.35,0.4,0.45,0.5",
        help="Comma-separated minimum dense scores between 0 and 1.",
    )
    parser.add_argument(
        "--corpus",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "evaluation" / "corpus.json",
    )
    parser.add_argument(
        "--questions",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "evaluation" / "questions.json",
    )
    parser.add_argument("--json-output", type=Path)
    return parser


def parse_thresholds(raw: str) -> list[float]:
    thresholds = [float(value.strip()) for value in raw.split(",") if value.strip()]
    if not thresholds or any(value < 0 or value > 1 for value in thresholds):
        raise ValueError("Thresholds must contain at least one value between 0 and 1.")
    return thresholds


async def run(args: argparse.Namespace) -> dict[str, object]:
    provider_name = cast(Literal["hash", "ollama"], args.provider)
    mode = cast(Literal["dense", "hybrid"], args.mode)
    provider = create_embedding_provider(Settings(embedding_provider=provider_name))
    reports, recommended = await run_threshold_sweep(
        corpus=load_corpus(args.corpus),
        question_set=load_questions(args.questions),
        embedding_provider=provider,
        thresholds=parse_thresholds(args.thresholds),
        retrieval_mode=mode,
    )
    return {
        "embedding_provider": provider.name,
        "embedding_model": provider.model,
        "retrieval_mode": mode,
        "corpus_version": reports[0].corpus_version,
        "question_version": reports[0].question_version,
        "selection_rule": (
            "max query_success_rate, then negative_no_answer_accuracy, "
            "then evidence_recall; lowest threshold breaks final ties"
        ),
        "recommended_minimum_score": recommended.minimum_score,
        "rows": [
            {
                "minimum_score": report.retrieval_min_score,
                "query_success_rate": report.metrics.query_success_rate,
                "negative_no_answer_accuracy": report.metrics.negative_no_answer_accuracy,
                "evidence_recall": report.metrics.macro_evidence_recall_at_requested_k,
                "document_recall": report.metrics.macro_document_recall_at_requested_k,
            }
            for report in reports
        ],
    }


def main() -> int:
    args = build_parser().parse_args()
    try:
        payload = asyncio.run(run(args))
    except (ProviderError, ValueError) as error:
        print(f"Threshold sweep failed: {error}")
        return 2

    rendered = json.dumps(payload, indent=2, ensure_ascii=False)
    print(rendered)
    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(rendered + "\n", encoding="utf-8")
        print(f"\nJSON report: {args.json_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
