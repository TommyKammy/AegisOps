from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import logging
from typing import TYPE_CHECKING, Protocol

from .action_policy import evaluate_action_policy_record
from .models import (
    ActionRequestRecord,
    AlertRecord,
    ApprovalDecisionRecord,
    CaseRecord,
)

if TYPE_CHECKING:
    from .service import AegisOpsControlPlaneService


class ActionReviewWriteSurfaceDependencies(Protocol):
    _store: object

    def _require_non_empty_string(self, value: object, field_name: str) -> str:
        ...

    def _require_aware_datetime(self, value: datetime, field_name: str) -> datetime:
        ...

    def _normalize_linked_record_ids(
        self,
        value: object,
        field_name: str,
    ) -> tuple[str, ...]:
        ...

    def _normalize_optional_string(
        self,
        value: object,
        field_name: str,
    ) -> str | None:
        ...

    def _require_review_bound_action_request(
        self,
        action_request_id: str,
    ) -> ActionRequestRecord:
        ...

    def _action_review_approval_decision(
        self,
        action_request: ActionRequestRecord,
    ) -> ApprovalDecisionRecord | None:
        ...

    def _action_review_approval_state(
        self,
        *,
        action_request: ActionRequestRecord,
        approval_decision: ApprovalDecisionRecord | None,
    ) -> str:
        ...

    def _action_review_execution(self, action_request: ActionRequestRecord) -> object:
        ...

    def _action_review_state(
        self,
        *,
        action_request: ActionRequestRecord,
        approval_state: str,
        action_execution: object,
    ) -> str:
        ...

    def _require_action_review_visibility_context_record(
        self,
        action_request: ActionRequestRecord,
    ) -> CaseRecord | AlertRecord:
        ...

    def _validate_case_evidence_linkage(
        self,
        *,
        case: CaseRecord,
        evidence_ids: tuple[str, ...],
        field_name: str,
    ) -> None:
        ...

    def _validate_alert_evidence_linkage(
        self,
        *,
        alert: AlertRecord,
        evidence_ids: tuple[str, ...],
        field_name: str,
    ) -> None:
        ...

    def _persist_action_review_visibility_context_record(
        self,
        *,
        context_record: CaseRecord | AlertRecord,
        reviewed_context_update: dict[str, object],
    ) -> CaseRecord | AlertRecord:
        ...

    def _action_review_visibility_update(
        self,
        *,
        action_request_id: str,
        context_key: str,
        context_value: dict[str, object],
    ) -> dict[str, object]:
        ...

    def _require_reviewed_action_approver_policy(
        self,
        *,
        action_request: ActionRequestRecord,
        approver_identity: str,
    ) -> None:
        ...

    def _resolve_new_record_identifier(
        self,
        record_type: type,
        requested_identifier: str | None,
        field_name: str,
        prefix: str,
    ) -> str:
        ...

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


