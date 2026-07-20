"""Test d'integration de l'assemblage demo (composition root)."""

from __future__ import annotations

import httpx
import pytest
from httpx import ASGITransport

from liaison.demo.mock_erp import app
from liaison.domain.models import SourceKind
from liaison.services import _cleanup, build_orchestrator

_ERPTRANSPORT = ASGITransport(app=app)


@pytest.fixture
def erp_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=_ERPTRANSPORT, base_url="http://erp")


async def test_demo_orchestrator_answers_docs_question() -> None:
    orchestrator = await build_orchestrator()

    response = await orchestrator.run("quelle est la clause de penalite du contrat ?")

    assert response.evidence
    assert any(e.kind == SourceKind.DOCS for e in response.evidence)
    await _cleanup()


async def test_demo_orchestrator_degrades_gracefully_on_sql() -> None:
    orchestrator = await build_orchestrator()

    response = await orchestrator.run("quel est l'encours du client ?")

    assert response.evidence
    sql_evidence = next(e for e in response.evidence if e.kind == SourceKind.SQL)
    assert "indisponible" in sql_evidence.summary or "ligne" in sql_evidence.summary
    await _cleanup()


async def test_demo_orchestrator_crosses_three_sources(erp_client: httpx.AsyncClient) -> None:
    orchestrator = await build_orchestrator(api_client=erp_client)

    response = await orchestrator.run(
        "Quel est l'encours du client Acme, un litige est-il ouvert et que dit le contrat ?"
    )

    kinds = {e.kind for e in response.evidence}
    assert kinds == {SourceKind.SQL, SourceKind.API, SourceKind.DOCS}
    api_evidence = next(e for e in response.evidence if e.kind == SourceKind.API)
    assert "Acme" in api_evidence.summary
    await _cleanup()
