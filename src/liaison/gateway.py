"""Gateway LLM asynchrone : abstraction du fournisseur avec fallback primaire -> secondaire.

Le gateway ne connait pas le fournisseur concret : il manipule un ``LLMProvider``
(Protocol). Un ``LocalProvider`` deterministe permet de tourner hors-ligne et en tests ;
en production on injecte un provider Bedrock/LiteLLM respectant le meme protocole.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol

import httpx

from liaison.config import Settings, get_settings
from liaison.logging import get_logger
from liaison.observability import METRICS, record_span
from liaison.schemas import LLMRequest, LLMResponse

logger = get_logger(__name__)


class LLMProviderError(RuntimeError):
    """Echec d'appel d'un fournisseur LLM."""


class LLMProvider(Protocol):
    """Contrat minimal d'un fournisseur LLM asynchrone."""

    model: str

    async def complete(self, request: LLMRequest) -> str:
        """Retourne la completion textuelle pour la requete fournie."""
        ...

    async def stream(self, _request: LLMRequest) -> AsyncIterator[str]:
        """Diffuse la completion token par token."""
        ...
        yield ""


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


class HttpLLMProvider:
    """Provider HTTP asynchrone compatible chat completions (LiteLLM/OpenAI)."""

    def __init__(
        self, model: str, client: httpx.AsyncClient, path: str = "/chat/completions"
    ) -> None:  # noqa: E501
        self.model = model
        self._client = client
        self._path = path

    def _build_payload(self, request: LLMRequest) -> dict[str, object]:
        return {
            "model": self.model,
            "messages": [{"role": m.role.value, "content": m.content} for m in request.messages],
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }

    async def complete(self, request: LLMRequest) -> str:
        payload = self._build_payload(request)
        try:
            response = await self._client.post(self._path, json=payload)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMProviderError(f"appel LLM {self.model} echoue: {exc}") from exc
        try:
            return str(response.json()["choices"][0]["message"]["content"])
        except (KeyError, IndexError, ValueError) as exc:
            raise LLMProviderError(f"reponse LLM {self.model} invalide: {exc}") from exc

    async def stream(self, request: LLMRequest) -> AsyncIterator[str]:
        payload = self._build_payload(request)
        payload["stream"] = True
        try:
            async with self._client.stream("POST", self._path, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line or line == "data: [DONE]":
                        continue
                    if line.startswith("data: "):
                        import json as _json

                        chunk = _json.loads(line[6:])
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        content: str = delta.get("content", "")
                        if content:
                            yield content
        except httpx.HTTPError as exc:
            raise LLMProviderError(f"stream LLM {self.model} echoue: {exc}") from exc


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


def _build_async_http_client(cfg: Settings) -> httpx.AsyncClient:
    """Construit le client HTTP async du provider LLM."""
    headers = {"Authorization": f"Bearer {cfg.llm_api_key}"} if cfg.llm_api_key else {}
    return httpx.AsyncClient(base_url=cfg.llm_api_base, headers=headers, timeout=30.0)


def build_default_gateway(
    settings: Settings | None = None,
    http_client: httpx.AsyncClient | None = None,
) -> LLMGateway:
    """Construit le gateway selon la configuration.

    Si ``llm_api_base`` est renseigne, utilise un provider HTTP reel (primaire + fallback) ;
    sinon, retombe sur ``LocalProvider`` deterministe pour fonctionner hors-ligne.
    """
    cfg = settings or get_settings()
    if not cfg.llm_api_base:
        return LLMGateway(
            primary=LocalProvider(model=cfg.llm_model_primary),
            fallback=LocalProvider(model=cfg.llm_model_fallback),
        )
    client = http_client or _build_async_http_client(cfg)
    return LLMGateway(
        primary=HttpLLMProvider(model=cfg.llm_model_primary, client=client),
        fallback=HttpLLMProvider(model=cfg.llm_model_fallback, client=client),
    )
