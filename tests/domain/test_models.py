"""Tests des DTOs partages (domain/models)."""

from __future__ import annotations

from liaison.domain.models import (
    AnswerResponse,
    Evidence,
    LLMRequest,
    LLMResponse,
    Message,
    Role,
    SourceKind,
)


def test_role_enum_values() -> None:
    assert Role.USER == "user"
    assert Role.ASSISTANT == "assistant"
    assert Role.SYSTEM == "system"


def test_message_roundtrip() -> None:
    msg = Message(role=Role.USER, content="hello")
    assert msg.role == Role.USER
    assert msg.content == "hello"
    data = msg.model_dump()
    assert Message.model_validate(data) == msg


def test_llm_request_defaults() -> None:
    req = LLMRequest(messages=[Message(role=Role.USER, content="q")])
    assert req.max_tokens == 1024
    assert req.temperature == 0.0


def test_llm_request_accepts_empty_messages() -> None:
    req = LLMRequest(messages=[])
    assert req.messages == []


def test_llm_response_used_fallback_default() -> None:
    resp = LLMResponse(content="ok", model="test")
    assert resp.used_fallback is False


def test_source_kind_enum_values() -> None:
    assert SourceKind.SQL == "sql"
    assert SourceKind.API == "api"
    assert SourceKind.DOCS == "docs"


def test_evidence_default_payload() -> None:
    ev = Evidence(kind=SourceKind.SQL, summary="row count")
    assert ev.payload == {}


def test_answer_response_default_evidence() -> None:
    ans = AnswerResponse(answer="42")
    assert ans.evidence == []
    assert ans.used_fallback is False


def test_answer_response_with_evidence() -> None:
    ev = Evidence(kind=SourceKind.API, summary="ticket #1")
    ans = AnswerResponse(answer="done", evidence=[ev], used_fallback=True)
    assert len(ans.evidence) == 1
    assert ans.used_fallback is True
