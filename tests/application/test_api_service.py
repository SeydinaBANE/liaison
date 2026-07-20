"""Tests du use case ERP/CRM, sans reseau (port ``ErpGateway`` fake)."""

from __future__ import annotations

import pytest

from liaison.application.api_service import ApiConnector
from liaison.domain.models import SourceKind
from liaison.ports.erp_gateway import ApiConnectorError, CustomerRecord, TicketRecord

_NAME_TO_ID = {"acme": 1}


class _FakeErpGateway:
    def __init__(self) -> None:
        self._customers = {
            1: CustomerRecord(id=1, name="Acme Corp", tier="gold", balance="1250.00")
        }
        self._tickets = {
            1: [
                TicketRecord(id=10, customer_id=1, subject="Litige facturation", status="open"),
                TicketRecord(id=11, customer_id=1, subject="Autre", status="closed"),
            ]
        }
        self._created: dict[str, TicketRecord] = {}

    async def get_customer(self, customer_id: int) -> CustomerRecord:
        record = self._customers.get(customer_id)
        if record is None:
            raise ApiConnectorError(f"client {customer_id} introuvable")
        return record

    async def list_tickets(self, customer_id: int) -> list[TicketRecord]:
        return self._tickets.get(customer_id, [])

    async def create_ticket(
        self, customer_id: int, subject: str, idempotency_key: str
    ) -> TicketRecord:
        if idempotency_key in self._created:
            return self._created[idempotency_key]
        ticket = TicketRecord(id=99, customer_id=customer_id, subject=subject, status="open")
        self._created[idempotency_key] = ticket
        return ticket


async def test_get_customer_returns_evidence() -> None:
    connector = ApiConnector(_FakeErpGateway())
    evidence = await connector.get_customer(1)
    assert evidence.kind == SourceKind.API
    assert "Acme" in evidence.summary


async def test_get_customer_raises_on_unknown() -> None:
    connector = ApiConnector(_FakeErpGateway())
    with pytest.raises(ApiConnectorError):
        await connector.get_customer(999)


async def test_list_open_tickets_filters_status() -> None:
    connector = ApiConnector(_FakeErpGateway())
    evidence = await connector.list_open_tickets(1)
    assert "1 ticket" in evidence.summary


async def test_create_ticket_is_idempotent() -> None:
    connector = ApiConnector(_FakeErpGateway())
    first = await connector.create_ticket(2, "Probleme connexion", idempotency_key="k-123")
    second = await connector.create_ticket(2, "Probleme connexion", idempotency_key="k-123")
    assert first.payload["id"] == second.payload["id"]


async def test_answer_combines_customer_and_open_tickets() -> None:
    connector = ApiConnector(_FakeErpGateway(), _NAME_TO_ID)
    evidence = await connector.answer("y a-t-il un litige chez Acme ?")
    assert "Acme" in evidence.summary
    assert "1 ticket" in evidence.summary


async def test_answer_returns_placeholder_when_no_customer_identified() -> None:
    connector = ApiConnector(_FakeErpGateway(), _NAME_TO_ID)
    evidence = await connector.answer("bonjour, comment ca va ?")
    assert evidence.summary == "aucun client identifie dans la question"
