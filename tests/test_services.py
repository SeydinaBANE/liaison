"""Test d'integration de l'assemblage demo (composition root)."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from liaison.connectors.mock_erp import app
from liaison.schemas import SourceKind
from liaison.services import build_orchestrator


@pytest.fixture
def erp_client() -> Iterator[TestClient]:
    with TestClient(app, base_url="http://erp") as client:
        yield client


def test_demo_orchestrator_answers_docs_question() -> None:
    orchestrator = build_orchestrator()

    response = orchestrator.run("quelle est la clause de penalite du contrat ?")

    assert response.evidence
    assert any(e.kind == SourceKind.DOCS for e in response.evidence)


def test_demo_orchestrator_degrades_gracefully_on_sql() -> None:
    orchestrator = build_orchestrator()

    response = orchestrator.run("quel est l'encours du client ?")

    assert response.evidence
    sql_evidence = next(e for e in response.evidence if e.kind == SourceKind.SQL)
    assert "indisponible" in sql_evidence.summary or "ligne" in sql_evidence.summary


def test_demo_orchestrator_crosses_three_sources(erp_client: TestClient) -> None:
    orchestrator = build_orchestrator(api_client=erp_client)

    response = orchestrator.run(
        "Quel est l'encours du client Acme, un litige est-il ouvert et que dit le contrat ?"
    )

    kinds = {e.kind for e in response.evidence}
    assert kinds == {SourceKind.SQL, SourceKind.API, SourceKind.DOCS}
    api_evidence = next(e for e in response.evidence if e.kind == SourceKind.API)
    assert "Acme" in api_evidence.summary
