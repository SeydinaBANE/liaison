"""Tests du routage par mots-cles (``Router``/``Tool``)."""

from __future__ import annotations

from liaison.domain.models import Evidence, SourceKind
from liaison.domain.routing import Router, Tool


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
