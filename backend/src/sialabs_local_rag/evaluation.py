from __future__ import annotations

import argparse
import asyncio
import json
from collections.abc import Iterable, Sequence
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal, cast

from pydantic import BaseModel, Field

from sialabs_local_rag.database import Database
from sialabs_local_rag.providers import (
    EmbeddingProvider,
    ProviderError,
    create_embedding_provider,
)
from sialabs_local_rag.schemas import SourceChunk
from sialabs_local_rag.settings import Settings
from sialabs_local_rag.storage import ChunkInput, Storage

_DEFAULT_EVALUATION_DIR = Path(__file__).resolve().parents[2] / "evaluation"


class EvaluationDocument(BaseModel):
    key: str = Field(min_length=1)
    title: str = Field(min_length=1)
    chunks: list[str] = Field(min_length=1)


class EvaluationCorpus(BaseModel):
    version: int = Field(ge=1)
    documents: list[EvaluationDocument] = Field(min_length=1)


class EvaluationQuestion(BaseModel):
    id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    expected_documents: list[str]
    expected_evidence: list[str]
    top_k: int = Field(ge=1, le=12)

    @property
    def expects_no_answer(self) -> bool:
        return not self.expected_documents and not self.expected_evidence


class EvaluationQuestionSet(BaseModel):
    version: int = Field(ge=1)
    questions: list[EvaluationQuestion] = Field(min_length=1)


class RetrievedChunkResult(BaseModel):
    document_title: str
    chunk_index: int
    score: float


class QueryEvaluationResult(BaseModel):
    id: str
    question: str
    top_k: int
    expected_documents: list[str]
    expected_evidence: list[str]
    retrieved: list[RetrievedChunkResult]
    first_relevant_rank: int | None
    document_hit_at_1: bool
    document_hit_at_k: bool
    document_recall_at_k: float
    evidence_recall_at_k: float
    no_answer_expected: bool
    no_answer_observed: bool
    success: bool


class EvaluationMetrics(BaseModel):
    total_queries: int
    positive_queries: int
    negative_queries: int
    document_hit_at_1: float
    document_hit_at_requested_k: float
    macro_document_recall_at_requested_k: float
    macro_evidence_recall_at_requested_k: float
    mean_reciprocal_rank: float
    negative_no_answer_accuracy: float
    query_success_rate: float


class EvaluationReport(BaseModel):
    corpus_version: int
    question_version: int
    embedding_provider: str
    embedding_model: str
    retrieval_min_score: float
    metrics: EvaluationMetrics
    queries: list[QueryEvaluationResult]


def load_corpus(path: Path) -> EvaluationCorpus:
    return EvaluationCorpus.model_validate_json(path.read_text(encoding="utf-8"))


def load_questions(path: Path) -> EvaluationQuestionSet:
    return EvaluationQuestionSet.model_validate_json(path.read_text(encoding="utf-8"))


async def run_evaluation(
    corpus: EvaluationCorpus,
    question_set: EvaluationQuestionSet,
    embedding_provider: EmbeddingProvider,
    minimum_score: float = 0.0,
) -> EvaluationReport:
    with TemporaryDirectory(prefix="sialabs-rag-eval-") as temp_dir:
        database = Database(f"sqlite:///{Path(temp_dir) / 'evaluation.db'}")
        database.init_schema()
        storage = Storage(database)
        await _index_corpus(storage, corpus.documents, embedding_provider)

        results: list[QueryEvaluationResult] = []
        for question in question_set.questions:
            results.append(
                await _evaluate_question(
                    storage,
                    question,
                    embedding_provider,
                    minimum_score,
                )
            )

    return EvaluationReport(
        corpus_version=corpus.version,
        question_version=question_set.version,
        embedding_provider=embedding_provider.name,
        embedding_model=embedding_provider.model,
        retrieval_min_score=minimum_score,
        metrics=_aggregate_metrics(results),
        queries=results,
    )


