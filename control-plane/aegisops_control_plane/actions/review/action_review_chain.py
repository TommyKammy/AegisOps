from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Mapping

from .action_review_coordination import action_review_coordination_ticket_outcome
from .action_review_index import (
    _ActionReviewRecordIndex,
    _action_request_is_review_bound,
)
from .action_review_path_health import action_review_path_health
from .action_review_timeline import (
    action_review_mismatch_inspection,
    action_review_reconciliation_detail,
    action_review_timeline,
)
from .action_review_visibility import action_review_runtime_visibility
from ...models import (
    ActionExecutionRecord,
    ActionRequestRecord,
    ApprovalDecisionRecord,
    ReconciliationRecord,
)

if TYPE_CHECKING:
    from ...service import AegisOpsControlPlaneService


def _action_review_approval_decision(
    service: AegisOpsControlPlaneService,
    action_request: ActionRequestRecord,
    *,
    record_index: _ActionReviewRecordIndex | None = None,
) -> ApprovalDecisionRecord | None:
    if record_index is not None and action_request.approval_decision_id:
        decision = record_index.approvals_by_id.get(action_request.approval_decision_id)
        if decision is not None:
            return decision
    if action_request.approval_decision_id:
        decision = service._store.get(
            ApprovalDecisionRecord,
            action_request.approval_decision_id,
        )
        if decision is not None:
            return decision
    if record_index is not None:
        matches = list(
            record_index.approvals_by_action_request_id.get(
                action_request.action_request_id,
                (),
            )
        )
    else:
        matches = [
            record
            for record in service._store.list(ApprovalDecisionRecord)
            if record.action_request_id == action_request.action_request_id
        ]
    if not matches:
        return None
    matches.sort(
        key=lambda record: (
            record.decided_at or datetime.min.replace(tzinfo=timezone.utc),
            record.approval_decision_id,
        ),
        reverse=True,
    )
    return matches[0]


def _action_review_execution(
    service: AegisOpsControlPlaneService,
    action_request: ActionRequestRecord,
    *,
    record_index: _ActionReviewRecordIndex | None = None,
) -> ActionExecutionRecord | None:
    if record_index is not None:
        matches = list(
            record_index.executions_by_action_request_id.get(
                action_request.action_request_id,
                (),
            )
        )
    else:
        matches = [
            record
            for record in service._store.list(ActionExecutionRecord)
            if record.action_request_id == action_request.action_request_id
        ]
    if not matches:
        return None
    matches.sort(
        key=lambda record: (
            record.delegated_at,
            record.action_execution_id,
        ),
        reverse=True,
    )
    return matches[0]


def _latest_action_review_reconciliation(
    service: AegisOpsControlPlaneService,
    *,
    action_request: ActionRequestRecord,
    approval_decision: ApprovalDecisionRecord | None,
    action_execution: ActionExecutionRecord | None,
    record_index: _ActionReviewRecordIndex | None = None,
) -> ReconciliationRecord | None:
    def _dedupe(
        reconciliations: tuple[ReconciliationRecord, ...] | list[ReconciliationRecord],
    ) -> list[ReconciliationRecord]:
        by_id: dict[str, ReconciliationRecord] = {}
        for reconciliation in reconciliations:
            by_id[reconciliation.reconciliation_id] = reconciliation
        return list(by_id.values())

    def _matches_current_execution_lineage(
        reconciliation: ReconciliationRecord,
    ) -> bool:
        if action_execution is None:
            return False
        subject_action_execution_ids = service._ai_trace_lifecycle_service.ids_from_mapping(
            reconciliation.subject_linkage,
            "action_execution_ids",
        )
        if action_execution.action_execution_id in subject_action_execution_ids:
            return True
        subject_delegation_ids = service._ai_trace_lifecycle_service.ids_from_mapping(
            reconciliation.subject_linkage,
            "delegation_ids",
        )
        return action_execution.delegation_id in subject_delegation_ids

    def _matches_review_lineage(reconciliation: ReconciliationRecord) -> bool:
        if _matches_current_execution_lineage(reconciliation):
            return True
        if approval_decision is not None:
            subject_approval_decision_ids = service._ai_trace_lifecycle_service.ids_from_mapping(
                reconciliation.subject_linkage,
                "approval_decision_ids",
            )
            if approval_decision.approval_decision_id in subject_approval_decision_ids:
                return True
        subject_action_request_ids = service._ai_trace_lifecycle_service.ids_from_mapping(
            reconciliation.subject_linkage,
            "action_request_ids",
        )
        return action_request.action_request_id in subject_action_request_ids

    matches: list[ReconciliationRecord] = []
    if record_index is not None:
        indexed_matches: list[ReconciliationRecord] = list(
            record_index.reconciliations_by_action_request_id.get(
                action_request.action_request_id,
                (),
            )
        )
        if approval_decision is not None:
            indexed_matches += list(
                record_index.reconciliations_by_approval_decision_id.get(
                    approval_decision.approval_decision_id,
                    (),
                )
            )
        if action_execution is not None:
            indexed_matches += list(
                record_index.reconciliations_by_action_execution_id.get(
                    action_execution.action_execution_id,
                    (),
                )
            )
            indexed_matches += list(
                record_index.reconciliations_by_delegation_id.get(
                    action_execution.delegation_id,
                    (),
                )
            )
        matches = _dedupe(indexed_matches)
    else:
        for reconciliation in service._store.list(ReconciliationRecord):
            if _matches_review_lineage(reconciliation):
                matches.append(reconciliation)
    if not matches:
        return None
    matches.sort(
        key=lambda record: (
            1 if _matches_current_execution_lineage(record) else 0,
            record.compared_at or record.last_seen_at or record.first_seen_at,
            record.reconciliation_id,
        ),
        reverse=True,
    )
    return matches[0]


