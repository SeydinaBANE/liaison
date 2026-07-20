# Liaison — Vision & Architecture

## Le probleme

Les entreprises ont deja un SI : bases metier (SQL), ERP/CRM exposes en API, GED de
contrats et procedures. Brancher la GenAI dessus se heurte a trois obstacles :

1. **Heterogeneite** — chaque systeme a son protocole, son schema, son authentification.
2. **Gouvernance** — un LLM ne doit jamais lire/ecrire librement dans un SI de production
   (donnees personnelles, integrite, tracabilite).
3. **Confiance** — une reponse sans source n'est pas exploitable en contexte metier.

## La proposition

**Liaison** est un hub qui transforme un SI existant en surface conversationnelle et
agentique **sans le reecrire**. Un orchestrateur multi-agent :

1. **route** la question vers les bons connecteurs (SQL, ERP/CRM, GED) ;
2. **execute** les acces sous une couche de gouvernance (RBAC, masquage PII, allow-list,
   write-back idempotent, audit) ;
3. **synthetise** une reponse en langage naturel, **sourcee** (chaque element cite son
   origine).

Chaque connecteur est aussi expose via **MCP** (Model Context Protocol), standard
d'integration outil/LLM.

## Architecture

```
UI / API (chat REST + SSE)
        |
   Orchestrateur (routage -> execution -> synthese)
        |
  +-----+-----------------+--------------------+
  |                       |                    |
Connecteur SQL     Connecteur API        Connecteur GED
(text-to-SQL       (ERP/CRM REST,        (RAG, retrieval
 gouverne)          write-back idempotent) top-k)
  |                       |                    |
Postgres metier     Mock ERP / SI reel    Qdrant / docs
        \                 |                    /
         +--- Gouvernance : RBAC, PII, audit, idempotence ---+
         +--- Transverse : gateway LLM (fallback), observabilite ---+
```

## Modules (`src/liaison/`) — architecture hexagonale

| Module | Role |
|---|---|
| `domain/routing.py` | `Tool`/`Router` : routage par mots-cles (regle pure) |
| `application/orchestrator.py` | Execution resiliente des outils, synthese sourcee |
| `domain/sql_policy.py` | Couche semantique + `SqlGuard` (regles pures) |
| `application/sql_service.py` | Text-to-SQL gouverne (utilise `ports.sql_executor`) |
| `application/api_service.py` | Appels ERP/CRM, write-back idempotent (utilise `ports.erp_gateway`) |
| `application/docs_service.py` | RAG documentaire (utilise `ports.retriever`) |
| `adapters/outbound/sql/sqlalchemy_executor.py` | Execution SQL lecture seule (SQLAlchemy) |
| `adapters/outbound/erp/http_gateway.py` | Client HTTP vers l'ERP/CRM (httpx) |
| `adapters/outbound/retriever/` | `InMemoryRetriever` (demo) / `QdrantRetriever` (prod) |
| `demo/mock_erp.py` | ERP/CRM de demonstration (FastAPI), hors hexagone |
| `domain/governance.py` | RBAC, `mask_pii`, `IdempotencyGuard`, `AuditLog` |
| `application/llm_gateway.py` | Fallback primaire/secondaire (utilise `ports.llm`) |
| `adapters/outbound/llm/` | `LocalProvider` (demo) / `HttpLLMProvider` (prod) |
| `platform/observability.py` | Spans chronometres + compteurs (abstraction Langfuse/Prometheus) |
| `adapters/inbound/mcp/registry.py` | Registre d'outils au format MCP |
| `services.py` | Composition root (assemblage demo en-process) |
| `adapters/inbound/http/api.py` | Endpoints sante + chat (REST/SSE) sous controle RBAC |

## Principes de conception

- **Le LLM ne touche jamais le SI directement** : il propose, la gouvernance dispose.
- **Tout est injectable** (provider LLM, engine, retriever, client HTTP) → testable
  hors-ligne, sans dependance reseau.
- **Degradation gracieuse** : un connecteur en echec n'interrompt pas la reponse.
- **Sourcage systematique** : chaque reponse porte ses `Evidence`.

Voir [docs/](docs/) pour le detail par couche et [docs/adr/](docs/adr/) pour les decisions.
