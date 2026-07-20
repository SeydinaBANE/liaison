"""Fixtures partagees : base SQLite en memoire seedee et gateway scriptable."""

from __future__ import annotations

import pytest
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.pool import StaticPool

from liaison.application.llm_gateway import LLMGateway
from liaison.domain.models import LLMRequest


class ScriptedProvider:
    """Provider LLM qui renvoie une reponse predefinie (tests deterministes)."""

    def __init__(self, model: str, reply: str) -> None:
        self.model = model
        self._reply = reply

    async def complete(self, request: LLMRequest) -> str:
        del request
        return self._reply

    async def stream(self, request: LLMRequest):  # type: ignore[return]  # noqa
        del request
        for word in self._reply.split():
            yield word


def make_gateway(reply: str) -> LLMGateway:
    """Construit un gateway dont le primaire renvoie toujours ``reply``."""
    provider = ScriptedProvider(model="scripted", reply=reply)
    return LLMGateway(primary=provider, fallback=provider)


@pytest.fixture
def business_engine() -> Engine:
    """Engine SQLite en memoire seede avec un schema metier minimal."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE customers ("
                "id INTEGER PRIMARY KEY, name TEXT, email TEXT, balance REAL)"
            )
        )
        conn.execute(
            text("CREATE TABLE tickets (id INTEGER PRIMARY KEY, customer_id INTEGER, status TEXT)")
        )
        conn.execute(
            text(
                "INSERT INTO customers (id, name, email, balance) VALUES "
                "(1, 'Acme', 'ops@acme.example', 1250.0), "
                "(2, 'Globex', 'hi@globex.example', 0.0)"
            )
        )
        conn.execute(
            text(
                "INSERT INTO tickets (id, customer_id, status) VALUES "
                "(10, 1, 'open'), (11, 1, 'closed')"
            )
        )
    return engine
