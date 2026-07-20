"""Masquage des donnees personnelles identifiables (PII)."""

from __future__ import annotations

import re

_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_PHONE = re.compile(r"\b(?:\+?\d[\s.-]?){9,}\d\b")


def mask_pii(text: str) -> str:
    """Masque emails et numeros de telephone dans un texte."""
    masked = _EMAIL.sub("[email]", text)
    return _PHONE.sub("[phone]", masked)
