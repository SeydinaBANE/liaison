"""Adapter ERP/CRM via HTTP (httpx). Implemente le port ``ErpGateway``."""

from __future__ import annotations

import httpx

from liaison.platform.observability import record_span
from liaison.ports.erp_gateway import ApiConnectorError, CustomerRecord, TicketRecord


class HttpErpGateway:
    """Appelle un ERP/CRM existant en REST via un client HTTP asynchrone injecte."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def get_customer(self, customer_id: int) -> CustomerRecord:
        """Recupere la fiche client ; leve ``ApiConnectorError`` si inconnu."""
        with record_span("api.get_customer", customer_id=str(customer_id)):
            response = await self._client.get(f"/customers/{customer_id}")
        if response.status_code == 404:
            raise ApiConnectorError(f"client {customer_id} introuvable")
        response.raise_for_status()
        data = response.json()
        return CustomerRecord(
            id=int(data["id"]),
            name=str(data["name"]),
            tier=str(data["tier"]),
            balance=str(data["balance"]),
        )

    async def list_tickets(self, customer_id: int) -> list[TicketRecord]:
        """Liste tous les tickets (tous statuts) d'un client."""
        with record_span("api.list_tickets", customer_id=str(customer_id)):
            response = await self._client.get(f"/customers/{customer_id}/tickets")
        response.raise_for_status()
        return [
            TicketRecord(
                id=int(t["id"]),
                customer_id=int(t["customer_id"]),
                subject=str(t["subject"]),
                status=str(t["status"]),
            )
            for t in response.json()
        ]

    async def create_ticket(
        self, customer_id: int, subject: str, idempotency_key: str
    ) -> TicketRecord:
        """Cree un ticket (write-back) protege par une cle d'idempotence."""
        with record_span("api.create_ticket", customer_id=str(customer_id)):
            response = await self._client.post(
                "/tickets",
                json={"customer_id": customer_id, "subject": subject},
                headers={"Idempotency-Key": idempotency_key},
            )
        response.raise_for_status()
        data = response.json()
        return TicketRecord(
            id=int(data["id"]),
            customer_id=int(data["customer_id"]),
            subject=str(data["subject"]),
            status=str(data["status"]),
        )
