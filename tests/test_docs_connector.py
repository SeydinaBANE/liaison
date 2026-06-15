"""Tests du connecteur GED (RAG in-memory)."""

from __future__ import annotations

from liaison.connectors.docs import DocsConnector, Document, InMemoryRetriever
from liaison.schemas import SourceKind

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


def test_retriever_ranks_relevant_document_first() -> None:
    retriever = InMemoryRetriever(_DOCS)
    results = retriever.search("litige facturation contrat", top_k=2)
    assert results[0].doc_id == "contrat-acme"


def test_retriever_returns_empty_when_no_overlap() -> None:
    retriever = InMemoryRetriever(_DOCS)
    assert retriever.search("kubernetes deploiement", top_k=3) == []


def test_connector_returns_evidence_with_citations() -> None:
    connector = DocsConnector(InMemoryRetriever(_DOCS))
    evidence = connector.search("clause de litige facturation")
    assert evidence.kind == SourceKind.DOCS
    assert "contrat-acme" in evidence.payload["citations"]
