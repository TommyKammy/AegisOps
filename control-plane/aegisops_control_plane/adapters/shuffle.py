from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping


@dataclass(frozen=True)
class ShuffleDelegationReceipt:
    execution_surface_type: str
    execution_surface_id: str
    execution_run_id: str
    adapter: str
    base_url: str


@dataclass(frozen=True)
class ShuffleActionAdapter:
    """Reviewed low-risk action delegation boundary for the standard Shuffle path."""

    base_url: str
    execution_surface_type: str = "automation_substrate"
    execution_surface_id: str = "shuffle"

    def dispatch_approved_action(
        self,
        *,
        delegation_id: str,
        action_request_id: str,
        approval_decision_id: str,
        payload_hash: str,
        idempotency_key: str,
        approved_payload: Mapping[str, object],
        delegated_at: datetime,
    ) -> ShuffleDelegationReceipt:
        del action_request_id
        del approval_decision_id
        del payload_hash
        del idempotency_key
        del approved_payload
        del delegated_at
        return ShuffleDelegationReceipt(
            execution_surface_type=self.execution_surface_type,
            execution_surface_id=self.execution_surface_id,
            execution_run_id=f"shuffle-run-{delegation_id}",
            adapter="shuffle",
            base_url=self.base_url,
        )
