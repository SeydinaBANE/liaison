# ADR 0002 — Text-to-SQL gouverne plutot que generation libre

## Statut
Accepte.

## Contexte
Laisser un LLM generer et executer du SQL sur une base de production est dangereux
(injection, ecritures destructrices, exfiltration de colonnes sensibles).

## Decision
Le LLM **propose** une requete a partir d'une **couche semantique** (descriptions de
tables/colonnes autorisees). Un garde-fou (`SqlGuard`) **valide avant execution** :
statement unique, lecture seule par defaut, allow-list de tables, mots-cles de modification
interdits. Seules les requetes conformes sont executees.

## Consequences
- (+) Surface d'attaque reduite ; pas d'execution non validee.
- (+) Minimisation RGPD : seules les colonnes decrites sont exposees.
- (-) Couverture fonctionnelle limitee par la couche semantique (intentionnel).

## Alternatives ecartees
- Generation + execution directe → risque inacceptable en production.
- ORM fige sans NL → perd l'interet conversationnel.
