"""Routage par mots-cles : selection des outils a invoquer pour une question donnee.

Logique pure et deterministe (testable hors-ligne), remplacable par un planificateur LLM
(ex. LangGraph) sans changer le contrat ``Tool``/``Router`` (cf. ADR-0003).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from liaison.domain.models import Evidence, SourceKind

ToolRunner = Callable[[str], Evidence | Awaitable[Evidence]]


@dataclass(frozen=True)
class Tool:
    """Outil orchestrable : un connecteur expose via un nom, une description et un runner."""

    name: str
    description: str
    keywords: frozenset[str]
    runner: ToolRunner
    source_kind: SourceKind = SourceKind.SQL


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
