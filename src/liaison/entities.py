"""Extraction d'entites metier depuis une question en langage naturel.

Resolution simple (identifiant numerique ou nom connu) ; en production cette etape serait
confiee a une extraction LLM ou a une recherche dans le referentiel client.
"""

from __future__ import annotations

import re

_CUSTOMER_ID = re.compile(r"\bclient\s+(\d+)\b|\b(?:id|n[o°])\s*[:#]?\s*(\d+)\b", re.IGNORECASE)


def extract_customer_id(question: str, name_to_id: dict[str, int]) -> int | None:
    """Extrait un identifiant client : numero explicite, sinon nom connu, sinon ``None``."""
    match = _CUSTOMER_ID.search(question)
    if match:
        return int(next(group for group in match.groups() if group))
    lowered = question.lower()
    for name, customer_id in name_to_id.items():
        if name in lowered:
            return customer_id
    return None