def _action_review_approval_state(
    *,
    action_request: ActionRequestRecord,
    approval_decision: ApprovalDecisionRecord | None,
) -> str | None:
    if approval_decision is not None:
        return approval_decision.lifecycle_state
    if action_request.lifecycle_state == "pending_approval":
        return "pending"
    if action_request.lifecycle_state in {"rejected", "expired", "superseded", "canceled"}:
        return action_request.lifecycle_state
    return None


def _action_review_state(
    *,
    action_request: ActionRequestRecord,
    approval_state: str | None,
    action_execution: ActionExecutionRecord | None,
) -> str:
    lifecycle_state = action_request.lifecycle_state
    execution_state = (
        action_execution.lifecycle_state if action_execution is not None else None
    )
    terminal_execution_review_states = {
        "succeeded": "completed",
        "failed": "failed",
        "canceled": "canceled",
        "superseded": "superseded",
        "unresolved": "unresolved",
        "expired": "expired",
        "rejected": "rejected",
    }
    if lifecycle_state in {"expired", "rejected", "superseded", "canceled"}:
        return lifecycle_state
    if lifecycle_state in {"completed", "failed", "unresolved"}:
        return lifecycle_state
    if execution_state in terminal_execution_review_states:
        return terminal_execution_review_states[execution_state]
    if execution_state is not None:
        return "executing"
    if lifecycle_state == "executing":
        return "executing"
    if approval_state in {"expired", "rejected", "superseded", "canceled"}:
        return approval_state
    if approval_state == "approved":
        return "approved"
    if lifecycle_state == "approved":
        return "approved"
    if lifecycle_state == "pending_approval" or approval_state == "pending":
        return "pending"
    return lifecycle_state


def _replacement_action_request(
    service: AegisOpsControlPlaneService,
    action_request: ActionRequestRecord,
    *,
    record_index: _ActionReviewRecordIndex | None = None,
) -> ActionRequestRecord | None:
    if action_request.lifecycle_state != "superseded":
        return None
    requested_payload = dict(action_request.requested_payload)
    recommendation_id = requested_payload.get("recommendation_id")
    action_type = requested_payload.get("action_type")
    if record_index is not None:
        candidate_requests = record_index.matching_requests(
            case_id=action_request.case_id,
            alert_id=action_request.alert_id,
        )
        matches = [
            record
            for record in candidate_requests
            if record.action_request_id != action_request.action_request_id
            and _action_request_is_review_bound(record)
            and record.requested_at >= action_request.requested_at
            and record.lifecycle_state != "superseded"
            and dict(record.requested_payload).get("action_type") == action_type
            and (
                recommendation_id is None
                or dict(record.requested_payload).get("recommendation_id")
                == recommendation_id
            )
        ]
    else:
        matches = [
            record
            for record in service._store.list(ActionRequestRecord)
            if record.action_request_id != action_request.action_request_id
            and _action_request_is_review_bound(record)
            and (
                (
                    action_request.case_id is not None
                    and record.case_id == action_request.case_id
                )
                or (
                    action_request.alert_id is not None
                    and record.alert_id == action_request.alert_id
                )
            )
            and record.requested_at >= action_request.requested_at
            and record.lifecycle_state != "superseded"
            and dict(record.requested_payload).get("action_type") == action_type
            and (
                recommendation_id is None
                or dict(record.requested_payload).get("recommendation_id")
                == recommendation_id
            )
        ]
    if not matches:
        return None
    matches.sort(
        key=lambda record: (record.requested_at, record.action_request_id),
        reverse=True,
    )
    return matches[0]


