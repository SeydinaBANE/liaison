# Couche 05 — Exposition MCP

`src/liaison/mcp.py`

## Role
Exposer les connecteurs comme outils standard **MCP (Model Context Protocol)**.

## Composants
- `McpTool` : descripteur `name` / `description` / `inputSchema` (+ handler).
  `descriptor()` produit la representation MCP listee par le serveur (sans le handler).
- `McpRegistry` : `register`, `list_tools` (descripteurs), `call_tool` (dispatch ; leve
  `McpToolError` si inconnu).

## Decouplage transport
Le registre est independant du transport MCP (stdio/SSE), qui vient l'envelopper en
production. Ce choix le rend testable hors-ligne.
Voir [ADR 0001](adr/0001-mcp-comme-couche-d-integration.md).
