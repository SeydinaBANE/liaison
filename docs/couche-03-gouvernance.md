# Couche 03 — Gouvernance

`src/liaison/domain/governance.py`

Couche transverse appliquee autour des connecteurs et au niveau de l'API.

| Composant | Role |
|---|---|
| `RBACPolicy` | Permissions par role (`viewer` lecture seule, `operator` + `WRITE_API`). `authorize` leve `AccessDeniedError`. |
| `mask_pii` | Masque emails et numeros de telephone dans les sorties. |
| `IdempotencyGuard` | Detecte le rejeu d'une ecriture par cle. |
| `AuditLog` | Journal append-only : qui, action, ressource, decision, horodatage. |

## Application dans l'API
`POST /chat` : autorise les lectures (`READ_SQL`, `READ_DOCS`) avant orchestration, masque
la PII de la reponse, enregistre l'audit. Un role inconnu -> HTTP 403.

Voir [SECURITY.md](../SECURITY.md) pour la posture securite/RGPD complete.
