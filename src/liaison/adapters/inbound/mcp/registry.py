"""Exposition des connecteurs au format MCP (Model Context Protocol).

Fournit un registre d'outils dont la description (nom, schema d'entree JSON) est conforme a
ce qu'attend un serveur MCP, et un dispatcher d'appels. Un transport MCP (stdio/SSE) vient
ensuite envelopper ce registre ; on le garde decouple pour rester testable hors-ligne.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from liaison.domain.models import Evidence
from liaison.platform.observability import METRICS, record_span

ToolHandler = Callable[[dict[str, object]], Evidence]


class McpToolError(RuntimeError):
    """Outil MCP inconnu ou arguments invalides."""


@dataclass(frozen=True)
class McpTool:
    """Descripteur d'outil au format MCP."""

    name: str
    description: str
    input_schema: dict[str, object]
    handler: ToolHandler

    def descriptor(self) -> dict[str, object]:
        """Retourne la representation MCP (sans le handler) listee par le serveur."""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }


class McpRegistry:
    """Registre d'outils MCP : enregistrement, listing et dispatch."""

    def __init__(self) -> None:
        self._tools: dict[str, McpTool] = {}

    def register(
        self,
        name: str,
        description: str,
        input_schema: dict[str, object],
        handler: ToolHandler,
    ) -> None:
        """Enregistre un outil expose via MCP."""
        self._tools[name] = McpTool(name, description, input_schema, handler)

    def list_tools(self) -> list[dict[str, object]]:
        """Liste les descripteurs MCP de tous les outils enregistres."""
        return [tool.descriptor() for tool in self._tools.values()]

    def call_tool(self, name: str, arguments: dict[str, object]) -> Evidence:
        """Execute un outil enregistre ; leve ``McpToolError`` si inconnu."""
        tool = self._tools.get(name)
        if tool is None:
            raise McpToolError(f"outil MCP inconnu: {name}")
        with record_span("mcp.call_tool", tool=name):
            result = tool.handler(arguments)
        METRICS.incr("mcp.call.success")
        return result