def _next_expected_action_for_review_state(review_state: str) -> str | None:
    return {
        "pending": "await_approver_decision",
        "approved": "await_reviewed_delegation",
        "executing": "await_execution_reconciliation",
        "expired": "create_replacement_or_close_case",
        "rejected": "review_rejection_and_record_follow_up",
        "canceled": "investigate_execution_cancellation",
        "superseded": "inspect_replacing_review_record",
        "completed": "review_execution_outcome",
        "failed": "investigate_execution_failure",
        "unresolved": "investigate_reconciliation_gap",
    }.get(review_state)


def action_review_chains_for_scope(
    service: AegisOpsControlPlaneService,
    *,
    case_id: str | None,
    alert_id: str | None,
    record_index: _ActionReviewRecordIndex | None = None,
) -> tuple[dict[str, object], ...]:
    if record_index is not None:
        if case_id is not None and alert_id is not None:
            matching_by_id: dict[str, ActionRequestRecord] = {}
            for scoped_request in (
                *record_index.scoped_requests(case_id=case_id, alert_id=alert_id),
                *record_index.scoped_requests(case_id=case_id, alert_id=None),
                *record_index.scoped_requests(case_id=None, alert_id=alert_id),
            ):
                matching_by_id[scoped_request.action_request_id] = scoped_request
            matching_requests = list(matching_by_id.values())
        else:
            matching_requests = list(
                record_index.matching_requests(case_id=case_id, alert_id=alert_id)
            )
    else:
        matching_requests = [
            record
            for record in service._store.list(ActionRequestRecord)
            if (
                (
                    case_id is not None
                    and alert_id is not None
                    and (
                        (
                            record.case_id == case_id
                            and record.alert_id == alert_id
                        )
                        or (
                            record.case_id == case_id
                            and record.alert_id is None
                        )
                        or (
                            record.case_id is None
                            and record.alert_id == alert_id
                        )
                    )
                )
                or (
                    alert_id is None
                    and case_id is not None
                    and record.case_id == case_id
                )
                or (
                    case_id is None
                    and alert_id is not None
                    and record.alert_id == alert_id
                )
            )
        ]
    matching_requests = [
        record
        for record in matching_requests
        if _action_request_is_review_bound(record)
    ]
    chains = [
        build_action_review_chain_snapshot(
            service,
            action_request,
            record_index=record_index,
        )
        for action_request in matching_requests
    ]
    chains.sort(
        key=lambda chain: (
            chain.get("requested_at") or datetime.min.replace(tzinfo=timezone.utc),
            action_review_priority(chain),
            chain.get("action_request_id") or "",
        ),
        reverse=True,
    )
    return tuple(chains)


def action_review_priority(chain: Mapping[str, object]) -> int:
    review_state = chain.get("review_state")
    if review_state == "pending":
        return 5
    if review_state in {"approved", "executing"}:
        return 4
    if review_state in {"expired", "rejected"}:
        return 3
    if review_state == "superseded":
        return 2
    return 1


