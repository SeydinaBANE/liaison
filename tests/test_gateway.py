"""Tests du gateway LLM (fallback + observabilite)."""

from __future__ import annotations

import pytest

from liaison.gateway import FailingProvider, LLMGateway, LLMProviderError, LocalProvider
from liaison.observability import METRICS
from liaison.schemas import LLMRequest, Message, Role


@pytest.fixture(autouse=True)
async def _reset_metrics() -> None:
    METRICS.reset()


def _request(text: str) -> LLMRequest:
    return LLMRequest(messages=[Message(role=Role.USER, content=text)])


async def test_complete_uses_primary_when_healthy() -> None:
    gateway = LLMGateway(
        primary=LocalProvider(model="primary"),
        fallback=LocalProvider(model="fallback"),
    )

    response = await gateway.complete(_request("bonjour"))

    assert response.content == "bonjour"
    assert response.model == "primary"
    assert response.used_fallback is False
    assert METRICS.counters["llm.primary.success"] == 1


async def test_complete_switches_to_fallback_on_primary_failure() -> None:
    gateway = LLMGateway(
        primary=FailingProvider(model="primary"),
        fallback=LocalProvider(model="fallback"),
    )

    response = await gateway.complete(_request("salut"))

    assert response.used_fallback is True
    assert response.model == "fallback"
    assert METRICS.counters["llm.primary.failure"] == 1
    assert METRICS.counters["llm.fallback.success"] == 1


async def test_complete_raises_when_both_providers_fail() -> None:
    gateway = LLMGateway(
        primary=FailingProvider(model="primary"),
        fallback=FailingProvider(model="fallback"),
    )

    with pytest.raises(LLMProviderError):
        await gateway.complete(_request("erreur"))


async def test_complete_fallback_missing_stream() -> None:
    """Le gateway n'expose pas stream sur complete."""
    gateway = LLMGateway(
        primary=LocalProvider(model="primary"),
        fallback=LocalProvider(model="fallback"),
    )
    response = await gateway.complete(_request("test"))
    assert response.content == "test"
