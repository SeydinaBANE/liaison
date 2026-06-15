# MVP — Integration multi-source (4-6 semaines)

## Objectif
Repondre a une question metier en croisant **plusieurs systemes existants** (base SQL,
ERP/CRM, GED) sous une gouvernance unifiee, avec write-back controle et exposition MCP.

## Perimetre
- Connecteur API ERP/CRM + mock ERP, write-back idempotent.
- Connecteur GED (RAG, retriever abstrait).
- Gouvernance : RBAC, masquage PII, idempotence, audit.
- Orchestration multi-connecteurs resiliente, synthese multi-sources.
- Exposition MCP des connecteurs.
- API chat REST + SSE, CI/CD, Docker Compose.

## Scenario de reference
> « Quel est l'encours du client Acme et y a-t-il un litige ouvert, et que dit le contrat ? »

→ SQL (encours) + API (tickets ouverts) + GED (clause contrat) → reponse synthetisee sourcee.

## Criteres de succes
- Reponse croisant >= 2 sources avec citations.
- Refus RBAC pour un role non autorise ; ecriture idempotente verifiee.
- Couverture >= 80 %, CI verte, stack `docker compose up` operationnelle.

## Resultat
Livre. Voir commits `feat: connecteur API`, `feat: connecteur GED`,
`feat: gouvernance`, `feat: MCP`, `feat: API chat`.
