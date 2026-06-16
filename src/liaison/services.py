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
from liaison.connectors.docs import DocsConnector, Document, InMemoryRetriever, QdrantRetriever
from liaison.connectors.sql import SemanticLayer, SqlConnector, TableSchema
from liaison.entities import extract_customer_id
from liaison.gateway import build_default_gateway
from liaison.orchestrator import Orchestrator, Tool
from liaison.schemas import Evidence, SourceKind

_DEMO_NAME_TO_ID = {"acme": 1, "globex": 2}

_clients: list[httpx.AsyncClient] = []
_engines: list[Engine] = []

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


def _build_engine() -> Engine:
    """Cree l'engine SQL selon la configuration : Postgres si DSN renseigne, sinon SQLite demo."""
    cfg = get_settings()
    if cfg.sql_dsn and not cfg.sql_dsn.startswith("postgresql+psycopg://liaison:liaison@localhost"):
        engine = create_engine(
            cfg.sql_dsn,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
        )
        _engines.append(engine)
        return engine
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


async def _api_runner(api_connector: ApiConnector, question: str) -> Evidence:
    """Resout le client cible puis croise fiche client et tickets ouverts."""
    customer_id = extract_customer_id(question, _DEMO_NAME_TO_ID)
    if customer_id is None:
        return Evidence(kind=SourceKind.API, summary="aucun client identifie dans la question")
    customer = await api_connector.get_customer(customer_id)
    tickets = await api_connector.list_open_tickets(customer_id)
    return Evidence(
        kind=SourceKind.API,
        summary=f"{customer.summary}; {tickets.summary}",
        payload={**customer.payload, **tickets.payload},
    )


async def _build_retriever() -> QdrantRetriever | InMemoryRetriever:
    """Retourne un retriever Qdrant si configure, sinon InMemoryRetriever demo."""
    cfg = get_settings()
    if cfg.qdrant_url:
        return QdrantRetriever(url=cfg.qdrant_url, collection=cfg.qdrant_collection)
    return InMemoryRetriever(_DEMO_DOCS)


async def build_orchestrator(api_client: httpx.AsyncClient | None = None) -> Orchestrator:
    """Assemble un orchestrateur cable sur les connecteurs SQL, API (ERP/CRM) et GED.

    En production (DSN non-local), utilise Postgres et Qdrant. En local, SQLite seede + memoire.
    Le client HTTP peut etre injecte (tests).
    """
    gateway = build_default_gateway()
    sql_connector = SqlConnector(_build_engine(), SemanticLayer(_DEMO_TABLES), gateway)
    retriever = await _build_retriever()
    docs_connector = DocsConnector(retriever)
    client = api_client or httpx.AsyncClient(base_url=get_settings().erp_base_url, timeout=10.0)
    _clients.append(client)
    api_connector = ApiConnector(client)

    tools = [
        Tool(
            name="sql",
            description="Interroge la base metier (encours, tickets) en text-to-SQL gouverne.",
            keywords=frozenset({"encours", "balance", "montant", "facture"}),
            runner=sql_connector.query,
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
            runner=docs_connector.search,
            source_kind=SourceKind.DOCS,
        ),
    ]
    return Orchestrator(gateway, tools)


async def _cleanup() -> None:
    """Ferme toutes les ressources acquises (clients HTTP async, engines DB)."""
    while _clients:
        client = _clients.pop()
        await client.aclose()
    while _engines:
        engine = _engines.pop()
        engine.dispose()
