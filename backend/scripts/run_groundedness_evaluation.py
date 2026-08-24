from __future__ import annotations

import argparse
import json
from pathlib import Path

from sialabs_local_rag.groundedness import SourceEvidence, evaluate_answer


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic groundedness/citation checks.")
    parser.add_argument(
        "--cases",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "evaluation" / "groundedness-cases.json",
    )
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()

    fixture = json.loads(args.cases.read_text(encoding="utf-8"))
    results = []
    for case in fixture["cases"]:
        report = evaluate_answer(
            case["answer"],
            [SourceEvidence(**source) for source in case["sources"]],
        )
        results.append({"id": case["id"], **report.__dict__})

    report = {
        "fixture_version": fixture["version"],
        "metric_definition": "lexical source overlap plus explicit [S#] coverage; not an LLM judge",
        "cases": results,
        "unsupported_case_count": sum(1 for result in results if result["unsupported_claims"]),
        "mean_grounded_claim_ratio": sum(
            result["grounded_claim_ratio"] for result in results
        ) / len(results),
        "mean_citation_coverage": sum(result["citation_coverage"] for result in results)
        / len(results),
    }
    rendered = json.dumps(report, indent=2, ensure_ascii=False)
    print(rendered)
    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(rendered + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
