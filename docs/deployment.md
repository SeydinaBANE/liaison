# Deploiement

## Stack locale (Docker Compose)
```bash
cp .env.example .env
make docker-up     # app + postgres (seede) + mock-erp + qdrant
make docker-logs
make docker-down
```
- `app` : API Liaison (8000)
- `postgres` : base metier seedee via `scripts/seed.sql` (5432)
- `mock-erp` : ERP/CRM de demonstration (9000)
- `qdrant` : base vectorielle pour la GED en production (6333)

## Image
Dockerfile **multi-stage**, execution **non-root**, healthcheck sur `/health`.
```bash
make docker-build  # liaison:latest
```

## Vers la production
1. Renseigner les `LIAISON_*` (provider LLM, DSN Postgres reel, URL ERP, cles Langfuse).
2. Remplacer `LocalProvider` par un provider Bedrock/LiteLLM (injection dans `services.py`).
3. Pointer le connecteur GED sur Qdrant (retriever embeddings + reranking).
4. Brancher l'observabilite sur Langfuse + Prometheus.
5. Deployer l'image (Kubernetes / ECS) derriere un reverse-proxy TLS.

## CI/CD
`.github/workflows/ci.yml` : lint -> format -> mypy -> tests (couverture >= 80 %) -> build
image, sur `main` et `develop`.
