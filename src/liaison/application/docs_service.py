"""Connecteur GED : RAG sur une base documentaire (contrats, procedures).

Use case applicatif : ne connait que le port ``Retriever``, jamais l'implementation concrete
(in-memory, Qdrant, ...).
"""

from __future__ import annotations

from liaison.domain.models import Evidence, SourceKind
from liaison.platform.observability import METRICS, record_span
from liaison.ports.retriever import Retriever


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
