from __future__ import annotations

import httpx
import pytest

from sialabs_local_rag.providers import (
    OllamaChatProvider,
    ProviderError,
    format_ollama_http_error,
)


def response(status_code: int, body: str) -> httpx.Response:
    return httpx.Response(
        status_code,
        text=body,
        request=httpx.Request("POST", "http://ollama.local/api/chat"),
    )


def test_ollama_http_error_is_bounded_sanitized_and_actionable() -> None:
    detail = "CUDA out of memory while starting llama-server. token=super-secret " + ("x" * 2000)

    message = format_ollama_http_error(response(500, detail), "chat")

    assert "GPU memory was exhausted" in message
    assert "Economy profile" in message
    assert "super-secret" not in message
    assert len(message) < 800


@pytest.mark.asyncio
async def test_ollama_chat_retains_runtime_diagnostic(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeClient:
        async def __aenter__(self) -> FakeClient:
            return self

        async def __aexit__(self, *_args: object) -> None:
            return None

        async def post(self, *_args: object, **_kwargs: object) -> httpx.Response:
            return response(500, '{"error":"CUDA out of memory in llama-server"}')

    monkeypatch.setattr(httpx, "AsyncClient", lambda **_kwargs: FakeClient())
    provider = OllamaChatProvider(
        base_url="http://ollama.local",
        model="gemma4:e2b",
        timeout_seconds=5,
        temperature=0.2,
        num_ctx=1024,
        num_gpu=None,
        keep_alive="5m",
    )

    with pytest.raises(ProviderError, match="GPU memory was exhausted") as caught:
        await provider.generate("system", "test")

    assert "CUDA out of memory" in str(caught.value)
