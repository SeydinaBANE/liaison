# POC — Fondations (1-2 semaines)

## Objectif
Prouver qu'une question metier en langage naturel peut interroger une base existante via un
text-to-SQL **gouverne** et produire une reponse sourcee, sans dependance reseau.

## Perimetre
- Gateway LLM avec fallback (provider abstrait, `LocalProvider` hors-ligne).
- Connecteur SQL : couche semantique, `SqlGuard` (lecture seule, allow-list), execution.
- Orchestrateur minimal (routage + synthese).
- API `/chat` + `/health`, observabilite (spans, compteurs).

## Criteres de succes
- Une question SQL routee, validee, executee, et synthetisee avec citation.
- Refus effectif d'un statement non-SELECT ou hors allow-list.
- `make build` vert (lint + types + tests, couverture >= 80 %).

## Resultat
Livre. Voir commits `feat: gateway`, `feat: connecteur SQL`, `feat: orchestrateur`.
