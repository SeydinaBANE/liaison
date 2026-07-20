"""Tests de la politique SQL (catalogue semantique + garde-fou de gouvernance)."""

from __future__ import annotations

import pytest

from liaison.domain.sql_policy import SemanticLayer, SqlGovernanceError, SqlGuard, TableSchema

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
