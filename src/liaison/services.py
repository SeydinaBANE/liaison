"""Composition root : assemble gateway, connecteurs et orchestrateur.

L'assemblage par defaut est entierement en-process (SQLite seede + GED en memoire) afin que
l'application demarre sans dependance externe ; en production on injecte un engine Postgres
et un retriever Qdrant.
"""

from __future__ import annotations

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.pool import StaticPool

from liaison.connectors.docs import DocsConnector, Document, InMemoryRetriever
from liaison.connectors.sql import SemanticLayer, SqlConnector, TableSchema
from liaison.gateway import build_default_gateway
from liaison.orchestrator import Orchestrator, Tool
from liaison.schemas import SourceKind

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


def build_orchestrator() -> Orchestrator:
    """Assemble un orchestrateur demo cable sur les connecteurs SQL et GED."""
    gateway = build_default_gateway()
    sql_connector = SqlConnector(build_demo_engine(), SemanticLayer(_DEMO_TABLES), gateway)
    docs_connector = DocsConnector(InMemoryRetriever(_DEMO_DOCS))

    tools = [
        Tool(
            name="sql",
            description="Interroge la base metier (encours, tickets) en text-to-SQL gouverne.",
            keywords=frozenset({"encours", "balance", "montant", "facture", "client", "ticket"}),
            runner=lambda q: sql_connector.query(q),
            source_kind=SourceKind.SQL,
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
