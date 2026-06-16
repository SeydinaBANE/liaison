"""Connecteur SQL asynchrone : text-to-SQL gouverne sur une base metier existante.

Le LLM ne touche jamais la base directement. Il propose une requete a partir d'une couche
semantique (descriptions de tables/colonnes), puis un garde-fou (``SqlGuard``) valide la
requete avant execution : statement unique, lecture seule par defaut, tables en allow-list,
mots-cles dangereux interdits. L'execution SQL reste synchrone, encapsulee dans
``asyncio.to_thread`` pour ne pas bloquer la boucle d'evenements.
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass

from sqlalchemy import Engine, text

from liaison.gateway import LLMGateway
from liaison.observability import METRICS, record_span
from liaison.schemas import Evidence, LLMRequest, Message, Role, SourceKind

_FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|truncate|create|grant|revoke|attach|pragma)\b",
    re.IGNORECASE,
)
_TABLE_REF = re.compile(r"\b(?:from|join)\s+([a-zA-Z_][a-zA-Z0-9_]*)", re.IGNORECASE)
_SQL_FENCE = re.compile(r"```(?:sql)?\s*(.*?)\s*```", re.IGNORECASE | re.DOTALL)


class SqlGovernanceError(RuntimeError):
    """Requete SQL refusee par le garde-fou de gouvernance."""


@dataclass(frozen=True)
class TableSchema:
    """Description semantique d'une table exposee au LLM."""

    name: str
    description: str
    columns: dict[str, str]


class SemanticLayer:
    """Catalogue des tables autorisees et de leur description metier."""

    def __init__(self, tables: list[TableSchema]) -> None:
        self._tables = {t.name: t for t in tables}

    @property
    def allowed_tables(self) -> frozenset[str]:
        """Ensemble des noms de tables autorisees."""
        return frozenset(self._tables)

    def render(self) -> str:
        """Rend le catalogue sous forme textuelle pour le prompt du LLM."""
        lines: list[str] = []
        for table in self._tables.values():
            cols = ", ".join(f"{c} ({d})" for c, d in table.columns.items())
            lines.append(f"- {table.name}: {table.description}. Colonnes: {cols}")
        return "\n".join(lines)


class SqlGuard:
    """Valide qu'une requete SQL respecte la politique de gouvernance."""

    def __init__(self, allowed_tables: frozenset[str], readonly: bool = True) -> None:
        self._allowed = allowed_tables
        self._readonly = readonly

    def validate(self, sql: str) -> str:
        """Retourne la requete nettoyee si elle est conforme, sinon leve ``SqlGovernanceError``."""
        cleaned = sql.strip().rstrip(";").strip()
        if not cleaned:
            raise SqlGovernanceError("requete vide")
        if ";" in cleaned:
            raise SqlGovernanceError("plusieurs statements interdits")
        if self._readonly and not cleaned.lower().startswith(("select", "with")):
            raise SqlGovernanceError("seules les lectures (SELECT) sont autorisees")
        if self._readonly and _FORBIDDEN.search(cleaned):
            raise SqlGovernanceError("mot-cle de modification interdit en lecture seule")
        referenced = {t.lower() for t in _TABLE_REF.findall(cleaned)}
        forbidden = {t for t in referenced if t not in self._allowed}
        if forbidden:
            raise SqlGovernanceError(f"table(s) hors allow-list: {sorted(forbidden)}")
        return cleaned


def _extract_sql(raw: str) -> str:
    """Extrait la requete SQL d'une reponse LLM (avec ou sans bloc de code)."""
    match = _SQL_FENCE.search(raw)
    return match.group(1).strip() if match else raw.strip()


class SqlConnector:
    """Traduit une question en SQL, la valide puis l'execute en lecture seule."""

    def __init__(
        self,
        engine: Engine,
        semantic_layer: SemanticLayer,
        gateway: LLMGateway,
        readonly: bool = True,
    ) -> None:
        self._engine = engine
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
        return self._guard.validate(_extract_sql(raw))

    def _execute_query(self, sql: str) -> list[dict[str, object]]:
        """Execute une requete SQL (synchrone, lancee dans un thread)."""
        with record_span("sql.execute", sql=sql), self._engine.connect() as conn:
            return [dict(r) for r in conn.execute(text(sql)).mappings()]

    async def query(self, question: str) -> Evidence:
        """Genere, valide, execute la requete et retourne une evidence citable."""
        sql = await self.generate_sql(question)
        rows = await asyncio.to_thread(self._execute_query, sql)
        METRICS.incr("sql.query.success")
        return Evidence(
            kind=SourceKind.SQL,
            summary=f"{len(rows)} ligne(s) via SQL",
            payload={"sql": sql, "rows": str(rows)},
        )
