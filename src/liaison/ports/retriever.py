"""Port du retriever documentaire : contrat implemente par les adapters outbound.

``InMemoryRetriever`` fournit un scoring par recouvrement de tokens, suffisant hors-ligne et
en tests ; en production on injecte un retriever Qdrant avec embeddings + reranking
respectant le meme contrat.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Document:
    """Document indexe : identifiant, titre et contenu."""

    doc_id: str
    title: str
    content: str


class Retriever(Protocol):
    """Contrat asynchrone d'un retriever documentaire."""

    async def search(self, query: str, top_k: int) -> list[Document]:
        """Retourne les ``top_k`` documents les plus pertinents pour la requete."""
        ...
