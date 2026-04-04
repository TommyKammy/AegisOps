from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PostgresControlPlaneStore:
    """Placeholder for the authoritative control-plane persistence adapter."""

    dsn: str