async def _index_corpus(
    storage: Storage,
    documents: Sequence[EvaluationDocument],
    embedding_provider: EmbeddingProvider,
) -> None:
    for document in documents:
        embeddings = await embedding_provider.embed(document.chunks)
        if len(embeddings) != len(document.chunks):
            raise ValueError(
                f"Embedding provider returned {len(embeddings)} vectors for "
                f"{len(document.chunks)} chunks in {document.key}."
            )
        chunks = [
            ChunkInput(index=index, content=content, embedding=embeddings[index])
            for index, content in enumerate(document.chunks)
        ]
        storage.create_document(
            title=document.title,
            source_type="evaluation",
            original_content="\n\n".join(document.chunks),
            chunks=chunks,
            embedding_provider=embedding_provider.name,
            embedding_model=embedding_provider.model,
        )


async def _evaluate_question(
    storage: Storage,
    question: EvaluationQuestion,
    embedding_provider: EmbeddingProvider,
    minimum_score: float,
) -> QueryEvaluationResult:
    query_embedding = (await embedding_provider.embed([question.question]))[0]
    sources = storage.search_chunks(
        query_embedding=query_embedding,
        top_k=question.top_k,
        embedding_provider=embedding_provider.name,
        embedding_model=embedding_provider.model,
        minimum_score=minimum_score,
    )

    retrieved_titles = [source.document_title for source in sources]
    expected_documents = set(question.expected_documents)
    matched_documents = expected_documents.intersection(retrieved_titles)

    if expected_documents:
        document_recall = len(matched_documents) / len(expected_documents)
        first_relevant_rank = _first_relevant_rank(sources, expected_documents)
        document_hit_at_1 = bool(sources and sources[0].document_title in expected_documents)
        document_hit_at_k = bool(matched_documents)
    else:
        document_recall = 1.0 if not sources else 0.0
        first_relevant_rank = None
        document_hit_at_1 = False
        document_hit_at_k = False

    evidence_recall = _evidence_recall(sources, question.expected_evidence)
    no_answer_observed = not sources

    if question.expects_no_answer:
        success = no_answer_observed
    else:
        success = document_recall == 1.0 and evidence_recall == 1.0

    return QueryEvaluationResult(
        id=question.id,
        question=question.question,
        top_k=question.top_k,
        expected_documents=question.expected_documents,
        expected_evidence=question.expected_evidence,
        retrieved=[
            RetrievedChunkResult(
                document_title=source.document_title,
                chunk_index=source.chunk_index,
                score=source.score,
            )
            for source in sources
        ],
        first_relevant_rank=first_relevant_rank,
        document_hit_at_1=document_hit_at_1,
        document_hit_at_k=document_hit_at_k,
        document_recall_at_k=document_recall,
        evidence_recall_at_k=evidence_recall,
        no_answer_expected=question.expects_no_answer,
        no_answer_observed=no_answer_observed,
        success=success,
    )


def _first_relevant_rank(
    sources: Sequence[SourceChunk],
    expected_documents: set[str],
) -> int | None:
    for rank, source in enumerate(sources, start=1):
        if source.document_title in expected_documents:
            return rank
    return None


def _evidence_recall(sources: Sequence[SourceChunk], expected_evidence: Sequence[str]) -> float:
    if not expected_evidence:
        return 1.0 if not sources else 0.0

    normalized_contents = [source.content.casefold() for source in sources]
    found = sum(
        1
        for evidence in expected_evidence
        if any(evidence.casefold() in content for content in normalized_contents)
    )
    return found / len(expected_evidence)


