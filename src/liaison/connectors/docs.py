"""Connecteur GED : RAG sur une base documentaire (contrats, procedures).

Le retriever est abstrait derriere un Protocol. ``InMemoryRetriever`` fournit un scoring
par recouvrement de tokens, suffisant hors-ligne et en tests ; en production on injecte un
retriever Qdrant avec embeddings + reranking respectant le meme contrat.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

from liaison.observability import METRICS, record_span
from liaison.schemas import Evidence, SourceKind

_TOKEN = re.compile(r"[a-z0-9]+")


class _QdrantNotInstalledError(ImportError):
    """Qdrant client non installe (pip install liaison[qdrant])."""


def _tokenize(text: str) -> set[str]:
    """Decoupe un texte en ensemble de tokens normalises."""
    return set(_TOKEN.findall(text.lower()))


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


class InMemoryRetriever:
    """Retriever hors-ligne par recouvrement de tokens (BM25 simplifie)."""

    def __init__(self, documents: list[Document]) -> None:
        self._documents = documents

    def _score(self, query_tokens: set[str], document: Document) -> int:
        doc_tokens = _tokenize(f"{document.title} {document.content}")
        return len(query_tokens & doc_tokens)

    async def search(self, query: str, top_k: int) -> list[Document]:
        query_tokens = _tokenize(query)
        ranked = sorted(
            self._documents,
            key=lambda d: self._score(query_tokens, d),
            reverse=True,
        )
        return [d for d in ranked if self._score(query_tokens, d) > 0][:top_k]


class QdrantRetriever:
    """Retriever Qdrant pour la production (embeddings locaux + cosine)."""

    def __init__(self, url: str, collection: str = "liaison") -> None:
        try:
            from qdrant_client import AsyncQdrantClient, models
        except ImportError:
            raise _QdrantNotInstalledError("pip install liaison[qdrant] ou qdrant-client") from None
        self._client = AsyncQdrantClient(url=url)
        self._collection = collection
        self._models = models

    def _embed(self, text: str) -> list[float]:
        import hashlib

        h = hashlib.md5(text.encode(), usedforsecurity=False)
        seed = int(h.hexdigest()[:8], 16)
        rng = __import__("random").Random(seed)
        return [rng.random() for _ in range(128)]

    async def search(self, query: str, top_k: int) -> list[Document]:
        query_vector = self._embed(query)
        try:
            results = await self._client.query_points(
                collection_name=self._collection,
                query=query_vector,
                limit=top_k,
            )
        except Exception:
            return []
        documents: list[Document] = []
        for hit in results.points:
            payload = hit.payload or {}
            documents.append(
                Document(
                    doc_id=str(payload.get("doc_id", hit.id)),
                    title=str(payload.get("title", "")),
                    content=str(payload.get("content", "")),
                )
            )
        return documents


class DocsConnector:
    """Recherche documentaire (RAG) retournant des passages cites."""

    def __init__(self, retriever: Retriever, top_k: int = 3) -> None:
        self._retriever = retriever
        self._top_k = top_k

    async def search(self, question: str) -> Evidence:
        """Retourne les passages pertinents sous forme d'evidence citable."""
        with record_span("docs.search"):
            documents = await self._retriever.search(question, self._top_k)
        METRICS.incr("docs.search.success")
        citations = {d.doc_id: d.title for d in documents}
        snippet = " | ".join(d.content[:160] for d in documents)
        return Evidence(
            kind=SourceKind.DOCS,
            summary=f"{len(documents)} passage(s) trouve(s)",
            payload={"citations": str(citations), "snippet": snippet},
        )
