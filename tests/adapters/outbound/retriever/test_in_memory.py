"""Tests de l'adapter retriever in-memory (scoring par recouvrement de tokens)."""

from __future__ import annotations

from liaison.adapters.outbound.retriever.in_memory import InMemoryRetriever
from liaison.ports.retriever import Document

_DOCS = [
    Document(
        doc_id="contrat-acme",
        title="Contrat Acme",
        content="Le contrat prevoit une penalite de retard en cas de litige facturation.",
    ),
    Document(
        doc_id="procedure-rgpd",
        title="Procedure RGPD",
        content="Les donnees personnelles sont conservees douze mois maximum.",
    ),
]


async def test_retriever_ranks_relevant_document_first() -> None:
    retriever = InMemoryRetriever(_DOCS)
    results = await retriever.search("litige facturation contrat", top_k=2)
    assert results[0].doc_id == "contrat-acme"


async def test_retriever_returns_empty_when_no_overlap() -> None:
    retriever = InMemoryRetriever(_DOCS)
    results = await retriever.search("kubernetes deploiement", top_k=3)
    assert results == []
