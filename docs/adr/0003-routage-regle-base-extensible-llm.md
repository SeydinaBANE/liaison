# ADR 0003 — Routage regle-base, extensible vers un planificateur LLM

## Statut
Accepte.

## Contexte
L'orchestrateur doit choisir quels connecteurs invoquer pour une question. Un planificateur
LLM (ex. LangGraph) est puissant mais non-deterministe et plus difficile a tester.

## Decision
Demarrer avec un **routage regle-base** (mots-cles par outil, repli exhaustif si aucun
match). Le `Router` et le contrat `Tool` sont concus pour etre remplaces par un
planificateur LLM sans changer l'orchestrateur ni les connecteurs.

## Consequences
- (+) Deterministe, testable, sans cout LLM pour le routage.
- (+) Migration LangGraph isolee derriere le meme contrat.
- (-) Routage moins fin que de la planification semantique (acceptable au MVP).

## Alternatives ecartees
- LangGraph des le POC → complexite et non-determinisme premature.
- Toujours invoquer tous les connecteurs → cout et latence inutiles.
