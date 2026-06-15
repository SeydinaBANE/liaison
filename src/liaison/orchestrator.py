"""Orchestrateur multi-agent : route une question vers les bons connecteurs puis synthetise.

Pipeline : routage (selection des outils) -> execution (collecte d'evidences) -> synthese
(reponse en langage naturel sourcee). Le routage est regle-base par defaut (deterministe,
testable) et reste remplacable par un planificateur LLM (ex. LangGraph) sans changer le
contrat.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from liaison.gateway import LLMGateway
from liaison.observability import METRICS, record_span
from liaison.schemas import AnswerResponse, Evidence, LLMRequest, Message, Role

ToolRunner = Callable[[str], Evidence]


@dataclass(frozen=True)
class Tool:
    """Outil orchestrable : un connecteur expose via un nom, une description et un runner."""

    name: str
    description: str
    keywords: frozenset[str]
    runner: ToolRunner


class Router:
    """Selectionne les outils a invoquer selon les mots-cles de la question."""

    def __init__(self, tools: list[Tool]) -> None:
        self._tools = tools

    def select(self, question: str) -> list[Tool]:
        """Retourne les outils dont au moins un mot-cle apparait dans la question.

        Si aucun ne correspond, retourne tous les outils (strategie de repli exhaustive).
        """
        lowered = question.lower()
        matched = [t for t in self._tools if any(k in lowered for k in t.keywords)]
        return matched or list(self._tools)


class Orchestrator:
    """Coordonne routage, execution des connecteurs et synthese de la reponse finale."""

    def __init__(self, gateway: LLMGateway, tools: list[Tool]) -> None:
        self._gateway = gateway
        self._router = Router(tools)

    def _synthesize(self, question: str, evidence: list[Evidence]) -> AnswerResponse:
        context = "\n".join(f"[{e.kind}] {e.summary}" for e in evidence)
        system = (
            "Tu es un assistant metier. Reponds a la question en t'appuyant UNIQUEMENT sur "
            "les elements fournis, en citant leur source entre crochets."
        )
        prompt = LLMRequest(
            messages=[
                Message(role=Role.SYSTEM, content=system),
                Message(role=Role.USER, content=f"Question: {question}\nElements:\n{context}"),
            ]
        )
        with record_span("orchestrator.synthesize"):
            completion = self._gateway.complete(prompt)
        return AnswerResponse(
            answer=completion.content,
            evidence=evidence,
            used_fallback=completion.used_fallback,
        )

    def run(self, question: str) -> AnswerResponse:
        """Execute le pipeline complet pour une question metier."""
        tools = self._router.select(question)
        METRICS.incr("orchestrator.runs")
        evidence: list[Evidence] = []
        for tool in tools:
            with record_span("orchestrator.tool", tool=tool.name):
                evidence.append(tool.runner(question))
        return self._synthesize(question, evidence)
