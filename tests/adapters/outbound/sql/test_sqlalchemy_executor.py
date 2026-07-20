"""Tests de l'adapter d'execution SQL (SQLAlchemy), contre une base SQLite reelle."""

from __future__ import annotations

from sqlalchemy import Engine

from liaison.adapters.outbound.sql.sqlalchemy_executor import SQLAlchemyExecutor


async def test_executor_executes_select(business_engine: Engine) -> None:
    executor = SQLAlchemyExecutor(business_engine)

    rows = await executor.execute("SELECT balance FROM customers WHERE id = 1")

    assert rows == [{"balance": 1250.0}]


async def test_executor_returns_multiple_rows(business_engine: Engine) -> None:
    executor = SQLAlchemyExecutor(business_engine)

    rows = await executor.execute("SELECT id, status FROM tickets ORDER BY id")

    assert [r["status"] for r in rows] == ["open", "closed"]
