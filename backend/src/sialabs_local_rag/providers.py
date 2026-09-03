from __future__ import annotations

import hashlib
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

import httpx

from sialabs_local_rag.schemas import GenerationDiagnostics
from sialabs_local_rag.settings import Settings
from sialabs_local_rag.vector_math import normalize_vector

_OLLAMA_DETAIL_LIMIT = 500
_OLLAMA_OOM_RE = re.compile(
    r"(?:cuda|gpu|llama-server)[^\n]{0,120}(?:out of memory|oom)|"
    r"(?:out of memory|oom)[^\n]{0,120}(?:cuda|gpu|llama-server)",
    re.IGNORECASE,
)
_SECRET_RE = re.compile(
    r"(?i)(bearer\s+|(?:api[_-]?key|token|password|secret)\s*[:=]\s*)[^\s,;]+"
)
_URL_CREDENTIAL_RE = re.compile(r"(?i)(https?://)([^/@\s]+):([^/@\s]+)@")
_OLLAMA_OOM_MESSAGE = (
    "The local model could not start because GPU memory was exhausted. "
    "Try the Economy profile (GPU 0 / CPU mode) or reduce GPU usage."
)

_TOKEN_RE = re.compile(r"[\wÀ-ÿ]+", re.UNICODE)


class ProviderError(RuntimeError):
    """Raised when an external AI provider cannot complete a request."""

    def __init__(self, message: str, diagnostics: GenerationDiagnostics | None = None) -> None:
        super().__init__(message)
        self.diagnostics = diagnostics


@dataclass(frozen=True)
class ChatGenerationResult:
    content: str
    diagnostics: GenerationDiagnostics


def format_ollama_http_error(response: httpx.Response, operation: str) -> str:
    """Return bounded, sanitized diagnostics for an unsuccessful Ollama response."""
    detail = ""
    try:
        body = response.json()
    except ValueError:
        body = None

    if isinstance(body, dict) and isinstance(body.get("error"), str):
        detail = body["error"]
    else:
        detail = response.text

    detail = _SECRET_RE.sub(r"\1[redacted]", detail)
    detail = _URL_CREDENTIAL_RE.sub(r"\1[redacted]@", detail)
    detail = " ".join(detail.split())[:_OLLAMA_DETAIL_LIMIT]
    if _OLLAMA_OOM_RE.search(detail):
        diagnostic = _OLLAMA_OOM_MESSAGE
    else:
        diagnostic = f"Ollama {operation} request failed with HTTP {response.status_code}."

    return f"{diagnostic} Ollama detail: {detail}" if detail else diagnostic


@dataclass(frozen=True)
class ChatRuntimeOptions:
    model: str | None = None
    num_ctx: int | None = None
    num_gpu: int | None = None
    keep_alive: str | None = None
    temperature: float | None = None
    think: bool | None = None
    num_predict: int | None = None


