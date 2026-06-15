"""Tests du connecteur API ERP/CRM contre le mock (sans reseau)."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from liaison.connectors.api import ApiConnector, ApiConnectorError
from liaison.connectors.mock_erp import app
from liaison.schemas import SourceKind


@pytest.fixture
def connector() -> Iterator[ApiConnector]:
    with TestClient(app, base_url="http://erp") as client:
        yield ApiConnector(client)


def test_get_customer_returns_evidence(connector: ApiConnector) -> None:
    evidence = connector.get_customer(1)
    assert evidence.kind == SourceKind.API
    assert "Acme" in evidence.summary


def test_get_customer_raises_on_unknown(connector: ApiConnector) -> None:
    with pytest.raises(ApiConnectorError):
        connector.get_customer(999)


def test_list_open_tickets_filters_status(connector: ApiConnector) -> None:
    evidence = connector.list_open_tickets(1)
    assert "1 ticket" in evidence.summary


def test_create_ticket_is_idempotent(connector: ApiConnector) -> None:
    first = connector.create_ticket(2, "Probleme connexion", idempotency_key="k-123")
    second = connector.create_ticket(2, "Probleme connexion", idempotency_key="k-123")
    assert first.payload["id"] == second.payload["id"]
