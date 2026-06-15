"""Mock d'un ERP/CRM existant expose en REST (cible du connecteur API).

Sert de systeme tiers realiste pour la demo : lecture de clients/tickets et write-back
idempotent (creation de ticket protegee par cle d'idempotence).
"""

from __future__ import annotations

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Mock ERP/CRM", version="1.0.0")

_CUSTOMERS: dict[int, dict[str, str]] = {
    1: {"name": "Acme Corp", "tier": "gold", "balance": "1250.00"},
    2: {"name": "Globex", "tier": "silver", "balance": "0.00"},
}
_TICKETS: dict[int, dict[str, str]] = {
    10: {"customer_id": "1", "subject": "Litige facturation", "status": "open"},
}
_IDEMPOTENCY: dict[str, int] = {}


class Customer(BaseModel):
    """Fiche client renvoyee par l'ERP."""

    id: int
    name: str
    tier: str
    balance: str


class Ticket(BaseModel):
    """Ticket support renvoye par l'ERP."""

    id: int
    customer_id: int
    subject: str
    status: str


class TicketCreate(BaseModel):
    """Charge utile de creation d'un ticket."""

    customer_id: int
    subject: str = Field(min_length=1)


@app.get("/customers/{customer_id}", response_model=Customer)
def get_customer(customer_id: int) -> Customer:
    """Retourne une fiche client ou 404."""
    data = _CUSTOMERS.get(customer_id)
    if data is None:
        raise HTTPException(status_code=404, detail="client inconnu")
    return Customer(id=customer_id, **data)


@app.get("/customers/{customer_id}/tickets", response_model=list[Ticket])
def list_tickets(customer_id: int) -> list[Ticket]:
    """Liste les tickets d'un client."""
    return [
        Ticket(id=tid, customer_id=int(t["customer_id"]), subject=t["subject"], status=t["status"])
        for tid, t in _TICKETS.items()
        if int(t["customer_id"]) == customer_id
    ]


@app.post("/tickets", response_model=Ticket, status_code=201)
def create_ticket(
    payload: TicketCreate,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
) -> Ticket:
    """Cree un ticket ; rejouer la meme cle d'idempotence renvoie le ticket existant."""
    if idempotency_key in _IDEMPOTENCY:
        existing = _IDEMPOTENCY[idempotency_key]
        stored = _TICKETS[existing]
        return Ticket(
            id=existing,
            customer_id=int(stored["customer_id"]),
            subject=stored["subject"],
            status=stored["status"],
        )
    new_id = max(_TICKETS) + 1 if _TICKETS else 1
    _TICKETS[new_id] = {
        "customer_id": str(payload.customer_id),
        "subject": payload.subject,
        "status": "open",
    }
    _IDEMPOTENCY[idempotency_key] = new_id
    return Ticket(
        id=new_id,
        customer_id=payload.customer_id,
        subject=payload.subject,
        status="open",
    )
