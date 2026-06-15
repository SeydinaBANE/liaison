# Roadmap

## POC (livre) — fondations
- [x] Gateway LLM + fallback + observabilite
- [x] Connecteur SQL text-to-SQL gouverne
- [x] Orchestrateur multi-agent + synthese sourcee
- [x] API chat REST/SSE sous RBAC

## MVP (livre) — integration multi-source
- [x] Connecteur API ERP/CRM + write-back idempotent
- [x] Connecteur GED (RAG)
- [x] Gouvernance complete (RBAC, PII, idempotence, audit)
- [x] Exposition MCP
- [x] CI/CD, Docker Compose, couverture >= 80 %

## Next — industrialisation
- [ ] Provider LLM Bedrock/LiteLLM reel (remplace `LocalProvider`)
- [ ] Retriever Qdrant (embeddings + reranking) en production
- [ ] Planificateur LLM (LangGraph) en remplacement du routage par mots-cles
- [ ] Serveur MCP (transport stdio/SSE) au-dessus du registre
- [ ] Cache semantique + rate limiting (reutilisables depuis GenAI Platform)
- [ ] Branchement Langfuse + exporter Prometheus reels
- [ ] Connecteurs supplementaires (SharePoint/Drive, ServiceNow, SAP)
- [ ] Evaluation continue (RAGAS / LLM-as-judge) de la pertinence
