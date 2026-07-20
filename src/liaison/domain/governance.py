"""Couche de gouvernance transverse : RBAC, masquage PII, idempotence et audit.

Barrel de re-export pour compatibilite. Les implementations sont dans :
- ``liaison.domain.rbac``     : RBACPolicy, Principal, Permission, AccessDeniedError
- ``liaison.domain.pii``      : mask_pii
- ``liaison.domain.idempotency`` : IdempotencyGuard
- ``liaison.domain.audit``    : AuditLog, AuditEntry
"""

from __future__ import annotations

from liaison.domain.audit import AuditEntry, AuditLog
from liaison.domain.idempotency import IdempotencyGuard
from liaison.domain.pii import mask_pii
from liaison.domain.rbac import (
    AccessDeniedError,
    Permission,
    Principal,
    RBACPolicy,
)

__all__ = [
    "AccessDeniedError",
    "AuditEntry",
    "AuditLog",
    "IdempotencyGuard",
    "Permission",
    "Principal",
    "RBACPolicy",
    "mask_pii",
]
