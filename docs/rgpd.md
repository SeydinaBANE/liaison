# RGPD — Note de conformite

Resume oriente conformite ; posture securite complete dans [SECURITY.md](../SECURITY.md).

## Minimisation
Seules les colonnes decrites dans la couche semantique sont exposees au LLM. Les autres
restent invisibles, y compris pour la generation SQL.

## Pas de copie persistante
Liaison **orchestre des acces** ; il ne stocke pas les resultats metier consultes. Les
donnees personnelles restent dans les systemes sources, qui gerent leur cycle de vie
(conservation, effacement, portabilite).

## Masquage
Les donnees personnelles detectables (emails, telephones) sont masquees dans les reponses
restituees (`mask_pii`).

## Tracabilite
Le journal d'audit conserve les **decisions d'acces** (qui, quoi, quand), pas le contenu des
donnees personnelles consultees.

## Responsabilites
- **Liaison** : controle d'acces, minimisation a l'exposition, masquage, audit.
- **Systemes sources** : base legale, conservation, droits des personnes.
