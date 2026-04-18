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
    coordination_reference_id: str | None = None
    coordination_target_type: str | None = None
    external_receipt_id: str | None = None
    coordination_target_id: str | None = None
    ticket_reference_url: str | None = None


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
        action_type = approved_payload.get("action_type")
        if action_type == "notify_identity_owner":
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
        if action_type == "create_tracking_ticket":
            self._require_reviewed_phase26_create_tracking_ticket_payload(
                approved_payload
            )
            coordination_target_type = str(approved_payload["coordination_target_type"])
            coordination_target_id = f"{coordination_target_type}-ticket-{delegation_id}"
            return ShuffleDelegationReceipt(
                execution_surface_type=self.execution_surface_type,
                execution_surface_id=self.execution_surface_id,
                execution_run_id=f"shuffle-run-{delegation_id}",
                approval_decision_id=approval_decision_id,
                delegation_id=delegation_id,
                payload_hash=payload_hash,
                adapter="shuffle",
                base_url=self.base_url,
                coordination_reference_id=str(
                    approved_payload["coordination_reference_id"]
                ),
                coordination_target_type=coordination_target_type,
                external_receipt_id=f"shuffle-receipt-{delegation_id}",
                coordination_target_id=coordination_target_id,
                ticket_reference_url=(
                    "https://tickets.example.test/#ticket/"
                    f"{coordination_target_id}"
                ),
            )
        raise ValueError(
            "approved action is outside the reviewed Phase 20 Shuffle delegation scope"
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

    @staticmethod
    def _require_reviewed_phase26_create_tracking_ticket_payload(
        approved_payload: Mapping[str, object],
    ) -> None:
        for field_name in (
            "case_id",
            "coordination_reference_id",
            "coordination_target_type",
            "ticket_title",
            "ticket_description",
        ):
            value = approved_payload.get(field_name)
            if not isinstance(value, str) or value.strip() == "":
                raise ValueError(
                    "approved action is outside the reviewed Phase 26 Shuffle delegation scope"
                )
        if approved_payload["coordination_target_type"] not in {"zammad", "glpi"}:
            raise ValueError(
                "approved action is outside the reviewed Phase 26 Shuffle delegation scope"
            )
