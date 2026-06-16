"""Tests des endpoints API (sante + chat REST/SSE avec auth)."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from fastapi.testclient import TestClient

from liaison import __version__
from liaison.api import app
from liaison.dependencies import get_orchestrator
from liaison.schemas import AnswerResponse, Evidence, SourceKind

_API_KEY = "dev-key-viewer"
_HEADERS = {"X-API-Key": _API_KEY}


class _FakeOrchestrator:
    async def run(self, question: str) -> AnswerResponse:
        del question
        return AnswerResponse(
            answer="Encours de Acme: 1250 (contact ops@acme.example) [sql]",
            evidence=[Evidence(kind=SourceKind.SQL, summary="encours 1250")],
        )

    async def run_stream(self, question: str) -> AsyncIterator[str]:
        del question
        for word in ["token1", "token2"]:
            yield f"data: {word}\n\n"
        yield "data: [DONE]\n\n"


@pytest.fixture
def client() -> TestClient:
    app.dependency_overrides[get_orchestrator] = _FakeOrchestrator
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": __version__}


def test_chat_returns_answer_with_masked_pii(client: TestClient) -> None:
    response = client.post("/chat", json={"question": "encours Acme ?"}, headers=_HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert "ops@acme.example" not in body["answer"]
    assert "[email]" in body["answer"]
    assert len(body["evidence"]) == 1


def test_chat_denied_for_missing_key(client: TestClient) -> None:
    response = client.post("/chat", json={"question": "encours ?"})
    assert response.status_code == 422


def test_chat_denied_for_invalid_key(client: TestClient) -> None:
    response = client.post(
        "/chat", json={"question": "encours ?"}, headers={"X-API-Key": "invalid"}
    )
    assert response.status_code == 401


def test_chat_stream_emits_sse_events(client: TestClient) -> None:
    response = client.post("/chat/stream", json={"question": "encours ?"}, headers=_HEADERS)
    assert response.status_code == 200
    assert "[DONE]" in response.text
