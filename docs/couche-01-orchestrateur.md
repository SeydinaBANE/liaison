# Couche 01 — Orchestrateur

`src/liaison/orchestrator.py`

## Role
Coordonne le cycle **routage → execution → synthese** pour une question metier.

## Composants
- **`Tool`** : connecteur orchestrable (nom, description, mots-cles, `runner` -> `Evidence`,
  `source_kind`).
- **`Router`** : selectionne les outils dont un mot-cle apparait dans la question ; repli
  exhaustif si aucun match.
- **`Orchestrator`** : execute les outils retenus, collecte les `Evidence`, puis appelle le
  gateway pour synthetiser une reponse **sourcee**.

## Resilience
`_run_tool` isole chaque connecteur : un echec produit une `Evidence` degradee
(`<connecteur> indisponible`) au lieu d'interrompre toute la reponse. Compteur
`orchestrator.tool_error`.

## Extension
Le routage regle-base est remplacable par un planificateur LLM (LangGraph) derriere le meme
contrat `Tool` — voir [ADR 0003](adr/0003-routage-regle-base-extensible-llm.md).