def _aggregate_metrics(results: Sequence[QueryEvaluationResult]) -> EvaluationMetrics:
    positive = [result for result in results if not result.no_answer_expected]
    negative = [result for result in results if result.no_answer_expected]

    return EvaluationMetrics(
        total_queries=len(results),
        positive_queries=len(positive),
        negative_queries=len(negative),
        document_hit_at_1=_average_bool(result.document_hit_at_1 for result in positive),
        document_hit_at_requested_k=_average_bool(
            result.document_hit_at_k for result in positive
        ),
        macro_document_recall_at_requested_k=_average(
            result.document_recall_at_k for result in positive
        ),
        macro_evidence_recall_at_requested_k=_average(
            result.evidence_recall_at_k for result in positive
        ),
        mean_reciprocal_rank=_average(
            0.0 if result.first_relevant_rank is None else 1.0 / result.first_relevant_rank
            for result in positive
        ),
        negative_no_answer_accuracy=_average_bool(
            result.no_answer_observed for result in negative
        ),
        query_success_rate=_average_bool(result.success for result in results),
    )


def _average(values: Iterable[float]) -> float:
    materialized = list(values)
    if not materialized:
        return 0.0
    return sum(materialized) / len(materialized)


def _average_bool(values: Iterable[bool]) -> float:
    materialized = list(values)
    if not materialized:
        return 0.0
    return sum(1 for value in materialized if value) / len(materialized)


def format_human_report(report: EvaluationReport) -> str:
    metrics = report.metrics
    lines = [
        f"Embedding: {report.embedding_provider}/{report.embedding_model}",
        f"Minimum score: {report.retrieval_min_score:.4f}",
        f"Queries: {metrics.total_queries} "
        f"({metrics.positive_queries} positive, {metrics.negative_queries} negative)",
        f"Document hit@1: {metrics.document_hit_at_1:.4f}",
        f"Document hit@requested-k: {metrics.document_hit_at_requested_k:.4f}",
        f"Macro document recall@requested-k: "
        f"{metrics.macro_document_recall_at_requested_k:.4f}",
        f"Macro evidence recall@requested-k: "
        f"{metrics.macro_evidence_recall_at_requested_k:.4f}",
        f"MRR: {metrics.mean_reciprocal_rank:.4f}",
        f"Negative no-answer accuracy: {metrics.negative_no_answer_accuracy:.4f}",
        f"Query success rate: {metrics.query_success_rate:.4f}",
        "",
        "Per-query results:",
    ]
    for result in report.queries:
        status = "PASS" if result.success else "FAIL"
        retrieved = ", ".join(
            f"{source.document_title}#{source.chunk_index} ({source.score:.3f})"
            for source in result.retrieved
        )
        lines.append(
            f"- {status} {result.id}: docs={result.document_recall_at_k:.2f}, "
            f"evidence={result.evidence_recall_at_k:.2f}; retrieved=[{retrieved}]"
        )
    return "\n".join(lines)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate SoberanIA Labs Local RAG retrieval quality."
    )
    parser.add_argument(
        "--provider",
        choices=("hash", "ollama"),
        default="hash",
        help="Embedding provider. Ollama uses OLLAMA_BASE_URL/OLLAMA_EMBED_MODEL settings.",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.0,
        help="Minimum cosine similarity required for a chunk to enter the result set.",
    )
    parser.add_argument(
        "--corpus",
        type=Path,
        default=_DEFAULT_EVALUATION_DIR / "corpus.json",
    )
    parser.add_argument(
        "--questions",
        type=Path,
        default=_DEFAULT_EVALUATION_DIR / "questions.json",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        help="Optional path for a machine-readable report.",
    )
    return parser


async def _run_from_args(args: argparse.Namespace) -> EvaluationReport:
    provider_name = cast(Literal["hash", "ollama"], args.provider)
    settings = Settings(embedding_provider=provider_name)
    provider = create_embedding_provider(settings)
    return await run_evaluation(
        corpus=load_corpus(cast(Path, args.corpus)),
        question_set=load_questions(cast(Path, args.questions)),
        embedding_provider=provider,
        minimum_score=cast(float, args.min_score),
    )


def main() -> int:
    args = build_argument_parser().parse_args()
    try:
        report = asyncio.run(_run_from_args(args))
    except (ProviderError, ValueError) as exc:
        print(f"Evaluation failed: {exc}")
        return 2

    print(format_human_report(report))
    output_path = cast(Path | None, args.json_output)
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(report.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"\nJSON report: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
