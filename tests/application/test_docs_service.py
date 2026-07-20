"""Tests du use case GED (RAG), port ``Retriever`` fourni par l'adapter in-memory."""

from __future__ import annotations

from liaison.adapters.outbound.retriever.in_memory import InMemoryRetriever
from liaison.application.docs_service import DocsConnector
from liaison.domain.models import SourceKind
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


async def test_connector_returns_evidence_with_citations() -> None:
    connector = DocsConnector(InMemoryRetriever(_DOCS))
    evidence = await connector.search("clause de litige facturation")
    assert evidence.kind == SourceKind.DOCS
    assert "contrat-acme" in evidence.payload["citations"]
