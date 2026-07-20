"""Orchestrateur multi-agent asynchrone : routage, execution, synthese.

Pipeline : routage (selection des outils) -> execution (collecte d'evidences) -> synthese
(reponse en langage naturel sourcee). Use case applicatif de plus haut niveau : coordonne le
domaine (``Router``/``Tool``) et les ports (``LLMGateway``).
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from liaison.application.llm_gateway import LLMGateway
from liaison.domain.models import AnswerResponse, Evidence, LLMRequest, Message, Role
from liaison.domain.routing import Router, Tool
from liaison.platform.logging import get_logger
from liaison.platform.observability import METRICS, record_span

logger = get_logger(__name__)


class Orchestrator:
    """Coordonne routage, execution des connecteurs et synthese de la reponse finale."""

    def __init__(self, gateway: LLMGateway, tools: list[Tool]) -> None:
        self._gateway = gateway
        self._router = Router(tools)

    async def _synthesize(self, question: str, evidence: list[Evidence]) -> AnswerResponse:
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
            completion = await self._gateway.complete(prompt)
        return AnswerResponse(
            answer=completion.content,
            evidence=evidence,
            used_fallback=completion.used_fallback,
        )

    async def _run_tool(self, tool: Tool, question: str) -> Evidence:
        """Execute un outil ; en cas d'echec, retourne une evidence degradee (resilience)."""
        try:
            with record_span("orchestrator.tool", tool=tool.name):
                result = tool.runner(question)
                if hasattr(result, "__await__"):
                    result = await result
                return result
        except Exception as exc:  # noqa: BLE001 - frontiere de resilience de l'orchestrateur
            METRICS.incr("orchestrator.tool_error")
            logger.warning("tool_failed", tool=tool.name, error=str(exc))
            return Evidence(
                kind=tool.source_kind,
                summary=f"connecteur {tool.name} indisponible",
                payload={"error": str(exc)},
            )

    async def run(self, question: str) -> AnswerResponse:
        """Execute le pipeline complet pour une question metier."""
        tools = self._router.select(question)
        METRICS.incr("orchestrator.runs")
        evidence = [await self._run_tool(tool, question) for tool in tools]
        return await self._synthesize(question, evidence)

    async def run_stream(self, question: str) -> AsyncIterator[str]:
        """Execute le pipeline et diffuse la synthese token par token."""
        tools = self._router.select(question)
        METRICS.incr("orchestrator.runs")

        evidence: list[Evidence] = []
        for tool in tools:
            evidence.append(await self._run_tool(tool, question))
            yield f"data: {__import__('json').dumps({'evidence': evidence[-1].summary})}\n\n"

        context = "\n".join(f"[{e.kind}] {e.summary}" for e in evidence)
        system = (
            "Tu es un assistant metier. Reponds a la question en t'appuyant UNIQUEMENT"
            " sur les elements fournis, en citant leur source entre crochets."
        )
        prompt = LLMRequest(
            messages=[
                Message(role=Role.SYSTEM, content=system),
                Message(role=Role.USER, content=f"Question: {question}\nElements:\n{context}"),
            ]
        )
        with record_span("orchestrator.synthesize"):
            async for token in self._gateway.stream(prompt):
                yield f"data: {__import__('json').dumps({'token': token})}\n\n"
        yield "data: [DONE]\n\n"
