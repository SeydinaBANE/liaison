# Couche 06 — Tests

`tests/`

## Strategie
- **Hors-ligne** : aucun appel reseau. Providers LLM scriptables, SQLite en memoire,
  `TestClient` pour le mock ERP, docs en memoire.
- **Nominal + erreur** pour chaque module (cf. regles projet).
- Nommage `test_<fonction>_<cas>`.

## Fixtures (`conftest.py`)
- `business_engine` : SQLite memoire seede (customers, tickets).
- `make_gateway(reply)` : gateway dont le primaire renvoie une reponse fixe (`ScriptedProvider`).

## Couverture
Seuil CI : **>= 80 %** (`--cov-fail-under=80`). Couverture actuelle ~99 %.

## Commandes
```bash
make test            # pytest + couverture terminal
make test-coverage   # rapport HTML (htmlcov/)
```
