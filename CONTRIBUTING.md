# Contribuer a Liaison

## Workflow Git

- `main` : branche stable. `develop` : branche d'integration.
- Une feature = une branche `feat/<sujet>` issue de `develop`, **un commit par feature**.
- Messages en [Conventional Commits](https://www.conventionalcommits.org/) :
  `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`, `ci:`.
- PR vers `develop` ; `main` est mis a jour par PR en fin de cycle (POC/MVP).

## Mise en place

```bash
make init        # venv 3.12 + dependances + hooks pre-commit
cp .env.example .env
```

## Avant de pousser

```bash
make lint        # ruff (lint)
make format      # ruff (format)
make typecheck   # mypy strict
make test        # pytest + couverture (>= 80 %)
```

Les hooks `pre-commit` et `pre-push` rejouent ces verifications automatiquement.

## Conventions de code

- Typage strict : tous les parametres et retours annotes ; pas de `Any`.
- Pas de commentaire superflu : le code doit etre auto-documente.
- Une fonction = une responsabilite.
- Gestion d'erreur explicite (exceptions metier dediees).
- Logger structure (`structlog`) — jamais de `print`.
- Tests : au minimum un cas nominal + un cas d'erreur ; services externes mockes ;
  nommage `test_<fonction>_<cas>`.

## Ajouter un connecteur

1. Creer `connectors/<nom>.py` exposant des methodes retournant des `Evidence`.
2. Injecter ses dependances (client, engine) — ne pas les instancier en dur.
3. L'enregistrer comme `Tool` dans `services.build_orchestrator`.
4. Eventuellement l'exposer via `mcp.McpRegistry`.
5. Ajouter ses tests (nominal + erreur) et documenter une couche dans `docs/`.
