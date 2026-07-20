"""Dependances FastAPI injectables (surchargeables en tests)."""

from __future__ import annotations

from fastapi import Header, HTTPException

from liaison.application.orchestrator import Orchestrator
from liaison.domain.audit import AuditLog
from liaison.domain.rbac import Principal, RBACPolicy
from liaison.platform.config import get_settings
from liaison.services import build_orchestrator

_orchestrator: Orchestrator | None = None


async def get_orchestrator() -> Orchestrator:
    """Retourne l'orchestrateur applicatif (singleton async)."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = await build_orchestrator()
    return _orchestrator


def get_rbac_policy() -> RBACPolicy:
    """Retourne la politique RBAC (singleton)."""
    return RBACPolicy()


def get_audit_log() -> AuditLog:
    """Retourne le journal d'audit (singleton)."""
    return AuditLog()


def get_principal(
    x_api_key: str = Header(..., description="API key for authentication"),
) -> Principal:
    """Extrait le principal authentifie depuis le header ``X-API-Key``."""
    settings = get_settings()
    role = settings.api_key_mapping.get(x_api_key)
    if role is None:
        raise HTTPException(status_code=401, detail="invalid API key")
    return Principal(user_id=f"key:{x_api_key[:8]}", roles=frozenset({role}))
