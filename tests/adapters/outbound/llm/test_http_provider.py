"""Tests du provider LLM HTTP (compatible chat completions) et de son cablage, sans reseau."""

from __future__ import annotations

import httpx
import pytest

from liaison.adapters.outbound.llm.http_provider import HttpLLMProvider
from liaison.domain.models import LLMRequest, Message, Role
from liaison.platform.config import Settings
from liaison.ports.llm import LLMProviderError
from liaison.services import build_default_gateway


def _request() -> LLMRequest:
    return LLMRequest(messages=[Message(role=Role.USER, content="bonjour")])


def _async_client(handler: httpx.MockTransport) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=handler, base_url="http://llm")


async def test_http_provider_parses_completion() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": [{"message": {"content": "salut"}}]})

    provider = HttpLLMProvider(model="m", client=_async_client(httpx.MockTransport(handler)))
    result = await provider.complete(_request())
    assert result == "salut"


async def test_http_provider_raises_on_http_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    provider = HttpLLMProvider(model="m", client=_async_client(httpx.MockTransport(handler)))
    with pytest.raises(LLMProviderError):
        await provider.complete(_request())


async def test_http_provider_raises_on_malformed_payload() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"unexpected": True})

    provider = HttpLLMProvider(model="m", client=_async_client(httpx.MockTransport(handler)))
    with pytest.raises(LLMProviderError):
        await provider.complete(_request())


async def test_build_default_gateway_uses_local_without_api_base() -> None:
    gateway = build_default_gateway(Settings(llm_api_base=""))
    response = await gateway.complete(_request())
    assert response.content == "bonjour"


async def test_build_default_gateway_uses_http_with_api_base() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": [{"message": {"content": "reponse llm"}}]})

    client = _async_client(httpx.MockTransport(handler))
    settings = Settings(llm_api_base="http://llm.internal")
    gateway = build_default_gateway(settings, http_client=client)

    response = await gateway.complete(_request())

    assert response.content == "reponse llm"
    assert response.used_fallback is False
