"""Tests de l'orchestrateur multi-agent (execution + synthese)."""

from __future__ import annotations

from liaison.application.orchestrator import Orchestrator
from liaison.domain.models import Evidence, SourceKind
from liaison.domain.routing import Tool
from tests.conftest import make_gateway


def _tool(name: str, keywords: set[str], summary: str) -> Tool:
    def runner(question: str) -> Evidence:
        del question
        return Evidence(kind=SourceKind.SQL, summary=summary)

    return Tool(
        name=name,
        description=summary,
        keywords=frozenset(keywords),
        runner=runner,
    )


async def test_orchestrator_collects_evidence_and_synthesizes() -> None:
    gateway = make_gateway("Reponse synthetisee [sql]")
    sql = _tool("sql", {"encours"}, "encours 1250")
    orchestrator = Orchestrator(gateway, [sql])

    response = await orchestrator.run("quel est l'encours ?")

    assert response.answer == "Reponse synthetisee [sql]"
    assert len(response.evidence) == 1
    assert response.evidence[0].summary == "encours 1250"


async def test_orchestrator_stream_emits_events() -> None:
    gateway = make_gateway("reponse test")
    sql = _tool("sql", {"encours"}, "encours 1250")
    orchestrator = Orchestrator(gateway, [sql])

    events: list[str] = []
    async for event in orchestrator.run_stream("quel est l'encours ?"):
        events.append(event)

    assert any("[DONE]" in e for e in events)
    assert any("encours 1250" in e for e in events)
