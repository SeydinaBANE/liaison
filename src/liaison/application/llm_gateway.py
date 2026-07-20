"""Gateway LLM asynchrone : policy de fallback primaire -> secondaire.

Use case applicatif : ne connait que le port ``LLMProvider``, jamais un fournisseur concret.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from liaison.domain.models import LLMRequest, LLMResponse
from liaison.platform.logging import get_logger
from liaison.platform.observability import METRICS, record_span
from liaison.ports.llm import LLMProvider, LLMProviderError

logger = get_logger(__name__)


class LLMGateway:
    """Route les requetes vers le provider primaire, bascule sur le secondaire en cas d'echec."""

    def __init__(self, primary: LLMProvider, fallback: LLMProvider) -> None:
        self._primary = primary
        self._fallback = fallback

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Appelle le primaire puis le fallback ; leve ``LLMProviderError`` si les deux echouent."""
        with record_span("llm.primary", model=self._primary.model):
            try:
                content = await self._primary.complete(request)
                METRICS.incr("llm.primary.success")
                return LLMResponse(content=content, model=self._primary.model)
            except LLMProviderError as exc:
                METRICS.incr("llm.primary.failure")
                logger.warning("primary_failed", model=self._primary.model, error=str(exc))

        with record_span("llm.fallback", model=self._fallback.model):
            content = await self._fallback.complete(request)
            METRICS.incr("llm.fallback.success")
            return LLMResponse(content=content, model=self._fallback.model, used_fallback=True)

    async def stream(self, request: LLMRequest) -> AsyncIterator[str]:
        """Diffuse la completion depuis le primaire, avec fallback sur le secondaire."""
        tried_primary = False
        try:
            with record_span("llm.primary", model=self._primary.model):
                async for token in self._primary.stream(request):
                    tried_primary = True
                    yield token
                METRICS.incr("llm.primary.success")
                return
        except LLMProviderError as exc:
            METRICS.incr("llm.primary.failure")
            logger.warning("primary_failed", model=self._primary.model, error=str(exc))
            if not tried_primary:
                with record_span("llm.fallback", model=self._fallback.model):
                    async for token in self._fallback.stream(request):
                        yield token
                    METRICS.incr("llm.fallback.success")
