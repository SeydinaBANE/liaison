"""Port ERP/CRM : separe l'appel HTTP brut (infrastructure) de la construction d'``Evidence``.

``ApiConnector`` (application) consomme ce port pour lire/ecrire dans le systeme tiers sans
connaitre le client HTTP concret (httpx, autre).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class ApiConnectorError(RuntimeError):
    """Echec d'appel au systeme ERP/CRM."""


@dataclass(frozen=True)
class CustomerRecord:
    """Fiche client telle que renvoyee par le systeme ERP/CRM."""

    id: int
    name: str
    tier: str
    balance: str


@dataclass(frozen=True)
class TicketRecord:
    """Ticket support tel que renvoye par le systeme ERP/CRM."""

    id: int
    customer_id: int
    subject: str
    status: str


class ErpGateway(Protocol):
    """Contrat d'acces au systeme ERP/CRM existant."""

    async def get_customer(self, customer_id: int) -> CustomerRecord:
        """Retourne la fiche client ; leve ``ApiConnectorError`` si inconnu."""
        ...

    async def list_tickets(self, customer_id: int) -> list[TicketRecord]:
        """Liste tous les tickets (tous statuts) d'un client."""
        ...

    async def create_ticket(
        self, customer_id: int, subject: str, idempotency_key: str
    ) -> TicketRecord:
        """Cree un ticket (write-back) protege par une cle d'idempotence."""
        ...
