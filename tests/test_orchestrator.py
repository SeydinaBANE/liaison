"""Tests de l'orchestrateur multi-agent (routage + synthese)."""

from __future__ import annotations

from liaison.orchestrator import Orchestrator, Router, Tool
from liaison.schemas import Evidence, SourceKind
from tests.conftest import make_gateway


async def _async_runner(summary: str) -> Evidence:
    return Evidence(kind=SourceKind.SQL, summary=summary)


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


def test_router_selects_by_keyword() -> None:
    sql = _tool("sql", {"encours", "facture"}, "encours")
    docs = _tool("docs", {"contrat", "clause"}, "clause")
    router = Router([sql, docs])

    selected = router.select("quel est l'encours du client ?")

    assert [t.name for t in selected] == ["sql"]


def test_router_falls_back_to_all_tools_when_no_match() -> None:
    sql = _tool("sql", {"encours"}, "encours")
    docs = _tool("docs", {"contrat"}, "clause")
    router = Router([sql, docs])

    selected = router.select("bonjour")

    assert len(selected) == 2


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
