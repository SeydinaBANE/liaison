"""Schemas partages entre l'orchestrateur, les connecteurs et l'API."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class Role(StrEnum):
    """Role d'un message dans une conversation."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """Message echange avec le LLM."""

    role: Role
    content: str


class LLMRequest(BaseModel):
    """Requete adressee au gateway LLM."""

    messages: list[Message]
    max_tokens: int = Field(default=1024, ge=1, le=8192)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)


class LLMResponse(BaseModel):
    """Reponse renvoyee par le gateway LLM."""

    content: str
    model: str
    used_fallback: bool = False


class SourceKind(StrEnum):
    """Type de connecteur ayant produit une evidence."""

    SQL = "sql"
    API = "api"
    DOCS = "docs"


class Evidence(BaseModel):
    """Element de preuve retourne par un connecteur, cite dans la reponse."""

    kind: SourceKind
    summary: str
    payload: dict[str, str] = Field(default_factory=dict)


class AnswerResponse(BaseModel):
    """Reponse synthetisee renvoyee a l'utilisateur, avec ses sources."""

    answer: str
    evidence: list[Evidence] = Field(default_factory=list)
    used_fallback: bool = False