def build_action_review_chain_snapshot(
    service: AegisOpsControlPlaneService,
    action_request: ActionRequestRecord,
    *,
    record_index: _ActionReviewRecordIndex | None = None,
) -> dict[str, object]:
    approval_decision = _action_review_approval_decision(
        service,
        action_request,
        record_index=record_index,
    )
    action_execution = _action_review_execution(
        service,
        action_request,
        record_index=record_index,
    )
    reconciliation = _latest_action_review_reconciliation(
        service,
        action_request=action_request,
        approval_decision=approval_decision,
        action_execution=action_execution,
        record_index=record_index,
    )
    approval_state = _action_review_approval_state(
        action_request=action_request,
        approval_decision=approval_decision,
    )
    review_state = _action_review_state(
        action_request=action_request,
        approval_state=approval_state,
        action_execution=action_execution,
    )
    timeline = action_review_timeline(
        service,
        action_request=action_request,
        approval_state=approval_state,
        approval_decision=approval_decision,
        action_execution=action_execution,
        reconciliation=reconciliation,
    )
    mismatch_inspection = action_review_mismatch_inspection(reconciliation)
    reconciliation_detail = action_review_reconciliation_detail(reconciliation)
    replacement_action_request = _replacement_action_request(
        service,
        action_request,
        record_index=record_index,
    )
    requested_payload = dict(action_request.requested_payload)
    runtime_visibility = action_review_runtime_visibility(
        service,
        action_request=action_request,
        approval_decision=approval_decision,
        review_state=review_state,
        record_index=record_index,
    )
    path_health_as_of = datetime.now(timezone.utc)
    path_health = action_review_path_health(
        service,
        action_request=action_request,
        approval_decision=approval_decision,
        action_execution=action_execution,
        reconciliation=reconciliation,
        review_state=review_state,
        as_of=path_health_as_of,
    )
    coordination_ticket_outcome = action_review_coordination_ticket_outcome(
        service,
        action_request=action_request,
        approval_decision=approval_decision,
        action_execution=action_execution,
        reconciliation=reconciliation,
        runtime_visibility=runtime_visibility,
        path_health=path_health,
        review_state=review_state,
    )

    return {
        "review_state": review_state,
        "next_expected_action": _next_expected_action_for_review_state(review_state),
        "action_request_id": action_request.action_request_id,
        "action_request_state": action_request.lifecycle_state,
        "approval_decision_id": (
            approval_decision.approval_decision_id if approval_decision is not None else None
        ),
        "approval_state": approval_state,
        "requester_identity": action_request.requester_identity,
        "approver_identities": (
            approval_decision.approver_identities if approval_decision is not None else ()
        ),
        "decision_rationale": (
            approval_decision.decision_rationale
            if approval_decision is not None
            else None
        ),
        "requested_at": action_request.requested_at,
        "expires_at": action_request.expires_at,
        "target_scope": dict(action_request.target_scope),
        "requested_payload": requested_payload,
        "recommendation_id": requested_payload.get("recommendation_id"),
        "recipient_identity": requested_payload.get("recipient_identity"),
        "message_intent": requested_payload.get("message_intent"),
        "escalation_reason": requested_payload.get("escalation_reason"),
        "runtime_visibility": runtime_visibility,
        "path_health": path_health,
        "coordination_ticket_outcome": coordination_ticket_outcome,
        "execution_surface_type": (
            action_execution.execution_surface_type
            if action_execution is not None
            else action_request.policy_evaluation.get("execution_surface_type")
        ),
        "execution_surface_id": (
            action_execution.execution_surface_id
            if action_execution is not None
            else action_request.policy_evaluation.get("execution_surface_id")
        ),
        "timeline": timeline,
        "reconciliation_detail": reconciliation_detail,
        "mismatch_inspection": mismatch_inspection,
        "action_execution_id": (
            action_execution.action_execution_id if action_execution is not None else None
        ),
        "action_execution_state": (
            action_execution.lifecycle_state if action_execution is not None else None
        ),
        "delegation_id": (
            action_execution.delegation_id if action_execution is not None else None
        ),
        "execution_run_id": (
            action_execution.execution_run_id if action_execution is not None else None
        ),
        "reconciliation_id": (
            reconciliation.reconciliation_id if reconciliation is not None else None
        ),
        "reconciliation_state": (
            reconciliation.lifecycle_state if reconciliation is not None else None
        ),
        "replacement_action_request_id": (
            replacement_action_request.action_request_id
            if replacement_action_request is not None
            else None
        ),
        "replacement_approval_decision_id": (
            replacement_action_request.approval_decision_id
            if replacement_action_request is not None
            else None
        ),
    }
