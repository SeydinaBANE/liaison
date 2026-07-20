"""Garantie d'idempotence des ecritures."""

from __future__ import annotations


class IdempotencyGuard:
    """Empeche le rejeu d'une ecriture : memorise les cles deja traitees."""

    def __init__(self) -> None:
        self._seen: set[str] = set()

    def is_new(self, key: str) -> bool:
        """Retourne True si la cle n'a jamais ete vue, et l'enregistre."""
        if key in self._seen:
            return False
        self._seen.add(key)
        return True
