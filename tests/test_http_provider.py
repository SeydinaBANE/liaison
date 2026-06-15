"""Tests du provider LLM HTTP (compatible chat completions), sans reseau."""

from __future__ import annotations

import httpx
import pytest

from liaison.config import Settings
from liaison.gateway import HttpLLMProvider, LLMProviderError, build_default_gateway
from liaison.schemas import LLMRequest, Message, Role


def _request() -> LLMRequest:
    return LLMRequest(messages=[Message(role=Role.USER, content="bonjour")])


def _client(handler: httpx.MockTransport) -> httpx.Client:
    return httpx.Client(transport=handler, base_url="http://llm")


def test_http_provider_parses_completion() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": [{"message": {"content": "salut"}}]})

    provider = HttpLLMProvider(model="m", client=_client(httpx.MockTransport(handler)))
    assert provider.complete(_request()) == "salut"


def test_http_provider_raises_on_http_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    provider = HttpLLMProvider(model="m", client=_client(httpx.MockTransport(handler)))
    with pytest.raises(LLMProviderError):
        provider.complete(_request())


def test_http_provider_raises_on_malformed_payload() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"unexpected": True})

    provider = HttpLLMProvider(model="m", client=_client(httpx.MockTransport(handler)))
    with pytest.raises(LLMProviderError):
        provider.complete(_request())


def test_build_default_gateway_uses_local_without_api_base() -> None:
    gateway = build_default_gateway(Settings(llm_api_base=""))
    response = gateway.complete(_request())
    assert response.content == "bonjour"


def test_build_default_gateway_uses_http_with_api_base() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": [{"message": {"content": "reponse llm"}}]})

    client = _client(httpx.MockTransport(handler))
    settings = Settings(llm_api_base="http://llm.internal")
    gateway = build_default_gateway(settings, http_client=client)

    response = gateway.complete(_request())

    assert response.content == "reponse llm"
    assert response.used_fallback is False
