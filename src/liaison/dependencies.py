"""Dependances FastAPI injectables (surchargeables en tests)."""

from __future__ import annotations

from functools import lru_cache

from liaison.governance import AuditLog, RBACPolicy
from liaison.orchestrator import Orchestrator
from liaison.services import build_orchestrator


@lru_cache(maxsize=1)
def get_orchestrator() -> Orchestrator:
    """Retourne l'orchestrateur applicatif (singleton)."""
    return build_orchestrator()


@lru_cache(maxsize=1)
def get_rbac_policy() -> RBACPolicy:
    """Retourne la politique RBAC (singleton)."""
    return RBACPolicy()


@lru_cache(maxsize=1)
def get_audit_log() -> AuditLog:
    """Retourne le journal d'audit (singleton)."""
    return AuditLog()
