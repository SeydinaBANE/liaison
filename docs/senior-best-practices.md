# Bonnes pratiques (rappel)

Principes appliques dans ce repo.

## Conception
- **Injection de dependances** partout (provider LLM, engine, client HTTP, retriever) →
  testable hors-ligne, substituable en production.
- **Contrats explicites** (`Protocol`, dataclasses frozen) → couplage faible, extensibilite
  (provider Bedrock, retriever Qdrant, planificateur LangGraph) sans toucher l'orchestrateur.
- **Composition root unique** (`services.py`) : l'assemblage est isole du code metier.
- **Degradation gracieuse** : une dependance en echec ne fait pas tomber la requete.

## Code
- Typage strict (mypy `--strict`), aucun `Any`, pas de `type: ignore` non justifie.
- Pas de commentaire superflu ; noms explicites ; une fonction = une responsabilite.
- Logger structure (`structlog`), jamais de `print`.
- Exceptions metier dediees (`SqlGovernanceError`, `AccessDeniedError`, ...).
- Config 12-factor (`pydantic-settings`, prefixe `LIAISON_`), aucun secret en dur.

## Qualite
- `ruff` (lint + format), `mypy --strict`, `pytest` couverture >= 80 %.
- Hooks `pre-commit` + `pre-push` (dont `detect-secrets`).
- CI GitHub Actions reproduisant la chaine complete + build image.

## Git
- `main` stable / `develop` integration ; un commit par feature ; Conventional Commits.
