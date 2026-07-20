"""Adapter d'execution SQL via SQLAlchemy.

Implemente le port ``SqlExecutor`` : l'execution reste synchrone, encapsulee dans
``asyncio.to_thread`` pour ne pas bloquer la boucle d'evenements.
"""

from __future__ import annotations

import asyncio

from sqlalchemy import Engine, text


class SQLAlchemyExecutor:
    """Execute une requete SQL deja validee via un ``Engine`` SQLAlchemy."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def _execute_query(self, sql: str) -> list[dict[str, object]]:
        with self._engine.connect() as conn:
            return [dict(r) for r in conn.execute(text(sql)).mappings()]

    async def execute(self, sql: str) -> list[dict[str, object]]:
        """Execute la requete (synchrone, lancee dans un thread)."""
        return await asyncio.to_thread(self._execute_query, sql)
