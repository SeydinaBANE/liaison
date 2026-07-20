# Setup developpement

## Prerequis
- Python **3.12** (`python3.12`)
- Docker + Docker Compose
- `make`

## Installation
```bash
make init          # venv 3.12 + dependances [dev,test] + hooks pre-commit
cp .env.example .env
```

## Boucle de developpement
```bash
. .venv/bin/activate
make lint          # ruff
make typecheck     # mypy strict
make test          # pytest + couverture
make precommit-all # tous les hooks
```

## Lancer l'API en local (sans Docker)
```bash
. .venv/bin/activate
uvicorn liaison.adapters.inbound.http.api:app --reload
# http://localhost:8000/docs
```
L'assemblage par defaut est en-process (SQLite seede + GED memoire) : l'API demarre sans
service externe.

## Note layout `src/`
Le projet utilise un layout `src/`. `pyproject.toml` declare `pythonpath = ["src"]` pour
pytest ; en cas d'ajout de module non detecte, relancer `pip install -e ".[dev,test]"`.
