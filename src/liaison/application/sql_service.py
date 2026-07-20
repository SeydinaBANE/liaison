"""Connecteur SQL asynchrone : text-to-SQL gouverne sur une base metier existante.

Use case applicatif : genere une requete via le gateway LLM, la valide via la politique de
gouvernance du domaine (``SqlGuard``), puis delegue son execution au port ``SqlExecutor``
sans connaitre le moteur SQL concret.
"""

from __future__ import annotations

from liaison.application.llm_gateway import LLMGateway
from liaison.domain.models import Evidence, LLMRequest, Message, Role, SourceKind
from liaison.domain.sql_policy import SemanticLayer, SqlGuard, extract_sql
from liaison.platform.observability import METRICS, record_span
from liaison.ports.sql_executor import SqlExecutor


class SqlConnector:
    """Traduit une question en SQL, la valide puis l'execute en lecture seule."""

    def __init__(
        self,
        executor: SqlExecutor,
        semantic_layer: SemanticLayer,
        gateway: LLMGateway,
        readonly: bool = True,
    ) -> None:
        self._executor = executor
        self._semantic = semantic_layer
        self._gateway = gateway
        self._guard = SqlGuard(semantic_layer.allowed_tables, readonly=readonly)

    def _build_prompt(self, question: str) -> LLMRequest:
        system = (
            "Tu es un generateur SQL pour PostgreSQL. Reponds UNIQUEMENT par une requete "
            "SELECT valide, sans explication. Tables disponibles:\n"
            f"{self._semantic.render()}"
        )
        return LLMRequest(
            messages=[
                Message(role=Role.SYSTEM, content=system),
                Message(role=Role.USER, content=question),
            ]
        )

    async def generate_sql(self, question: str) -> str:
        """Genere et valide une requete SQL a partir d'une question en langage naturel."""
        with record_span("sql.generate"):
            raw = (await self._gateway.complete(self._build_prompt(question))).content
        return self._guard.validate(extract_sql(raw))

    async def query(self, question: str) -> Evidence:
        """Genere, valide, execute la requete et retourne une evidence citable."""
        sql = await self.generate_sql(question)
        with record_span("sql.execute", sql=sql):
            rows = await self._executor.execute(sql)
        METRICS.incr("sql.query.success")
        return Evidence(
            kind=SourceKind.SQL,
            summary=f"{len(rows)} ligne(s) via SQL",
            payload={"sql": sql, "rows": str(rows)},
        )
