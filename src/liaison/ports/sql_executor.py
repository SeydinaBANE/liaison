"""Port d'execution SQL : separe la politique de gouvernance (domaine) de l'infrastructure.

``SqlConnector`` (application) valide une requete via ``SqlGuard`` puis delegue son
execution a ce port, sans connaitre le moteur SQL concret (SQLAlchemy, autre).
"""

from __future__ import annotations

from typing import Protocol


class SqlExecutor(Protocol):
    """Contrat d'execution d'une requete SQL deja validee."""

    async def execute(self, sql: str) -> list[dict[str, object]]:
        """Execute la requete et retourne les lignes sous forme de mappings."""
        ...
