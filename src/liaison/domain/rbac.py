"""Controle d'acces basee sur les roles (RBAC)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


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
            raise AccessDeniedError(f"{principal.user_id} non autorise pour {permission}")
