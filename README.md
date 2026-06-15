<p align="center">
  <img src="https://img.shields.io/badge/python-3.12-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/ruff-passing-00cc00?logo=ruff" alt="Ruff">
  <img src="https://img.shields.io/badge/mypy-strict-00cc00?logo=python" alt="Mypy">
  <img src="https://img.shields.io/badge/pre--commit-active-FAB040?logo=pre-commit" alt="Pre-commit">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

<h1 align="center">Liaison</h1>

<p align="center">
  Hub d'integration GenAI pour systemes d'information existants —
  text-to-SQL gouverne, connecteurs ERP/CRM &amp; GED, orchestration multi-agent, MCP.
</p>

---

## A propos

**Liaison** transforme un SI existant en surface conversationnelle et agentique **sans le
reecrire**. Un orchestrateur multi-agent route chaque question metier vers le bon
connecteur — base SQL (text-to-SQL gouverne), ERP/CRM (API REST), GED (RAG) — applique une
couche de gouvernance (RBAC, masquage PII, allow-list, write-back idempotent, audit) et
synthetise une reponse sourcee. Chaque connecteur est aussi expose via **MCP**.

| | |
|---|---|
| **Stack** | Python 3.12, FastAPI, SQLAlchemy, Pydantic, structlog |
| **Coeur** | Orchestrateur multi-agent, gateway LLM (fallback), guardrails |
| **Connecteurs** | SQL (text-to-SQL), API ERP/CRM (OpenAPI), GED (RAG Qdrant), MCP |
| **Gouvernance** | RBAC, masquage PII, allow-list, write-back idempotent, audit log |
| **Infra** | Docker Compose (app + Postgres + mock-ERP + Qdrant), CI GitHub Actions |

## Quick Start

```bash
make init        # venv + dependances + hooks pre-commit
cp .env.example .env
make docker-up   # app + Postgres seede + mock ERP + Qdrant
```

API : http://localhost:8000/docs

## Commandes

```bash
make lint        # ruff
make typecheck   # mypy strict
make test        # pytest + couverture
make build       # lint + typecheck + test
```

## Documentation

| Fichier | Description |
|---|---|
| [PROJET.md](PROJET.md) | Vision, probleme, architecture |
| [docs/](docs/) | Une couche = un document (orchestrateur, connecteurs, gouvernance...) |
| [docs/adr/](docs/adr/) | Decisions d'architecture (ADR) |
| [SECURITY.md](SECURITY.md) | Securite & RGPD |
| [ROADMAP.md](ROADMAP.md) · [POC.md](POC.md) · [MVP.md](MVP.md) | Planning |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Workflow de contribution |

## Licence

MIT — voir [LICENSE](LICENSE).
