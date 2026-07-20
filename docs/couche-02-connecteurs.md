# Couche 02 — Connecteurs

`src/liaison/application/{sql_service,api_service,docs_service}.py` (use cases),
`src/liaison/domain/sql_policy.py` (regles SQL), `src/liaison/ports/{sql_executor,erp_gateway,retriever}.py`
(contrats), `src/liaison/adapters/outbound/{sql,erp,retriever}/` (implementations),
`src/liaison/demo/mock_erp.py` (SI tiers simule)

Chaque connecteur retourne une `Evidence` citable (`kind`, `summary`, `payload`).

## SQL — `application/sql_service.py` + `domain/sql_policy.py`
Text-to-SQL gouverne : `SemanticLayer` (tables/colonnes decrites) rendue dans le prompt,
`SqlGuard` (statement unique, lecture seule, allow-list, mots-cles interdits), execution
SQLAlchemy. Le LLM ne touche jamais la base directement.
Voir [ADR 0002](adr/0002-text-to-sql-gouverne.md).

## API — `application/api_service.py` + `demo/mock_erp.py`
Appels REST vers un ERP/CRM (client HTTP injecte) : lecture client/tickets et **write-back
idempotent** (creation de ticket via cle d'idempotence). `mock_erp.py` fournit un SI tiers
realiste pour la demo et les tests.

## GED — `application/docs_service.py`
RAG documentaire : `Retriever` (Protocol) + `InMemoryRetriever` (recouvrement de tokens,
hors-ligne). Production : retriever Qdrant avec embeddings + reranking, meme contrat.

## Principe commun
Toutes les dependances externes (engine, client HTTP, retriever) sont **injectees** → tests
sans reseau (SQLite memoire, `TestClient`, docs en memoire).
