from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from typing import Mapping, Protocol

from .models import (
    ActionExecutionRecord,
    ActionRequestRecord,
    ReconciliationRecord,
)

_PHASE26_REVIEWED_COORDINATION_TARGET_TYPES = frozenset(("zammad", "glpi"))


class ExecutionCoordinatorServiceDependencies(Protocol):
    _assistant_advisory_coordinator: object
    _assistant_context_assembler: object
    _store: object
    _shuffle: object
    _isolated_executor: object

    def persist_record(
        self,
        record: object,
        *,
        transitioned_at: datetime | None = None,
    ) -> object:
        ...

    def _emit_structured_event(
        self,
        level: int,
        event: str,
        **fields: object,
    ) -> None:
        ...

    def _emit_action_execution_delegated_event(
        self,
        execution: ActionExecutionRecord,
    ) -> None:
        ...

    def _require_reviewed_case_scoped_advisory_read(
        self,
        context_snapshot: object,
    ) -> None:
        ...

    def _require_reviewed_operator_case(self, case_id: str) -> object:
        ...

    def _resolve_new_record_identifier(
        self,
        record_type: type,
        requested_identifier: str | None,
        field_name: str,
        prefix: str,
    ) -> str:
        ...

    def _require_aware_datetime(self, value: datetime, field_name: str) -> datetime:
        ...

    def _require_non_empty_string(self, value: object, field_name: str) -> str:
        ...

    def _require_mapping(self, value: object, field_name: str) -> dict[str, object]:
        ...

    def _next_identifier(self, prefix: str) -> str:
        ...

    def _merge_linked_ids(
        self,
        existing_values: object,
        incoming_value: str | None,
    ) -> tuple[str, ...]:
        ...


def _approved_payload_binding_hash(
    *,
    target_scope: Mapping[str, object],
    approved_payload: Mapping[str, object],
    execution_surface_type: str,
    execution_surface_id: str,
) -> str:
    binding = _json_ready(
        {
            "approved_payload": approved_payload,
            "execution_surface_id": execution_surface_id,
            "execution_surface_type": execution_surface_type,
            "target_scope": target_scope,
        }
    )
    return hashlib.sha256(
        json.dumps(binding, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _json_ready(value: object) -> object:
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime values used for binding must be timezone-aware")
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value


from .execution_coordinator_action_requests import ReviewedActionRequestCoordinator
from .execution_coordinator_delegation import ApprovedActionDelegationCoordinator
from .execution_coordinator_reconciliation import (
    ActionExecutionReconciliationCoordinator,
)


class ExecutionCoordinator:
    """Owns stable coordination entrypoints over extracted internals."""

    def __init__(self, service: ExecutionCoordinatorServiceDependencies) -> None:
        self._service = service
        self._action_requests = ReviewedActionRequestCoordinator(service)
        self._delegation = ApprovedActionDelegationCoordinator(service)
        self._reconciliation = ActionExecutionReconciliationCoordinator(service)

    def create_reviewed_action_request_from_advisory(
        self,
        *,
        record_family: str,
        record_id: str,
        requester_identity: str,
        recipient_identity: str,
        message_intent: str,
        escalation_reason: str,
        expires_at: datetime,
        action_request_id: str | None = None,
    ) -> ActionRequestRecord:
        return self._action_requests.create_reviewed_action_request_from_advisory(
            record_family=record_family,
            record_id=record_id,
            requester_identity=requester_identity,
            recipient_identity=recipient_identity,
            message_intent=message_intent,
            escalation_reason=escalation_reason,
            expires_at=expires_at,
            action_request_id=action_request_id,
        )

    def create_reviewed_tracking_ticket_request_from_advisory(
        self,
        *,
        record_family: str,
        record_id: str,
        requester_identity: str,
        coordination_reference_id: str,
        coordination_target_type: str,
        ticket_title: str,
        ticket_description: str,
        expires_at: datetime,
        ticket_severity: str = "medium",
        action_request_id: str | None = None,
    ) -> ActionRequestRecord:
        return self._action_requests.create_reviewed_tracking_ticket_request_from_advisory(
            record_family=record_family,
            record_id=record_id,
            requester_identity=requester_identity,
            coordination_reference_id=coordination_reference_id,
            coordination_target_type=coordination_target_type,
            ticket_title=ticket_title,
            ticket_description=ticket_description,
            expires_at=expires_at,
            ticket_severity=ticket_severity,
            action_request_id=action_request_id,
        )

    def delegate_approved_action_to_shuffle(
        self,
        *,
        action_request_id: str,
        approved_payload: Mapping[str, object],
        delegated_at: datetime,
        delegation_issuer: str,
        evidence_ids: tuple[str, ...] = (),
    ) -> ActionExecutionRecord:
        return self._delegation.delegate_approved_action_to_shuffle(
            action_request_id=action_request_id,
            approved_payload=approved_payload,
            delegated_at=delegated_at,
            delegation_issuer=delegation_issuer,
            evidence_ids=evidence_ids,
        )

    def delegate_approved_action_to_isolated_executor(
        self,
        *,
        action_request_id: str,
        approved_payload: Mapping[str, object],
        delegated_at: datetime,
        delegation_issuer: str,
        evidence_ids: tuple[str, ...] = (),
    ) -> ActionExecutionRecord:
        return self._delegation.delegate_approved_action_to_isolated_executor(
            action_request_id=action_request_id,
            approved_payload=approved_payload,
            delegated_at=delegated_at,
            delegation_issuer=delegation_issuer,
            evidence_ids=evidence_ids,
        )

    def reconcile_action_execution(
        self,
        *,
        action_request_id: str,
        execution_surface_type: str,
        execution_surface_id: str,
        observed_executions: tuple[Mapping[str, object], ...],
        compared_at: datetime,
        stale_after: datetime,
    ) -> ReconciliationRecord:
        return self._reconciliation.reconcile_action_execution(
            action_request_id=action_request_id,
            execution_surface_type=execution_surface_type,
            execution_surface_id=execution_surface_id,
            observed_executions=observed_executions,
            compared_at=compared_at,
            stale_after=stale_after,
        )

    @staticmethod
    def _action_execution_lifecycle_from_status(
        status: object,
        current_lifecycle_state: str,
    ) -> str:
        return ActionExecutionReconciliationCoordinator._action_execution_lifecycle_from_status(
            status,
            current_lifecycle_state,
        )
