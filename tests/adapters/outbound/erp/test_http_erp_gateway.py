"""Tests de l'adapter ERP/CRM HTTP contre le mock (sans reseau)."""

from __future__ import annotations

import httpx
import pytest
from httpx import ASGITransport

from liaison.adapters.outbound.erp.http_gateway import HttpErpGateway
from liaison.demo.mock_erp import app
from liaison.ports.erp_gateway import ApiConnectorError

_ERPTRANSPORT = ASGITransport(app=app)


@pytest.fixture
async def gateway() -> HttpErpGateway:
    client = httpx.AsyncClient(transport=_ERPTRANSPORT, base_url="http://erp")
    return HttpErpGateway(client)


async def test_get_customer_returns_record(gateway: HttpErpGateway) -> None:
    customer = await gateway.get_customer(1)
    assert customer.name == "Acme Corp"
    assert customer.tier == "gold"


async def test_get_customer_raises_on_unknown(gateway: HttpErpGateway) -> None:
    with pytest.raises(ApiConnectorError):
        await gateway.get_customer(999)


async def test_list_tickets_returns_all_statuses(gateway: HttpErpGateway) -> None:
    tickets = await gateway.list_tickets(1)
    assert {t.status for t in tickets} == {"open"}


async def test_create_ticket_is_idempotent(gateway: HttpErpGateway) -> None:
    first = await gateway.create_ticket(2, "Probleme connexion", idempotency_key="k-123")
    second = await gateway.create_ticket(2, "Probleme connexion", idempotency_key="k-123")
    assert first.id == second.id
