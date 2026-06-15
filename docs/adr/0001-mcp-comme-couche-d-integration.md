# ADR 0001 — MCP comme couche d'integration des connecteurs

## Statut
Accepte.

## Contexte
Les connecteurs (SQL, API, GED) doivent etre exposables a differents clients LLM et agents
sans recoder l'integration a chaque fois.

## Decision
Exposer chaque connecteur via un registre au format **MCP (Model Context Protocol)** :
descripteurs `name` / `description` / `inputSchema` + dispatch d'appels. Le transport MCP
(stdio/SSE) vient envelopper ce registre.

## Consequences
- (+) Standard reconnu, interoperable avec les agents compatibles MCP.
- (+) Decouplage transport / logique : registre testable hors-ligne.
- (-) Couche d'indirection supplementaire vs appel direct des connecteurs.

## Alternatives ecartees
- SDK proprietaire par client → couplage fort, non reutilisable.
- Tool-calling specifique a un seul fournisseur → enfermement.