class ActionReviewWriteSurface:
    def __init__(self, service: ActionReviewWriteSurfaceDependencies) -> None:
        self._service = service

    def record_action_review_manual_fallback(
        self,
        *,
        action_request_id: str,
        fallback_at: datetime,
        fallback_actor_identity: str,
        authority_boundary: str,
        reason: str,
        action_taken: str,
        verification_evidence_ids: tuple[str, ...] = (),
        residual_uncertainty: str | None = None,
    ) -> CaseRecord | AlertRecord:
        service = self._service
        fallback_at = service._require_aware_datetime(fallback_at, "fallback_at")
        fallback_actor_identity = service._require_non_empty_string(
            fallback_actor_identity,
            "fallback_actor_identity",
        )
        authority_boundary = service._require_non_empty_string(
            authority_boundary,
            "authority_boundary",
        )
        reason = service._require_non_empty_string(reason, "reason")
        action_taken = service._require_non_empty_string(action_taken, "action_taken")
        normalized_evidence_ids = service._normalize_linked_record_ids(
            verification_evidence_ids,
            "verification_evidence_ids",
        )
        normalized_residual_uncertainty = service._normalize_optional_string(
            residual_uncertainty,
            "residual_uncertainty",
        )
        with service._store.transaction():
            action_request = service._require_review_bound_action_request(action_request_id)
            approval_decision = service._action_review_approval_decision(action_request)
            approval_state = service._action_review_approval_state(
                action_request=action_request,
                approval_decision=approval_decision,
            )
            review_state = service._action_review_state(
                action_request=action_request,
                approval_state=approval_state,
                action_execution=service._action_review_execution(action_request),
            )
            if (
                approval_decision is None
                or approval_decision.lifecycle_state != "approved"
                or review_state in {"pending", "rejected", "expired", "superseded"}
            ):
                raise ValueError(
                    "manual fallback requires an approved action review in a live post-approval state"
                )
            context_record = service._require_action_review_visibility_context_record(
                action_request
            )
            if isinstance(context_record, CaseRecord):
                service._validate_case_evidence_linkage(
                    case=context_record,
                    evidence_ids=normalized_evidence_ids,
                    field_name="verification_evidence_ids",
                )
            else:
                service._validate_alert_evidence_linkage(
                    alert=context_record,
                    evidence_ids=normalized_evidence_ids,
                    field_name="verification_evidence_ids",
                )
            manual_fallback_context: dict[str, object] = {
                "action_request_id": action_request.action_request_id,
                "approval_decision_id": approval_decision.approval_decision_id,
                "fallback_at": fallback_at.isoformat(),
                "fallback_actor_identity": fallback_actor_identity,
                "authority_boundary": authority_boundary,
                "reason": reason,
                "action_taken": action_taken,
                "verification_evidence_ids": normalized_evidence_ids,
            }
            if normalized_residual_uncertainty is not None:
                manual_fallback_context["residual_uncertainty"] = (
                    normalized_residual_uncertainty
                )
            return service._persist_action_review_visibility_context_record(
                context_record=context_record,
                reviewed_context_update=service._action_review_visibility_update(
                    action_request_id=action_request.action_request_id,
                    context_key="manual_fallback",
                    context_value=manual_fallback_context,
                ),
            )

    def record_action_review_escalation_note(
        self,
        *,
        action_request_id: str,
        escalated_at: datetime,
        escalated_by_identity: str,
        escalated_to: str,
        note: str,
    ) -> CaseRecord | AlertRecord:
        service = self._service
        escalated_at = service._require_aware_datetime(escalated_at, "escalated_at")
        escalated_by_identity = service._require_non_empty_string(
            escalated_by_identity,
            "escalated_by_identity",
        )
        escalated_to = service._require_non_empty_string(
            escalated_to,
            "escalated_to",
        )
        note = service._require_non_empty_string(note, "note")
        with service._store.transaction():
            action_request = service._require_review_bound_action_request(action_request_id)
            approval_decision = service._action_review_approval_decision(action_request)
            approval_state = service._action_review_approval_state(
                action_request=action_request,
                approval_decision=approval_decision,
            )
            review_state = service._action_review_state(
                action_request=action_request,
                approval_state=approval_state,
                action_execution=service._action_review_execution(action_request),
            )
            context_record = service._require_action_review_visibility_context_record(
                action_request
            )
            escalation_context: dict[str, object] = {
                "action_request_id": action_request.action_request_id,
                "escalated_at": escalated_at.isoformat(),
                "escalated_by_identity": escalated_by_identity,
                "escalated_to": escalated_to,
                "note": note,
                "review_state": review_state,
            }
            if approval_decision is not None:
                escalation_context["approval_decision_id"] = (
                    approval_decision.approval_decision_id
                )
            return service._persist_action_review_visibility_context_record(
                context_record=context_record,
                reviewed_context_update=service._action_review_visibility_update(
                    action_request_id=action_request.action_request_id,
                    context_key="escalation",
                    context_value=escalation_context,
                ),
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
        service = self._service
        approver_identity = service._require_non_empty_string(
            approver_identity,
            "approver_identity",
        )
        normalized_decision = service._require_non_empty_string(
            decision,
            "decision",
        ).lower()
        if normalized_decision not in {"grant", "reject"}:
            raise ValueError("decision must be 'grant' or 'reject'")
        decision_rationale = service._require_non_empty_string(
            decision_rationale,
            "decision_rationale",
        )
        decided_at = service._require_aware_datetime(decided_at, "decided_at")
        if authenticated_approver_identity is not None:
            authenticated_approver_identity = service._require_non_empty_string(
                authenticated_approver_identity,
                "authenticated_approver_identity",
            )
            if authenticated_approver_identity != approver_identity:
                raise PermissionError(
                    "authenticated approver identity must match the asserted control-plane approver identity"
                )

        approval_decision: ApprovalDecisionRecord | None = None
        request_expired = False
        with service._store.transaction(isolation_level="SERIALIZABLE"):
            action_request = service._require_review_bound_action_request(action_request_id)
            if action_request.lifecycle_state != "pending_approval":
                raise ValueError(
                    "approval decisions can only be recorded for pending reviewed action requests"
                )
            if action_request.approval_decision_id is not None:
                raise ValueError(
                    f"action request {action_request.action_request_id!r} already has an approval decision"
                )
            if (
                action_request.requester_identity is not None
                and action_request.requester_identity == approver_identity
            ):
                raise PermissionError(
                    "approver identity must be distinct from requester identity"
                )
            if decided_at < action_request.requested_at:
                raise ValueError("decided_at must be on or after requested_at")

            policy_evaluation = evaluate_action_policy_record(
                action_request
            ).policy_evaluation
            if policy_evaluation.get("approval_requirement") == "policy_authorized":
                raise PermissionError(
                    "reviewed approval decisions are not authorized when the re-evaluated action policy is policy_authorized"
                )
            if policy_evaluation.get("approval_requirement") != "human_required":
                raise PermissionError(
                    "reviewed approval decisions require a human-required action policy"
                )
            service._require_reviewed_action_approver_policy(
                action_request=action_request,
                approver_identity=approver_identity,
            )

            now = datetime.now(timezone.utc)
            if action_request.expires_at is not None and (
                now > action_request.expires_at or decided_at > action_request.expires_at
            ):
                service.persist_record(
                    replace(action_request, lifecycle_state="expired"),
                    transitioned_at=action_request.expires_at,
                )
                request_expired = True
            else:
                resolved_approval_decision_id = service._resolve_new_record_identifier(
                    ApprovalDecisionRecord,
                    approval_decision_id,
                    "approval_decision_id",
                    "approval-decision",
                )
                decision_state = (
                    "approved" if normalized_decision == "grant" else "rejected"
                )
                approval_decision = service.persist_record(
                    ApprovalDecisionRecord(
                        approval_decision_id=resolved_approval_decision_id,
                        action_request_id=action_request.action_request_id,
                        approver_identities=(approver_identity,),
                        target_snapshot=dict(action_request.target_scope),
                        payload_hash=action_request.payload_hash,
                        decided_at=decided_at,
                        lifecycle_state=decision_state,
                        decision_rationale=decision_rationale,
                        approved_expires_at=(
                            action_request.expires_at
                            if decision_state == "approved"
                            else None
                        ),
                    ),
                    transitioned_at=decided_at,
                )
                service.persist_record(
                    replace(
                        action_request,
                        approval_decision_id=approval_decision.approval_decision_id,
                        lifecycle_state=decision_state,
                        policy_evaluation=policy_evaluation,
                    ),
                    transitioned_at=decided_at,
                )
        if request_expired:
            raise PermissionError(
                "reviewed action request expired before the approval decision was recorded"
            )
        if approval_decision is None:
            raise RuntimeError(
                "approval decision transaction completed without recording a decision"
            )
        service._emit_structured_event(
            logging.INFO,
            "action_approval_decision_recorded",
            approval_decision_id=approval_decision.approval_decision_id,
            action_request_id=approval_decision.action_request_id,
            decision=normalized_decision,
            approver_identity=approver_identity,
            lifecycle_state=approval_decision.lifecycle_state,
        )
        return approval_decision
