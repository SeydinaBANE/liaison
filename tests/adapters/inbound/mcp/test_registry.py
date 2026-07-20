"""Tests du registre d'outils MCP."""

from __future__ import annotations

import pytest

from liaison.adapters.inbound.mcp.registry import McpRegistry, McpToolError
from liaison.domain.models import Evidence, SourceKind


def _handler(arguments: dict[str, object]) -> Evidence:
    return Evidence(kind=SourceKind.SQL, summary=f"recu {arguments['customer_id']}")


def _registry() -> McpRegistry:
    registry = McpRegistry()
    registry.register(
        name="get_customer",
        description="Recupere une fiche client",
        input_schema={
            "type": "object",
            "properties": {"customer_id": {"type": "integer"}},
            "required": ["customer_id"],
        },
        handler=_handler,
    )
    return registry


def test_list_tools_exposes_mcp_descriptor() -> None:
    tools = _registry().list_tools()
    assert tools[0]["name"] == "get_customer"
    assert "inputSchema" in tools[0]
    assert "handler" not in tools[0]


def test_call_tool_dispatches_to_handler() -> None:
    evidence = _registry().call_tool("get_customer", {"customer_id": 1})
    assert evidence.summary == "recu 1"


def test_call_unknown_tool_raises() -> None:
    with pytest.raises(McpToolError):
        _registry().call_tool("unknown", {})
