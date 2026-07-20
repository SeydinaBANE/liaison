# Couche 04 — Gateway LLM & Observabilite

`src/liaison/application/llm_gateway.py`, `src/liaison/ports/llm.py`,
`src/liaison/adapters/outbound/llm/{local_provider,http_provider}.py`,
`src/liaison/platform/observability.py`

## Gateway
- `LLMProvider` (Protocol) : contrat minimal `complete(request) -> str`.
- `LocalProvider` : deterministe, hors-ligne (tests et mode local).
- `LLMGateway` : appelle le **primaire**, bascule sur le **fallback** en cas
  d'`LLMProviderError` ; leve si les deux echouent. Compteurs `llm.primary.*`,
  `llm.fallback.*`.
- Production : injecter un provider Bedrock/LiteLLM respectant le meme protocole.

## Observabilite
- `record_span(name, **attrs)` : context manager qui chronometre un bloc et l'enregistre.
- `METRICS` : compteurs + spans en memoire (abstraction Langfuse/Prometheus).
- Production : brancher `record_span` sur Langfuse et `METRICS` sur un exporter Prometheus.

Le decouplage permet de tourner et tester **sans aucune dependance reseau**.
