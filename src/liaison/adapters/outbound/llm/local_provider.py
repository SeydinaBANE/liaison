"""Adapters LLM hors-ligne : deterministe (demo/tests) et systematiquement en echec (tests)."""

from __future__ import annotations

from collections.abc import AsyncIterator

from liaison.domain.models import LLMRequest
from liaison.ports.llm import LLMProviderError


class LocalProvider:
    """Fournisseur deterministe hors-ligne (tests et mode local)."""

    def __init__(self, model: str, prefix: str = "") -> None:
        self.model = model
        self._prefix = prefix

    async def complete(self, request: LLMRequest) -> str:
        last_user = next(
            (m.content for m in reversed(request.messages) if m.role == "user"),
            "",
        )
        return f"{self._prefix}{last_user}".strip()

    async def stream(self, request: LLMRequest) -> AsyncIterator[str]:
        result = await self.complete(request)
        for word in result.split():
            yield word


class FailingProvider:
    """Fournisseur qui echoue systematiquement (utile pour tester le fallback)."""

    def __init__(self, model: str) -> None:
        self.model = model

    async def complete(self, request: LLMRequest) -> str:
        del request
        raise LLMProviderError(f"provider {self.model} indisponible")

    async def stream(self, request: LLMRequest) -> AsyncIterator[str]:
        del request
        raise LLMProviderError(f"provider {self.model} indisponible")
        yield  # pragma: no cover
