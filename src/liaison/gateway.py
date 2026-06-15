"""Gateway LLM : abstraction du fournisseur avec fallback primaire -> secondaire.

Le gateway ne connait pas le fournisseur concret : il manipule un ``LLMProvider``
(Protocol). Un ``LocalProvider`` deterministe permet de tourner hors-ligne et en tests ;
en production on injecte un provider Bedrock/LiteLLM respectant le meme protocole.
"""

from __future__ import annotations

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
    """Contrat minimal d'un fournisseur LLM."""

    model: str

    def complete(self, request: LLMRequest) -> str:
        """Retourne la completion textuelle pour la requete fournie."""
        ...


class LocalProvider:
    """Fournisseur deterministe hors-ligne (tests et mode local).

    Restitue le dernier message utilisateur, eventuellement prefixe, ce qui suffit a
    valider l'orchestration sans dependance reseau.
    """

    def __init__(self, model: str, prefix: str = "") -> None:
        self.model = model
        self._prefix = prefix

    def complete(self, request: LLMRequest) -> str:
        last_user = next(
            (m.content for m in reversed(request.messages) if m.role == "user"),
            "",
        )
        return f"{self._prefix}{last_user}".strip()


class FailingProvider:
    """Fournisseur qui echoue systematiquement (utile pour tester le fallback)."""

    def __init__(self, model: str) -> None:
        self.model = model

    def complete(self, request: LLMRequest) -> str:
        del request
        raise LLMProviderError(f"provider {self.model} indisponible")


class HttpLLMProvider:
    """Provider HTTP compatible chat completions (LiteLLM/OpenAI, frontant Bedrock en prod).

    Le client HTTP est injecte pour permettre les tests sans reseau (httpx.MockTransport).
    """

    def __init__(self, model: str, client: httpx.Client, path: str = "/chat/completions") -> None:
        self.model = model
        self._client = client
        self._path = path

    def complete(self, request: LLMRequest) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": m.role.value, "content": m.content} for m in request.messages],
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }
        try:
            response = self._client.post(self._path, json=payload)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMProviderError(f"appel LLM {self.model} echoue: {exc}") from exc
        try:
            return str(response.json()["choices"][0]["message"]["content"])
        except (KeyError, IndexError, ValueError) as exc:
            raise LLMProviderError(f"reponse LLM {self.model} invalide: {exc}") from exc


class LLMGateway:
    """Route les requetes vers le provider primaire, bascule sur le secondaire en cas d'echec."""

    def __init__(self, primary: LLMProvider, fallback: LLMProvider) -> None:
        self._primary = primary
        self._fallback = fallback

    def complete(self, request: LLMRequest) -> LLMResponse:
        """Appelle le primaire puis le fallback ; leve ``LLMProviderError`` si les deux echouent."""
        with record_span("llm.primary", model=self._primary.model):
            try:
                content = self._primary.complete(request)
                METRICS.incr("llm.primary.success")
                return LLMResponse(content=content, model=self._primary.model)
            except LLMProviderError as exc:
                METRICS.incr("llm.primary.failure")
                logger.warning("primary_failed", model=self._primary.model, error=str(exc))

        with record_span("llm.fallback", model=self._fallback.model):
            content = self._fallback.complete(request)
            METRICS.incr("llm.fallback.success")
            return LLMResponse(content=content, model=self._fallback.model, used_fallback=True)


def _build_http_client(cfg: Settings) -> httpx.Client:
    """Construit le client HTTP du provider LLM (base URL + cle d'API)."""
    headers = {"Authorization": f"Bearer {cfg.llm_api_key}"} if cfg.llm_api_key else {}
    return httpx.Client(base_url=cfg.llm_api_base, headers=headers, timeout=30.0)


def build_default_gateway(
    settings: Settings | None = None,
    http_client: httpx.Client | None = None,
) -> LLMGateway:
    """Construit le gateway selon la configuration.

    Si ``llm_api_base`` est renseigne, utilise un provider HTTP reel (primaire + fallback) ;
    sinon, retombe sur ``LocalProvider`` deterministe pour fonctionner hors-ligne. Le client
    HTTP peut etre injecte (tests).
    """
    cfg = settings or get_settings()
    if not cfg.llm_api_base:
        return LLMGateway(
            primary=LocalProvider(model=cfg.llm_model_primary),
            fallback=LocalProvider(model=cfg.llm_model_fallback),
        )
    client = http_client or _build_http_client(cfg)
    return LLMGateway(
        primary=HttpLLMProvider(model=cfg.llm_model_primary, client=client),
        fallback=HttpLLMProvider(model=cfg.llm_model_fallback, client=client),
    )
