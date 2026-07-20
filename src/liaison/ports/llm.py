"""Port du fournisseur LLM : contrat implemente par les adapters outbound.

Le reste du systeme ne connait pas le fournisseur concret. Un ``LocalProvider``
deterministe permet de tourner hors-ligne et en tests ; en production on injecte un
provider Bedrock/LiteLLM respectant le meme protocole.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol

from liaison.domain.models import LLMRequest


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
