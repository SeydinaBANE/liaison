"""Connecteur API asynchrone : orchestre les appels vers un ERP/CRM existant.

Use case applicatif : ne connait que le port ``ErpGateway``, jamais le client HTTP concret.
Applique les regles metier de presentation (filtrage des tickets ouverts, resolution du
client cible depuis la question) avant de construire les ``Evidence`` citables.
"""

from __future__ import annotations

from dataclasses import asdict

from liaison.domain.entities import extract_customer_id
from liaison.domain.models import Evidence, SourceKind
from liaison.platform.observability import METRICS
from liaison.ports.erp_gateway import ErpGateway


class ApiConnector:
    """Encapsule les appels metier vers l'ERP/CRM via le port ``ErpGateway`` injecte."""

    def __init__(self, gateway: ErpGateway, name_to_id: dict[str, int] | None = None) -> None:
        self._gateway = gateway
        self._name_to_id = name_to_id or {}

    async def get_customer(self, customer_id: int) -> Evidence:
        """Recupere la fiche client et la retourne sous forme d'evidence."""
        customer = await self._gateway.get_customer(customer_id)
        METRICS.incr("api.read.success")
        return Evidence(
            kind=SourceKind.API,
            summary=f"client {customer.name} (tier {customer.tier})",
            payload={k: str(v) for k, v in asdict(customer).items()},
        )

    async def list_open_tickets(self, customer_id: int) -> Evidence:
        """Liste les tickets ouverts d'un client."""
        tickets = [t for t in await self._gateway.list_tickets(customer_id) if t.status == "open"]
        METRICS.incr("api.read.success")
        return Evidence(
            kind=SourceKind.API,
            summary=f"{len(tickets)} ticket(s) ouvert(s)",
            payload={"tickets": str([asdict(t) for t in tickets])},
        )

    async def create_ticket(self, customer_id: int, subject: str, idempotency_key: str) -> Evidence:
        """Cree un ticket (write-back) protege par une cle d'idempotence."""
        ticket = await self._gateway.create_ticket(customer_id, subject, idempotency_key)
        METRICS.incr("api.write.success")
        return Evidence(
            kind=SourceKind.API,
            summary=f"ticket {ticket.id} cree",
            payload={k: str(v) for k, v in asdict(ticket).items()},
        )

    async def answer(self, question: str) -> Evidence:
        """Resout le client cible puis croise fiche client et tickets ouverts."""
        customer_id = extract_customer_id(question, self._name_to_id)
        if customer_id is None:
            return Evidence(kind=SourceKind.API, summary="aucun client identifie dans la question")
        customer = await self.get_customer(customer_id)
        tickets = await self.list_open_tickets(customer_id)
        return Evidence(
            kind=SourceKind.API,
            summary=f"{customer.summary}; {tickets.summary}",
            payload={**customer.payload, **tickets.payload},
        )
