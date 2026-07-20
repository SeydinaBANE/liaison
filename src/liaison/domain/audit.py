"""Journal d'audit append-only pour tracabilite des decisions."""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass(frozen=True)
class AuditEntry:
    """Entree d'audit immuable."""

    user_id: str
    action: str
    resource: str
    allowed: bool
    timestamp: float


@dataclass
class AuditLog:
    """Journal d'audit append-only en memoire."""

    entries: list[AuditEntry] = field(default_factory=list)

    def record(self, user_id: str, action: str, resource: str, allowed: bool) -> None:
        """Ajoute une entree d'audit."""
        entry = AuditEntry(
            user_id=user_id,
            action=action,
            resource=resource,
            allowed=allowed,
            timestamp=time.time(),
        )
        self.entries.append(entry)
