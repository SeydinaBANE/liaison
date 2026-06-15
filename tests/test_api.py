"""Tests des endpoints API (sante + chat REST/SSE avec RBAC)."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from liaison import __version__
from liaison.api import app
from liaison.dependencies import get_orchestrator
from liaison.schemas import AnswerResponse, Evidence, SourceKind


class _FakeOrchestrator:
    def run(self, question: str) -> AnswerResponse:
        del question
        return AnswerResponse(
            answer="Encours de Acme: 1250 (contact ops@acme.example) [sql]",
            evidence=[Evidence(kind=SourceKind.SQL, summary="encours 1250")],
        )


@pytest.fixture
def client() -> Iterator[TestClient]:
    app.dependency_overrides[get_orchestrator] = _FakeOrchestrator
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": __version__}


def test_chat_returns_answer_with_masked_pii(client: TestClient) -> None:
    response = client.post("/chat", json={"question": "encours Acme ?", "role": "viewer"})
    assert response.status_code == 200
    body = response.json()
    assert "ops@acme.example" not in body["answer"]
    assert "[email]" in body["answer"]
    assert len(body["evidence"]) == 1


def test_chat_denied_for_unknown_role(client: TestClient) -> None:
    response = client.post("/chat", json={"question": "encours ?", "role": "anonymous"})
    assert response.status_code == 403


def test_chat_stream_emits_sse_events(client: TestClient) -> None:
    response = client.post("/chat/stream", json={"question": "encours ?", "role": "viewer"})
    assert response.status_code == 200
    assert "[DONE]" in response.text
