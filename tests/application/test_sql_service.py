"""Tests du use case SQL (text-to-SQL gouverne), sans moteur SQL reel."""

from __future__ import annotations

import pytest

from liaison.application.sql_service import SqlConnector
from liaison.domain.models import SourceKind
from liaison.domain.sql_policy import SemanticLayer, SqlGovernanceError, TableSchema
from tests.conftest import make_gateway

_LAYER = SemanticLayer(
    [
        TableSchema(
            name="customers",
            description="clients",
            columns={"id": "identifiant", "name": "nom", "balance": "encours"},
        ),
        TableSchema(
            name="tickets",
            description="tickets support",
            columns={"id": "identifiant", "status": "statut"},
        ),
    ]
)


class _FakeExecutor:
    def __init__(self, rows: list[dict[str, object]]) -> None:
        self._rows = rows
        self.received_sql: str | None = None

    async def execute(self, sql: str) -> list[dict[str, object]]:
        self.received_sql = sql
        return self._rows


async def test_connector_executes_generated_sql() -> None:
    gateway = make_gateway("```sql\nSELECT balance FROM customers WHERE id = 1\n```")
    executor = _FakeExecutor([{"balance": 1250.0}])
    connector = SqlConnector(executor, _LAYER, gateway)

    evidence = await connector.query("quel est l'encours du client 1 ?")

    assert evidence.kind == SourceKind.SQL
    assert "1250.0" in evidence.payload["rows"]
    assert evidence.payload["sql"] == "SELECT balance FROM customers WHERE id = 1"
    assert executor.received_sql == "SELECT balance FROM customers WHERE id = 1"


async def test_connector_blocks_unsafe_generated_sql() -> None:
    gateway = make_gateway("DROP TABLE customers")
    executor = _FakeExecutor([])
    connector = SqlConnector(executor, _LAYER, gateway)

    with pytest.raises(SqlGovernanceError):
        await connector.query("supprime les clients")

    assert executor.received_sql is None
