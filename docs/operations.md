# Operations (Run)

## Sante
- `GET /health` → `{ "status": "ok", "version": ... }`. Utilise par le healthcheck Docker.

## Observabilite
- **Spans** (`record_span`) : `llm.primary`, `llm.fallback`, `sql.generate`, `sql.execute`,
  `api.*`, `docs.search`, `orchestrator.*`, `mcp.call_tool`.
- **Compteurs** (`METRICS`) : succes/echecs LLM, acces refuses RBAC, erreurs connecteurs,
  appels MCP.
- En production : exporter vers Langfuse (traces) et Prometheus (compteurs/latence).

## Signaux a surveiller
| Signal | Interpretation |
|---|---|
| `llm.fallback.success` eleve | Provider primaire degrade |
| `orchestrator.tool_error` eleve | Un connecteur/SI en panne |
| `governance.access_denied` eleve | Mauvais role ou tentative d'acces |

## Incidents typiques
- **Reponses degradees** (`<connecteur> indisponible`) : verifier la connectivite du SI
  source (Postgres/ERP) — l'orchestrateur degrade au lieu de planter.
- **403 sur /chat** : role appelant sans permission (voir RBAC).
- **SQL refuse** : requete hors allow-list / non-SELECT — comportement attendu du `SqlGuard`.

## Audit
Le journal (`AuditLog`) trace chaque decision d'acces ; a externaliser vers un stockage
append-only en production.
