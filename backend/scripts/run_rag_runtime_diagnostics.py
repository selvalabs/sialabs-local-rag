from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

CASES = {
    "A1": {"num_ctx": 2048, "top_k": 1, "num_predict": 384, "num_gpu": 0, "think": False},
    "A2": {"num_ctx": 2048, "top_k": 2, "num_predict": 384, "num_gpu": 0, "think": False},
    "A3": {"num_ctx": 4096, "top_k": 2, "num_predict": 384, "num_gpu": 0, "think": False},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Exercise the local RAG chat path and print privacy-safe Ollama diagnostics."
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--case", choices=[*CASES, "all"], default="all")
    parser.add_argument(
        "--question", required=True, help="Question sent to the local app; never emitted."
    )
    parser.add_argument("--model", default="gemma4:e2b")
    parser.add_argument("--output", type=Path, help="Optional JSON results path.")
    return parser.parse_args()


def post_json(url: str, payload: dict[str, object]) -> tuple[int, dict[str, Any]]:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=300) as response:  # noqa: S310 - local diagnostic URL
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        return error.code, json.loads(error.read().decode("utf-8"))
    except URLError as error:
        return 0, {"detail": {"message": f"Local API connection failed: {error.reason}"}}


def safe_generation(value: object) -> dict[str, object]:
    allowed = {
        "failure_classification",
        "done",
        "done_reason",
        "total_duration",
        "load_duration",
        "prompt_eval_count",
        "prompt_eval_duration",
        "eval_count",
        "eval_duration",
        "content_chars",
        "thinking_present",
    }
    if not isinstance(value, dict):
        return {}
    return {key: item for key, item in value.items() if key in allowed}


def safe_diagnostics(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        return {}
    runtime = value.get("runtime") if isinstance(value.get("runtime"), dict) else {}
    retrieval = value.get("retrieval") if isinstance(value.get("retrieval"), dict) else {}
    prompt = value.get("prompt") if isinstance(value.get("prompt"), dict) else {}
    return {
        "runtime": {
            key: runtime[key]
            for key in ("model", "num_ctx", "num_predict", "num_gpu", "think")
            if key in runtime
        },
        "retrieval": {
            key: retrieval[key]
            for key in ("requested_top_k", "final_top_k", "selected_source_count", "retrieval_mode")
            if key in retrieval
        },
        "prompt": {
            key: prompt[key]
            for key in (
                "system_prompt_chars",
                "user_prompt_chars",
                "question_chars",
                "conversation_chars",
                "retrieved_evidence_chars",
                "source_wrapper_chars",
                "estimated_system_tokens",
                "estimated_user_tokens",
                "estimated_total_prompt_tokens",
            )
            if key in prompt
        },
        "generation": safe_generation(value.get("generation")),
    }


def run_case(name: str, config: dict[str, object], args: argparse.Namespace) -> dict[str, object]:
    runtime = {key: config[key] for key in ("num_ctx", "num_predict", "num_gpu", "think")}
    runtime["model"] = args.model
    payload = {"question": args.question, "top_k": config["top_k"], "runtime_options": runtime}
    started = time.perf_counter()
    status, body = post_json(f"{args.base_url.rstrip('/')}/api/chat", payload)
    latency_ms = int((time.perf_counter() - started) * 1000)
    if 200 <= status < 300:
        sources = body.get("sources") if isinstance(body.get("sources"), list) else []
        return {
            "case": name,
            "success": True,
            "latency_ms": latency_ms,
            "runtime": runtime,
            "top_k": config["top_k"],
            "selected_source_count": len(sources),
            "selected_source_ids": [
                source.get("chunk_id") for source in sources if isinstance(source, dict)
            ],
            "diagnostics": safe_diagnostics(body.get("diagnostics")),
        }

    detail = body.get("detail") if isinstance(body, dict) else None
    structured = detail if isinstance(detail, dict) else {}
    diagnostics = safe_diagnostics(structured.get("diagnostics"))
    generation = diagnostics.get("generation", {})
    return {
        "case": name,
        "success": False,
        "status_code": status,
        "latency_ms": latency_ms,
        "runtime": runtime,
        "top_k": config["top_k"],
        "failure_classification": generation.get("failure_classification"),
        "diagnostics": diagnostics,
    }


def main() -> int:
    args = parse_args()
    selected = CASES.items() if args.case == "all" else [(args.case, CASES[args.case])]
    results = [run_case(name, config, args) for name, config in selected]
    rendered = json.dumps(results, ensure_ascii=False, indent=2)
    print(rendered)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    return 0 if all(result["success"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
