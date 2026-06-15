"""Tests du point d'entree API."""

from __future__ import annotations

from fastapi.testclient import TestClient

from liaison import __version__
from liaison.api import app

client = TestClient(app)


def test_health_returns_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": __version__}


def test_health_only_accepts_get() -> None:
    response = client.post("/health")
    assert response.status_code == 405