class EmbeddingProvider(Protocol):
    name: str
    model: str

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Return embeddings for the provided texts."""


class ChatProvider(Protocol):
    name: str
    model: str

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        runtime_options: ChatRuntimeOptions | None = None,
    ) -> ChatGenerationResult:
        """Generate an answer from prompts."""


class HashEmbeddingProvider:
    """Deterministic local embeddings for tests, CI and offline demos.

    This is intentionally simple. It is not a semantic model, but it allows
    the full RAG pipeline to run without external dependencies.
    """

    name = "hash"
    model = "hash-bow-128"

    def __init__(self, dimension: int = 128) -> None:
        self.dimension = dimension

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0 for _ in range(self.dimension)]
        tokens = _TOKEN_RE.findall(text.lower())

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        return normalize_vector(vector)


class OllamaEmbeddingProvider:
    name = "ollama"

    def __init__(self, base_url: str, model: str, timeout_seconds: float) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []

        payload = {"model": self.model, "input": list(texts)}
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(f"{self.base_url}/api/embed", json=payload)
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise ProviderError(format_ollama_http_error(exc.response, "embedding")) from exc
        except httpx.HTTPError as exc:
            raise ProviderError(f"Ollama embedding request failed: {exc}") from exc

        data = response.json()
        embeddings_raw = data.get("embeddings")
        if not isinstance(embeddings_raw, list) or len(embeddings_raw) != len(texts):
            raise ProviderError("Ollama embedding response did not match the requested inputs.")

        embeddings: list[list[float]] = []
        for item in embeddings_raw:
            if not isinstance(item, list):
                raise ProviderError("Ollama returned an invalid embedding item.")
            embeddings.append([float(value) for value in item])

        return embeddings


class MockChatProvider:
    name = "mock"
    model = "deterministic-local-mock"

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        runtime_options: ChatRuntimeOptions | None = None,
    ) -> ChatGenerationResult:
        del system_prompt, runtime_options
        context_lines = [line for line in user_prompt.splitlines() if line.startswith("Fonte")]
        source_count = len(context_lines)
        content = (
            "Resposta simulada para validação local. "
            f"Foram usadas {source_count} fontes recuperadas. "
            "Ative LLM_PROVIDER=ollama para gerar respostas com Gemma via Ollama."
        )
        return ChatGenerationResult(
            content=content,
            diagnostics=GenerationDiagnostics(content_chars=len(content)),
        )


class OllamaChatProvider:
    name = "ollama"

    def __init__(
        self,
        base_url: str,
        model: str,
        timeout_seconds: float,
        temperature: float,
        num_ctx: int | None,
        num_gpu: int | None,
        keep_alive: str | None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.temperature = temperature
        self.num_ctx = num_ctx
        self.num_gpu = num_gpu
        self.keep_alive = keep_alive

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        runtime_options: ChatRuntimeOptions | None = None,
    ) -> ChatGenerationResult:
        model = runtime_options.model if runtime_options and runtime_options.model else self.model
        temperature = (
            runtime_options.temperature
            if runtime_options and runtime_options.temperature is not None
            else self.temperature
        )
        num_ctx = (
            runtime_options.num_ctx
            if runtime_options and runtime_options.num_ctx is not None
            else self.num_ctx
        )
        num_gpu = (
            runtime_options.num_gpu
            if runtime_options and runtime_options.num_gpu is not None
            else self.num_gpu
        )
        keep_alive = (
            runtime_options.keep_alive
            if runtime_options and runtime_options.keep_alive is not None
            else self.keep_alive
        )

        options: dict[str, float | int] = {"temperature": temperature}
        if num_ctx is not None:
            options["num_ctx"] = num_ctx
        if num_gpu is not None:
            options["num_gpu"] = num_gpu
        if runtime_options and runtime_options.num_predict is not None:
            options["num_predict"] = runtime_options.num_predict

        payload: dict[str, object] = {
            "model": model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "options": options,
        }
        if keep_alive:
            payload["keep_alive"] = keep_alive
        if runtime_options and runtime_options.think is not None:
            payload["think"] = runtime_options.think

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(f"{self.base_url}/api/chat", json=payload)
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise ProviderError(
                format_ollama_http_error(exc.response, "chat"),
                GenerationDiagnostics(
                    failure_classification=(
                        "gpu_oom"
                        if _OLLAMA_OOM_RE.search(exc.response.text)
                        else "provider_http_error"
                    )
                ),
            ) from exc
        except httpx.HTTPError as exc:
            raise ProviderError(
                f"Ollama chat request failed: {exc}",
                GenerationDiagnostics(
                    failure_classification="provider_timeout_or_connection_error"
                ),
            ) from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise ProviderError(
                "Ollama chat response is invalid.",
                GenerationDiagnostics(failure_classification="invalid_provider_response"),
            ) from exc
        if not isinstance(data, dict):
            raise ProviderError(
                "Ollama chat response is invalid.",
                GenerationDiagnostics(failure_classification="invalid_provider_response"),
            )
        message = data.get("message")
        if not isinstance(message, dict):
            raise ProviderError(
                "Ollama chat response is missing message content.",
                GenerationDiagnostics(failure_classification="invalid_provider_response"),
            )

        content = message.get("content")
        diagnostics = _ollama_generation_diagnostics(data, message, content)
        if not isinstance(content, str) or not content.strip():
            thinking = message.get("thinking")
            if isinstance(thinking, str) and thinking.strip():
                raise ProviderError(
                    "The local model produced reasoning but no final answer. "
                    "Disable thinking or increase the context window.",
                    diagnostics.model_copy(update={"failure_classification": "empty_content"}),
                )
            classification = (
                "length_exhausted"
                if diagnostics.done_reason == "length"
                else "empty_content_unknown_cause"
            )
            raise ProviderError(
                "Ollama chat response returned empty content.",
                diagnostics.model_copy(update={"failure_classification": classification}),
            )

        final_content = content.strip()
        return ChatGenerationResult(
            content=final_content,
            diagnostics=diagnostics.model_copy(update={"content_chars": len(final_content)}),
        )


def _ollama_generation_diagnostics(
    data: object,
    message: dict[object, object],
    content: object,
) -> GenerationDiagnostics:
    payload = data if isinstance(data, dict) else {}
    thinking = message.get("thinking")
    return GenerationDiagnostics(
        done=payload.get("done") if isinstance(payload.get("done"), bool) else None,
        done_reason=(
            payload.get("done_reason") if isinstance(payload.get("done_reason"), str) else None
        ),
        total_duration=_safe_int(payload.get("total_duration")),
        load_duration=_safe_int(payload.get("load_duration")),
        prompt_eval_count=_safe_int(payload.get("prompt_eval_count")),
        prompt_eval_duration=_safe_int(payload.get("prompt_eval_duration")),
        eval_count=_safe_int(payload.get("eval_count")),
        eval_duration=_safe_int(payload.get("eval_duration")),
        content_chars=len(content) if isinstance(content, str) else 0,
        thinking_present=isinstance(thinking, str) and bool(thinking.strip()),
    )


def _safe_int(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def create_embedding_provider(settings: Settings) -> EmbeddingProvider:
    if settings.embedding_provider == "hash":
        return HashEmbeddingProvider()
    return OllamaEmbeddingProvider(
        base_url=settings.ollama_base_url,
        model=settings.ollama_embed_model,
        timeout_seconds=settings.ollama_request_timeout_seconds,
    )


def create_chat_provider(settings: Settings) -> ChatProvider:
    if settings.llm_provider == "mock":
        return MockChatProvider()
    return OllamaChatProvider(
        base_url=settings.ollama_base_url,
        model=settings.ollama_chat_model,
        timeout_seconds=settings.ollama_request_timeout_seconds,
        temperature=settings.ollama_temperature,
        num_ctx=settings.ollama_num_ctx,
        num_gpu=settings.ollama_num_gpu,
        keep_alive=settings.ollama_keep_alive,
    )
