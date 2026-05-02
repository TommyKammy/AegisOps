from __future__ import annotations

from datetime import datetime
from typing import Mapping, Protocol

from ..models import (
    ActionExecutionRecord,
    ActionRequestRecord,
    ApprovalDecisionRecord,
    ReconciliationRecord,
)


class ActionReconciliationOrchestrationServiceDependencies(Protocol):
    _action_review_write_surface: object
    _execution_coordinator: object

    def _require_control_plane_change_authority_unfrozen(self) -> None:
        ...


class ActionOrchestrationBoundary:
    """Owns approval-bound action intent and delegation orchestration."""

    def __init__(
        self,
        service: ActionReconciliationOrchestrationServiceDependencies,
    ) -> None:
        self._service = service

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
        self._service._require_control_plane_change_authority_unfrozen()
        return self._service._execution_coordinator.create_reviewed_action_request_from_advisory(
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
        self._service._require_control_plane_change_authority_unfrozen()
        return self._service._execution_coordinator.create_reviewed_tracking_ticket_request_from_advisory(
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

    def record_action_approval_decision(
        self,
        *,
        action_request_id: str,
        approver_identity: str,
        authenticated_approver_identity: str | None = None,
        decision: str,
        decision_rationale: str,
        decided_at: datetime,
        approval_decision_id: str | None = None,
    ) -> ApprovalDecisionRecord:
        self._service._require_control_plane_change_authority_unfrozen()
        return self._service._action_review_write_surface.record_action_approval_decision(
            action_request_id=action_request_id,
            approver_identity=approver_identity,
            authenticated_approver_identity=authenticated_approver_identity,
            decision=decision,
            decision_rationale=decision_rationale,
            decided_at=decided_at,
            approval_decision_id=approval_decision_id,
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
        self._service._require_control_plane_change_authority_unfrozen()
        return self._service._execution_coordinator.delegate_approved_action_to_shuffle(
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
        self._service._require_control_plane_change_authority_unfrozen()
        return self._service._execution_coordinator.delegate_approved_action_to_isolated_executor(
            action_request_id=action_request_id,
            approved_payload=approved_payload,
            delegated_at=delegated_at,
            delegation_issuer=delegation_issuer,
            evidence_ids=evidence_ids,
        )


class ReconciliationOrchestrationBoundary:
    """Owns action-execution reconciliation orchestration."""

    def __init__(
        self,
        service: ActionReconciliationOrchestrationServiceDependencies,
    ) -> None:
        self._service = service

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
        self._service._require_control_plane_change_authority_unfrozen()
        return self._service._execution_coordinator.reconcile_action_execution(
            action_request_id=action_request_id,
            execution_surface_type=execution_surface_type,
            execution_surface_id=execution_surface_id,
            observed_executions=observed_executions,
            compared_at=compared_at,
            stale_after=stale_after,
        )
