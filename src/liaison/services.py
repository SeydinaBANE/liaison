"""Composition root : assemble gateway, connecteurs et orchestrateur.

L'assemblage par defaut est entierement en-process (SQLite seede + GED en memoire) afin que
l'application demarre sans dependance externe ; en production on injecte un engine Postgres
et un retriever Qdrant. C'est le seul endroit du code qui choisit une implementation
concrete (adapter) pour chaque port, selon la configuration.
"""

from __future__ import annotations

import httpx
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.pool import StaticPool

from liaison.adapters.outbound.erp.http_gateway import HttpErpGateway
from liaison.adapters.outbound.llm.http_provider import HttpLLMProvider
from liaison.adapters.outbound.llm.local_provider import LocalProvider
from liaison.adapters.outbound.retriever.in_memory import InMemoryRetriever
from liaison.adapters.outbound.retriever.qdrant import QdrantRetriever
from liaison.adapters.outbound.sql.sqlalchemy_executor import SQLAlchemyExecutor
from liaison.application.api_service import ApiConnector
from liaison.application.docs_service import DocsConnector
from liaison.application.llm_gateway import LLMGateway
from liaison.application.orchestrator import Orchestrator
from liaison.application.sql_service import SqlConnector
from liaison.domain.models import SourceKind
from liaison.domain.routing import Tool
from liaison.domain.sql_policy import SemanticLayer, TableSchema
from liaison.platform.config import Settings, get_settings
from liaison.ports.retriever import Document

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


async def _build_retriever() -> QdrantRetriever | InMemoryRetriever:
    """Retourne un retriever Qdrant si configure, sinon InMemoryRetriever demo."""
    cfg = get_settings()
    if cfg.qdrant_url:
        return QdrantRetriever(url=cfg.qdrant_url, collection=cfg.qdrant_collection)
    return InMemoryRetriever(_DEMO_DOCS)


def _build_async_http_client(cfg: Settings) -> httpx.AsyncClient:
    """Construit le client HTTP async du provider LLM."""
    headers = {"Authorization": f"Bearer {cfg.llm_api_key}"} if cfg.llm_api_key else {}
    return httpx.AsyncClient(base_url=cfg.llm_api_base, headers=headers, timeout=30.0)


def build_default_gateway(
    settings: Settings | None = None,
    http_client: httpx.AsyncClient | None = None,
) -> LLMGateway:
    """Construit le gateway selon la configuration.

    Si ``llm_api_base`` est renseigne, utilise un provider HTTP reel (primaire + fallback) ;
    sinon, retombe sur ``LocalProvider`` deterministe pour fonctionner hors-ligne.
    """
    cfg = settings or get_settings()
    if not cfg.llm_api_base:
        return LLMGateway(
            primary=LocalProvider(model=cfg.llm_model_primary),
            fallback=LocalProvider(model=cfg.llm_model_fallback),
        )
    client = http_client or _build_async_http_client(cfg)
    return LLMGateway(
        primary=HttpLLMProvider(model=cfg.llm_model_primary, client=client),
        fallback=HttpLLMProvider(model=cfg.llm_model_fallback, client=client),
    )


async def build_orchestrator(api_client: httpx.AsyncClient | None = None) -> Orchestrator:
    """Assemble un orchestrateur cable sur les connecteurs SQL, API (ERP/CRM) et GED.

    En production (DSN non-local), utilise Postgres et Qdrant. En local, SQLite seede + memoire.
    Le client HTTP peut etre injecte (tests).
    """
    gateway = build_default_gateway()
    executor = SQLAlchemyExecutor(_build_engine())
    sql_connector = SqlConnector(executor, SemanticLayer(_DEMO_TABLES), gateway)
    retriever = await _build_retriever()
    docs_connector = DocsConnector(retriever)
    client = api_client or httpx.AsyncClient(base_url=get_settings().erp_base_url, timeout=10.0)
    _clients.append(client)
    api_connector = ApiConnector(HttpErpGateway(client), _DEMO_NAME_TO_ID)

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
            runner=api_connector.answer,
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
