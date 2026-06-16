"""Tests du connecteur API ERP/CRM contre le mock (sans reseau)."""

from __future__ import annotations

import httpx
import pytest
from httpx import ASGITransport

from liaison.connectors.api import ApiConnector, ApiConnectorError
from liaison.connectors.mock_erp import app
from liaison.schemas import SourceKind

_ERPTRANSPORT = ASGITransport(app=app)


@pytest.fixture
async def connector() -> ApiConnector:
    client = httpx.AsyncClient(transport=_ERPTRANSPORT, base_url="http://erp")
    return ApiConnector(client)


async def test_get_customer_returns_evidence(connector: ApiConnector) -> None:
    evidence = await connector.get_customer(1)
    assert evidence.kind == SourceKind.API
    assert "Acme" in evidence.summary


async def test_get_customer_raises_on_unknown(connector: ApiConnector) -> None:
    with pytest.raises(ApiConnectorError):
        await connector.get_customer(999)


async def test_list_open_tickets_filters_status(connector: ApiConnector) -> None:
    evidence = await connector.list_open_tickets(1)
    assert "1 ticket" in evidence.summary


async def test_create_ticket_is_idempotent(connector: ApiConnector) -> None:
    first = await connector.create_ticket(2, "Probleme connexion", idempotency_key="k-123")
    second = await connector.create_ticket(2, "Probleme connexion", idempotency_key="k-123")
    assert first.payload["id"] == second.payload["id"]
