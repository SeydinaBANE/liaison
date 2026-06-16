# Liaison — agent instructions

Python 3.12+ FastAPI GenAI integration hub (text-to-SQL, ERP/CRM, GED/RAG, MCP).

## Setup & commands

```bash
make init        # .venv + pip install -e ".[dev,test]" + pre-commit hooks
cp .env.example .env
make docker-up   # app + Postgres + mock-ERP + Qdrant
```

Order before push: `make build` (= lint + typecheck + test). CI runs the same plus `ruff format --check` and `pytest --cov-fail-under=80`.

| Command | What |
|---|---|
| `make lint` | `ruff check src/ tests/` |
| `make format` | `ruff format src/ tests/` |
| `make typecheck` | `mypy src/` (strict + pydantic plugin) |
| `make test` | `pytest tests/` (asyncio_mode=auto, auto-coverage) |
| `make security` | `detect-secrets scan` + `pip-audit` |

Run a single test: `pytest tests/test_sql_connector.py -k test_guard_accepts`.

## Architecture

- Package `liaison` under `src/` (setuptools `find` at `src`, so imports are `from liaison.xxx import …`)
- **Entrypoints:** `liaison.api:app` (main FastAPI), `liaison.connectors.mock_erp:app` (mock ERP)
- **Config:** pydantic-settings, `LIAISON_` prefix, loaded from `.env` – see `src/liaison/config.py`
- **Orchestrator** (`orchestrator.py`): keyword-based `Router` → tool execution → LLM synthesis
- **Connectors** (`connectors/`): `sql.py` (governed text-to-SQL), `api.py` (ERP/CRM REST), `docs.py` (RAG over docs), `mock_erp.py` (mock demo ERP)
- **LLM Gateway** (`gateway.py`): primary + fallback `LLMProvider` (uses `HttpLLMProvider` in prod, `LocalProvider` offline)
- **Governance** (`governance.py`): RBAC (viewer/operator), PII masking, idempotency (`IdempotencyGuard`), `AuditLog`
- **Composition root** (`services.py`): `build_orchestrator()` – demo mode uses SQLite in-memory + `InMemoryRetriever`; prod swaps in Postgres + Qdrant
- **Middlewares** (`middleware.py`): rate limiting (sliding window par IP), correlation ID tracing

## API auth

- Tous les endpoints `/chat` et `/chat/stream` nécessitent un header `X-API-Key`
- Les clés sont configurées dans `LIAISON_API_KEYS` (format `key:role,key:role`)
- Rôles disponibles : `viewer` (lecture seule), `operator` (lecture + écriture)
- Le header manquant → `422`, clé invalide → `401`, permissions insuffisantes → `403`
- Le endpoint `/health` est public
- Rate limiting : `LIAISON_RATE_LIMIT_MAX_REQUESTS` requêtes par fenêtre de `LIAISON_RATE_LIMIT_WINDOW_SEC` secondes

## Production wiring

- Si `LIAISON_SQL_DSN` pointe vers du Postgres (pas localhost par défaut), l'engine est créé avec pool_size=5, max_overflow=10, pool_pre_ping=True
- Si `LIAISON_QDRANT_URL` est renseigné, le connecteur GED utilise Qdrant au lieu de l'InMemoryRetriever de démo
- Graceful shutdown via lifespan : fermeture des clients HTTP et disposal des engines SQL

## Testing conventions

- **No external services needed** – tests use SQLite in-memory (`business_engine` fixture in `conftest.py`) and `ScriptedProvider` (deterministic LLM replies)
- LLM gateway is tested via `make_gateway(reply)` helper which returns the given string verbatim
- Use `pytest -m integration` for tests that need the Docker stack (marker defined in `pyproject.toml`)
- `httpx.MockTransport` can be injected to test `HttpLLMProvider` and `ApiConnector` without network

## Style

- Ruff line-length 100, target py312, no `Any`/`dict`/`list` without concrete types
- Python 3.12 syntax (`Annotated`, `frozenset`, `StrEnum`, `Protocol`)
- structlog JSON logging (use `get_logger(__name__)`), no `print`
- No comments in code – code must be self-documenting
- `pre-commit` hooks run on every commit: ruff lint/format, mypy, detect-secrets
