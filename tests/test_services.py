"""Test d'integration de l'assemblage demo (composition root)."""

from __future__ import annotations

from liaison.schemas import SourceKind
from liaison.services import build_orchestrator


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
