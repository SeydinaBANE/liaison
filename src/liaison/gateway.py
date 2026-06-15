"""Gateway LLM : abstraction du fournisseur avec fallback primaire -> secondaire.

Le gateway ne connait pas le fournisseur concret : il manipule un ``LLMProvider``
(Protocol). Un ``LocalProvider`` deterministe permet de tourner hors-ligne et en tests ;
en production on injecte un provider Bedrock/LiteLLM respectant le meme protocole.
"""

from __future__ import annotations

from typing import Protocol

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


def build_default_gateway(settings: Settings | None = None) -> LLMGateway:
    """Construit un gateway local a partir de la configuration (mode hors-ligne)."""
    cfg = settings or get_settings()
    return LLMGateway(
        primary=LocalProvider(model=cfg.llm_model_primary),
        fallback=LocalProvider(model=cfg.llm_model_fallback),
    )
