"""Couche de gouvernance transverse : RBAC, masquage PII, idempotence et audit.

Appliquee autour des connecteurs : autorise (ou refuse) une action selon le role de
l'appelant, masque les donnees personnelles dans les sorties, garantit l'idempotence des
ecritures et journalise chaque decision pour tracabilite.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from enum import StrEnum

from liaison.logging import get_logger
from liaison.observability import METRICS

logger = get_logger(__name__)

_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_PHONE = re.compile(r"\b(?:\+?\d[\s.-]?){9,}\d\b")


class AccessDeniedError(RuntimeError):
    """Action refusee par la politique RBAC."""


class Permission(StrEnum):
    """Permissions atomiques exposees par les connecteurs."""

    READ_SQL = "read_sql"
    READ_API = "read_api"
    WRITE_API = "write_api"
    READ_DOCS = "read_docs"


@dataclass(frozen=True)
class Principal:
    """Appelant authentifie : identifiant et roles."""

    user_id: str
    roles: frozenset[str]


_ROLE_PERMISSIONS: dict[str, frozenset[Permission]] = {
    "viewer": frozenset({Permission.READ_SQL, Permission.READ_API, Permission.READ_DOCS}),
    "operator": frozenset(
        {Permission.READ_SQL, Permission.READ_API, Permission.READ_DOCS, Permission.WRITE_API}
    ),
}


class RBACPolicy:
    """Politique de controle d'acces basee sur les roles."""

    def __init__(self, role_permissions: dict[str, frozenset[Permission]] | None = None) -> None:
        self._role_permissions = role_permissions or _ROLE_PERMISSIONS

    def permissions_of(self, principal: Principal) -> frozenset[Permission]:
        """Union des permissions accordees par les roles du principal."""
        granted: set[Permission] = set()
        for role in principal.roles:
            granted |= self._role_permissions.get(role, frozenset())
        return frozenset(granted)

    def authorize(self, principal: Principal, permission: Permission) -> None:
        """Leve ``AccessDeniedError`` si le principal ne possede pas la permission."""
        if permission not in self.permissions_of(principal):
            METRICS.incr("governance.access_denied")
            raise AccessDeniedError(f"{principal.user_id} non autorise pour {permission}")


def mask_pii(text: str) -> str:
    """Masque emails et numeros de telephone dans un texte."""
    masked = _EMAIL.sub("[email]", text)
    return _PHONE.sub("[phone]", masked)


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


@dataclass(frozen=True)
class AuditEntry:
    """Entree d'audit immuable."""

    user_id: str
    action: str
    resource: str
    allowed: bool
    timestamp: float


@dataclass
class AuditLog:
    """Journal d'audit append-only en memoire."""

    entries: list[AuditEntry] = field(default_factory=list)

    def record(self, principal: Principal, action: str, resource: str, allowed: bool) -> None:
        """Ajoute une entree d'audit et la trace."""
        entry = AuditEntry(
            user_id=principal.user_id,
            action=action,
            resource=resource,
            allowed=allowed,
            timestamp=time.time(),
        )
        self.entries.append(entry)
        logger.info(
            "audit",
            user=principal.user_id,
            action=action,
            resource=resource,
            allowed=allowed,
        )
