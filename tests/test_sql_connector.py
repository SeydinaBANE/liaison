"""Tests du connecteur SQL text-to-SQL gouverne."""

from __future__ import annotations

import pytest
from sqlalchemy import Engine

from liaison.connectors.sql import (
    SemanticLayer,
    SqlConnector,
    SqlGovernanceError,
    SqlGuard,
    TableSchema,
)
from liaison.schemas import SourceKind
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


def test_guard_accepts_select_on_allowed_table() -> None:
    guard = SqlGuard(_LAYER.allowed_tables)
    assert guard.validate("SELECT name FROM customers;") == "SELECT name FROM customers"


def test_guard_rejects_table_outside_allowlist() -> None:
    guard = SqlGuard(_LAYER.allowed_tables)
    with pytest.raises(SqlGovernanceError, match="allow-list"):
        guard.validate("SELECT * FROM salaries")


def test_guard_rejects_write_statement() -> None:
    guard = SqlGuard(_LAYER.allowed_tables)
    with pytest.raises(SqlGovernanceError):
        guard.validate("DELETE FROM customers WHERE id = 1")


def test_guard_rejects_multiple_statements() -> None:
    guard = SqlGuard(_LAYER.allowed_tables)
    with pytest.raises(SqlGovernanceError, match="statements"):
        guard.validate("SELECT 1; DROP TABLE customers")


def test_connector_executes_generated_sql(business_engine: Engine) -> None:
    gateway = make_gateway("```sql\nSELECT balance FROM customers WHERE id = 1\n```")
    connector = SqlConnector(business_engine, _LAYER, gateway)

    evidence = connector.query("quel est l'encours du client 1 ?")

    assert evidence.kind == SourceKind.SQL
    assert "1250.0" in evidence.payload["rows"]
    assert evidence.payload["sql"] == "SELECT balance FROM customers WHERE id = 1"


def test_connector_blocks_unsafe_generated_sql(business_engine: Engine) -> None:
    gateway = make_gateway("DROP TABLE customers")
    connector = SqlConnector(business_engine, _LAYER, gateway)

    with pytest.raises(SqlGovernanceError):
        connector.query("supprime les clients")
