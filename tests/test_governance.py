"""Tests de la couche de gouvernance (RBAC, PII, idempotence, audit)."""

from __future__ import annotations

import pytest

from liaison.governance import (
    AccessDeniedError,
    AuditLog,
    IdempotencyGuard,
    Permission,
    Principal,
    RBACPolicy,
    mask_pii,
)

_VIEWER = Principal(user_id="alice", roles=frozenset({"viewer"}))
_OPERATOR = Principal(user_id="bob", roles=frozenset({"operator"}))


def test_viewer_can_read_but_not_write() -> None:
    policy = RBACPolicy()
    policy.authorize(_VIEWER, Permission.READ_SQL)
    with pytest.raises(AccessDeniedError):
        policy.authorize(_VIEWER, Permission.WRITE_API)


def test_operator_can_write() -> None:
    policy = RBACPolicy()
    policy.authorize(_OPERATOR, Permission.WRITE_API)


def test_mask_pii_hides_email_and_phone() -> None:
    masked = mask_pii("contact ops@acme.example ou +33 6 12 34 56 78")
    assert "ops@acme.example" not in masked
    assert "[email]" in masked
    assert "[phone]" in masked


def test_idempotency_guard_detects_replay() -> None:
    guard = IdempotencyGuard()
    assert guard.is_new("k-1") is True
    assert guard.is_new("k-1") is False


def test_audit_log_records_decision() -> None:
    log = AuditLog()
    log.record(_VIEWER, action="read_sql", resource="customers", allowed=True)
    assert len(log.entries) == 1
    assert log.entries[0].user_id == "alice"
    assert log.entries[0].allowed is True
