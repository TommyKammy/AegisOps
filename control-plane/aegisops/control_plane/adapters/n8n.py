from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class N8NReconciliationAdapter:
    """Placeholder for reconciling control-plane intent with workflow outcomes."""

    base_url: str
