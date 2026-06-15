"""Composition root : assemble gateway, connecteurs et orchestrateur.

L'assemblage par defaut est entierement en-process (SQLite seede + GED en memoire) afin que
l'application demarre sans dependance externe ; en production on injecte un engine Postgres
et un retriever Qdrant.
"""

from __future__ import annotations

import httpx
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.pool import StaticPool

from liaison.config import get_settings
from liaison.connectors.api import ApiConnector
from liaison.connectors.docs import DocsConnector, Document, InMemoryRetriever
from liaison.connectors.sql import SemanticLayer, SqlConnector, TableSchema
from liaison.entities import extract_customer_id
from liaison.gateway import build_default_gateway
from liaison.orchestrator import Orchestrator, Tool
from liaison.schemas import Evidence, SourceKind

_DEMO_NAME_TO_ID = {"acme": 1, "globex": 2}

_DEMO_DOCS = [
    Document(
        doc_id="contrat-acme",
        title="Contrat Acme",
        content="Le contrat Acme prevoit une penalite en cas de litige de facturation non resolu.",
    ),
    Document(
        doc_id="procedure-support",
        title="Procedure support",
        content="Un litige de facturation ouvre un ticket prioritaire traite sous 48 heures.",
    ),
]

_DEMO_TABLES = [
    TableSchema(
        name="customers",
        description="clients et leur encours",
        columns={"id": "identifiant", "name": "nom", "balance": "encours"},
    ),
    TableSchema(
        name="tickets",
        description="tickets support",
        columns={"id": "identifiant", "customer_id": "client", "status": "statut"},
    ),
]


def build_demo_engine() -> Engine:
    """Cree un engine SQLite en memoire seede pour la demo locale."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.begin() as conn:
        conn.execute(
            text("CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT, balance REAL)")
        )
        conn.execute(
            text("CREATE TABLE tickets (id INTEGER PRIMARY KEY, customer_id INTEGER, status TEXT)")
        )
        conn.execute(
            text(
                "INSERT INTO customers (id, name, balance) VALUES "
                "(1, 'Acme', 1250.0), (2, 'Globex', 0.0)"
            )
        )
        conn.execute(text("INSERT INTO tickets (id, customer_id, status) VALUES (10, 1, 'open')"))
    return engine


def _api_runner(api_connector: ApiConnector, question: str) -> Evidence:
    """Resout le client cible puis croise fiche client et tickets ouverts."""
    customer_id = extract_customer_id(question, _DEMO_NAME_TO_ID)
    if customer_id is None:
        return Evidence(kind=SourceKind.API, summary="aucun client identifie dans la question")
    customer = api_connector.get_customer(customer_id)
    tickets = api_connector.list_open_tickets(customer_id)
    return Evidence(
        kind=SourceKind.API,
        summary=f"{customer.summary}; {tickets.summary}",
        payload={**customer.payload, **tickets.payload},
    )


def build_orchestrator(api_client: httpx.Client | None = None) -> Orchestrator:
    """Assemble un orchestrateur demo cable sur les connecteurs SQL, API (ERP/CRM) et GED.

    Le client HTTP de l'ERP peut etre injecte (tests) ; sinon il pointe sur ``erp_base_url``.
    """
    gateway = build_default_gateway()
    sql_connector = SqlConnector(build_demo_engine(), SemanticLayer(_DEMO_TABLES), gateway)
    docs_connector = DocsConnector(InMemoryRetriever(_DEMO_DOCS))
    client = api_client or httpx.Client(base_url=get_settings().erp_base_url, timeout=10.0)
    api_connector = ApiConnector(client)

    tools = [
        Tool(
            name="sql",
            description="Interroge la base metier (encours, tickets) en text-to-SQL gouverne.",
            keywords=frozenset({"encours", "balance", "montant", "facture"}),
            runner=lambda q: sql_connector.query(q),
            source_kind=SourceKind.SQL,
        ),
        Tool(
            name="api",
            description="Consulte l'ERP/CRM (fiche client, tickets ouverts).",
            keywords=frozenset({"client", "ticket", "litige", "statut", "compte"}),
            runner=lambda q: _api_runner(api_connector, q),
            source_kind=SourceKind.API,
        ),
        Tool(
            name="docs",
            description="Recherche dans la GED (contrats, procedures).",
            keywords=frozenset({"contrat", "clause", "procedure", "penalite", "litige"}),
            runner=lambda q: docs_connector.search(q),
            source_kind=SourceKind.DOCS,
        ),
    ]
    return Orchestrator(gateway, tools)
