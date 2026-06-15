# Changelog

Format base sur [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/),
versionnage [SemVer](https://semver.org/lang/fr/).

## [Unreleased]

### Added
- Scaffold projet + outillage senior (ruff, mypy strict, pytest, pre-commit, Docker, CI).
- Gateway LLM avec fallback primaire -> secondaire et observabilite (spans, compteurs).
- Connecteur SQL text-to-SQL gouverne (couche semantique, `SqlGuard`, lecture seule).
- Connecteur API ERP/CRM + mock ERP avec write-back idempotent.
- Connecteur GED (RAG documentaire, retriever abstrait + implementation in-memory).
- Orchestrateur multi-agent (routage par mots-cles, execution resiliente, synthese sourcee).
- Couche gouvernance : RBAC, masquage PII, idempotence, journal d'audit.
- Exposition MCP des connecteurs (registre d'outils + dispatch).
- API chat REST + SSE sous controle RBAC, composition root demo en-process.
- Provider LLM HTTP reel (LiteLLM/OpenAI, frontant Bedrock) avec selection auto et repli local.
- Orchestration croisant 3 sources (SQL + API + GED) avec extraction d'entite (n° client).
- Opt-in Node 24 pour les actions CI (depreciation Node 20).

[Unreleased]: https://github.com/SeydinaBANE/liaison/compare/main...develop
