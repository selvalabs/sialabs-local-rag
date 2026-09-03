from __future__ import annotations

import httpx
import pytest

from sialabs_local_rag.providers import (
    ChatRuntimeOptions,
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


@pytest.mark.asyncio
@pytest.mark.parametrize("think", [False, True, None])
async def test_ollama_chat_serializes_runtime_think(
    monkeypatch: pytest.MonkeyPatch, think: bool | None
) -> None:
    class FakeClient:
        payload: dict[str, object]

        async def __aenter__(self) -> FakeClient:
            return self

        async def __aexit__(self, *_args: object) -> None:
            return None

        async def post(self, *_args: object, **kwargs: object) -> httpx.Response:
            self.payload = kwargs["json"]  # type: ignore[assignment]
            return httpx.Response(
                200,
                json={"message": {"content": "Final answer"}},
                request=httpx.Request("POST", "http://ollama.local/api/chat"),
            )

    client = FakeClient()
    monkeypatch.setattr(httpx, "AsyncClient", lambda **_kwargs: client)
    provider = OllamaChatProvider(
        base_url="http://ollama.local",
        model="gemma4:e2b",
        timeout_seconds=5,
        temperature=0.2,
        num_ctx=1024,
        num_gpu=None,
        keep_alive="5m",
    )

    result = await provider.generate("system", "test", ChatRuntimeOptions(think=think))

    if think is None:
        assert "think" not in client.payload
    else:
        assert client.payload["think"] is think
    assert "think" not in client.payload["options"]  # type: ignore[operator]
    assert result.content == "Final answer"


@pytest.mark.asyncio
async def test_ollama_chat_preserves_safe_generation_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeClient:
        async def __aenter__(self) -> FakeClient:
            return self

        async def __aexit__(self, *_args: object) -> None:
            return None

        async def post(self, *_args: object, **_kwargs: object) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "done": True,
                    "done_reason": "stop",
                    "total_duration": 100,
                    "load_duration": 20,
                    "prompt_eval_count": 30,
                    "prompt_eval_duration": 40,
                    "eval_count": 50,
                    "eval_duration": 60,
                    "message": {"content": "Final answer", "thinking": "private reasoning"},
                },
                request=httpx.Request("POST", "http://ollama.local/api/chat"),
            )

    monkeypatch.setattr(httpx, "AsyncClient", lambda **_kwargs: FakeClient())
    provider = OllamaChatProvider("http://ollama.local", "gemma4:e2b", 5, 0.2, 1024, None, "5m")

    result = await provider.generate("system", "test")

    assert result.diagnostics.done is True
    assert result.diagnostics.done_reason == "stop"
    assert result.diagnostics.eval_count == 50
    assert result.diagnostics.thinking_present is True
    assert "private reasoning" not in result.diagnostics.model_dump_json()


@pytest.mark.asyncio
async def test_ollama_chat_omits_or_serializes_num_predict(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeClient:
        payload: dict[str, object]

        async def __aenter__(self) -> FakeClient:
            return self

        async def __aexit__(self, *_args: object) -> None:
            return None

        async def post(self, *_args: object, **kwargs: object) -> httpx.Response:
            self.payload = kwargs["json"]  # type: ignore[assignment]
            return httpx.Response(
                200,
                json={"message": {"content": "Final answer"}},
                request=httpx.Request("POST", "http://ollama.local/api/chat"),
            )

    client = FakeClient()
    monkeypatch.setattr(httpx, "AsyncClient", lambda **_kwargs: client)
    provider = OllamaChatProvider("http://ollama.local", "gemma4:e2b", 5, 0.2, 1024, None, "5m")

    await provider.generate("system", "test", ChatRuntimeOptions(num_predict=None))
    assert "num_predict" not in client.payload["options"]  # type: ignore[operator]
    await provider.generate("system", "test", ChatRuntimeOptions(num_predict=384))
    assert client.payload["options"]["num_predict"] == 384  # type: ignore[index]


@pytest.mark.asyncio
async def test_ollama_chat_classifies_malformed_success_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeClient:
        async def __aenter__(self) -> FakeClient:
            return self

        async def __aexit__(self, *_args: object) -> None:
            return None

        async def post(self, *_args: object, **_kwargs: object) -> httpx.Response:
            return response(200, "not valid JSON")

    monkeypatch.setattr(httpx, "AsyncClient", lambda **_kwargs: FakeClient())
    provider = OllamaChatProvider("http://ollama.local", "gemma4:e2b", 5, 0.2, 1024, None, "5m")

    with pytest.raises(ProviderError, match="response is invalid") as caught:
        await provider.generate("system", "test")

    assert caught.value.diagnostics is not None
    assert caught.value.diagnostics.failure_classification == "invalid_provider_response"


@pytest.mark.asyncio
async def test_ollama_chat_rejects_reasoning_without_a_final_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw_reasoning = "private reasoning that must never reach the user"

    class FakeClient:
        async def __aenter__(self) -> FakeClient:
            return self

        async def __aexit__(self, *_args: object) -> None:
            return None

        async def post(self, *_args: object, **_kwargs: object) -> httpx.Response:
            return httpx.Response(
                200,
                json={"message": {"content": "", "thinking": raw_reasoning}},
                request=httpx.Request("POST", "http://ollama.local/api/chat"),
            )

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

    with pytest.raises(ProviderError, match="produced reasoning but no final answer") as caught:
        await provider.generate("system", "test")

    assert raw_reasoning not in str(caught.value)
    assert caught.value.diagnostics is not None
    assert caught.value.diagnostics.thinking_present is True
    assert raw_reasoning not in caught.value.diagnostics.model_dump_json()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("done_reason", "classification"),
    [("stop", "empty_content_unknown_cause"), ("length", "length_exhausted")],
)
async def test_ollama_chat_classifies_empty_content_without_reasoning(
    monkeypatch: pytest.MonkeyPatch,
    done_reason: str,
    classification: str,
) -> None:
    class FakeClient:
        async def __aenter__(self) -> FakeClient:
            return self

        async def __aexit__(self, *_args: object) -> None:
            return None

        async def post(self, *_args: object, **_kwargs: object) -> httpx.Response:
            return httpx.Response(
                200,
                json={"done_reason": done_reason, "message": {"content": ""}},
                request=httpx.Request("POST", "http://ollama.local/api/chat"),
            )

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

    with pytest.raises(ProviderError, match="returned empty content") as caught:
        await provider.generate("system", "test")

    assert caught.value.diagnostics is not None
    assert caught.value.diagnostics.failure_classification == classification
