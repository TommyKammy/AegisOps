from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping


@dataclass(frozen=True)
class ShuffleDelegationReceipt:
    execution_surface_type: str
    execution_surface_id: str
    execution_run_id: str
    approval_decision_id: str
    delegation_id: str
    payload_hash: str
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
        del idempotency_key
        del delegated_at
        self._require_reviewed_phase20_notify_payload(approved_payload)
        return ShuffleDelegationReceipt(
            execution_surface_type=self.execution_surface_type,
            execution_surface_id=self.execution_surface_id,
            execution_run_id=f"shuffle-run-{delegation_id}",
            approval_decision_id=approval_decision_id,
            delegation_id=delegation_id,
            payload_hash=payload_hash,
            adapter="shuffle",
            base_url=self.base_url,
        )

    @staticmethod
    def _require_reviewed_phase20_notify_payload(
        approved_payload: Mapping[str, object],
    ) -> None:
        action_type = approved_payload.get("action_type")
        if action_type != "notify_identity_owner":
            raise ValueError(
                "approved action is outside the reviewed Phase 20 Shuffle delegation scope"
            )

        for field_name in (
            "recipient_identity",
            "message_intent",
            "escalation_reason",
        ):
            value = approved_payload.get(field_name)
            if not isinstance(value, str) or value.strip() == "":
                raise ValueError(
                    "approved action is outside the reviewed Phase 20 Shuffle delegation scope"
                )
