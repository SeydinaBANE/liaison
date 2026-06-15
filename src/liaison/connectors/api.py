"""Connecteur API : orchestre les appels vers un ERP/CRM existant en REST.

Lecture (fiche client, tickets) et write-back idempotent (creation de ticket). Le client
HTTP est injecte pour permettre les tests sans reseau.
"""

from __future__ import annotations

import httpx

from liaison.observability import METRICS, record_span
from liaison.schemas import Evidence, SourceKind


class ApiConnectorError(RuntimeError):
    """Echec d'appel au systeme ERP/CRM."""


class ApiConnector:
    """Encapsule les appels metier vers l'ERP/CRM via un client HTTP injecte."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def get_customer(self, customer_id: int) -> Evidence:
        """Recupere la fiche client et la retourne sous forme d'evidence."""
        with record_span("api.get_customer", customer_id=str(customer_id)):
            response = self._client.get(f"/customers/{customer_id}")
        if response.status_code == 404:
            raise ApiConnectorError(f"client {customer_id} introuvable")
        response.raise_for_status()
        data = response.json()
        METRICS.incr("api.read.success")
        return Evidence(
            kind=SourceKind.API,
            summary=f"client {data['name']} (tier {data['tier']})",
            payload={k: str(v) for k, v in data.items()},
        )

    def list_open_tickets(self, customer_id: int) -> Evidence:
        """Liste les tickets ouverts d'un client."""
        with record_span("api.list_tickets", customer_id=str(customer_id)):
            response = self._client.get(f"/customers/{customer_id}/tickets")
        response.raise_for_status()
        tickets = [t for t in response.json() if t["status"] == "open"]
        METRICS.incr("api.read.success")
        return Evidence(
            kind=SourceKind.API,
            summary=f"{len(tickets)} ticket(s) ouvert(s)",
            payload={"tickets": str(tickets)},
        )

    def create_ticket(self, customer_id: int, subject: str, idempotency_key: str) -> Evidence:
        """Cree un ticket (write-back) protege par une cle d'idempotence."""
        with record_span("api.create_ticket", customer_id=str(customer_id)):
            response = self._client.post(
                "/tickets",
                json={"customer_id": customer_id, "subject": subject},
                headers={"Idempotency-Key": idempotency_key},
            )
        response.raise_for_status()
        data = response.json()
        METRICS.incr("api.write.success")
        return Evidence(
            kind=SourceKind.API,
            summary=f"ticket {data['id']} cree",
            payload={k: str(v) for k, v in data.items()},
        )
