from __future__ import annotations

import hashlib
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

import httpx

from sialabs_local_rag.settings import Settings
from sialabs_local_rag.vector_math import normalize_vector

_TOKEN_RE = re.compile(r"[\wÀ-ÿ]+", re.UNICODE)


class ProviderError(RuntimeError):
    """Raised when an external AI provider cannot complete a request."""


@dataclass(frozen=True)
class ChatRuntimeOptions:
    model: str | None = None
    num_ctx: int | None = None
    num_gpu: int | None = None
    keep_alive: str | None = None
    temperature: float | None = None


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
    ) -> str:
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
    ) -> str:
        del system_prompt, runtime_options
        context_lines = [line for line in user_prompt.splitlines() if line.startswith("Fonte")]
        source_count = len(context_lines)
        return (
            "Resposta simulada para validação local. "
            f"Foram usadas {source_count} fontes recuperadas. "
            "Ative LLM_PROVIDER=ollama para gerar respostas com Gemma via Ollama."
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
    ) -> str:
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

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(f"{self.base_url}/api/chat", json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderError(f"Ollama chat request failed: {exc}") from exc

        data = response.json()
        message = data.get("message")
        if not isinstance(message, dict):
            raise ProviderError("Ollama chat response is missing message content.")

        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise ProviderError("Ollama chat response returned empty content.")

        return content.strip()


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
