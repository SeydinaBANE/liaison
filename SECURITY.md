# Securite & RGPD

## Principes

- **Moindre privilege** : RBAC par role (`viewer` lecture seule, `operator` + write_api).
  Toute action verifie une `Permission` avant execution (`governance.RBACPolicy`).
- **Lecture seule par defaut** : le connecteur SQL refuse tout statement non-SELECT et
  toute table hors allow-list (`SqlGuard`). Aucune generation SQL n'est executee sans
  validation.
- **Pas d'ecriture aveugle** : les write-back (ERP/CRM) exigent une cle d'idempotence ;
  rejouer la meme cle ne duplique pas l'effet (`IdempotencyGuard`, mock ERP).
- **Masquage PII** : emails et numeros de telephone sont masques dans les reponses
  (`governance.mask_pii`) avant restitution.
- **Tracabilite** : chaque decision (autorisee ou refusee) est journalisee
  (`governance.AuditLog`) — qui, quelle action, quelle ressource, quand.

## RGPD

- **Minimisation** : seules les colonnes decrites dans la couche semantique sont exposees au
  LLM ; les autres restent invisibles.
- **Pas de stockage de donnees personnelles** par Liaison : il orchestre des acces, il
  n'archive pas les resultats metier.
- **Droit a l'effacement** : Liaison ne possedant pas de copie, l'effacement reste gere par
  les systemes sources.
- **Journal d'audit** : conserve les decisions d'acces, pas les donnees personnelles
  consultees.

## Secrets

- Aucun secret en dur : configuration via variables d'environnement (`LIAISON_*`,
  `pydantic-settings`).
- `detect-secrets` en hook pre-commit (`.secrets.baseline`).
- `.env` ignore par Git ; seul `.env.example` est versionne.

## Signalement

Pour signaler une vulnerabilite, ouvrir une issue privee ou contacter le mainteneur.
