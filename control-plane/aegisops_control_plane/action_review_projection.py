from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Mapping

from .models import (
    ActionExecutionRecord,
    ActionRequestRecord,
    AlertRecord,
    ApprovalDecisionRecord,
    CaseRecord,
    ReconciliationRecord,
)

if TYPE_CHECKING:
    from .service import AegisOpsControlPlaneService


@dataclass(frozen=True)
class _ActionReviewRecordIndex:
    requests_by_case_id: dict[str, tuple[ActionRequestRecord, ...]]
    requests_by_alert_id: dict[str, tuple[ActionRequestRecord, ...]]
    requests_by_scope: dict[tuple[str | None, str | None], tuple[ActionRequestRecord, ...]]
    approvals_by_id: dict[str, ApprovalDecisionRecord]
    approvals_by_action_request_id: dict[str, tuple[ApprovalDecisionRecord, ...]]
    executions_by_action_request_id: dict[str, tuple[ActionExecutionRecord, ...]]
    reconciliations_by_action_request_id: dict[str, tuple[ReconciliationRecord, ...]]
    reconciliations_by_approval_decision_id: dict[str, tuple[ReconciliationRecord, ...]]
    reconciliations_by_action_execution_id: dict[str, tuple[ReconciliationRecord, ...]]
    reconciliations_by_delegation_id: dict[str, tuple[ReconciliationRecord, ...]]

    def matching_requests(
        self,
        *,
        case_id: str | None,
        alert_id: str | None,
    ) -> tuple[ActionRequestRecord, ...]:
        matching_by_id: dict[str, ActionRequestRecord] = {}
        if case_id is not None:
            for record in self.requests_by_case_id.get(case_id, ()):
                matching_by_id[record.action_request_id] = record
        if alert_id is not None:
            for record in self.requests_by_alert_id.get(alert_id, ()):
                matching_by_id[record.action_request_id] = record
        return tuple(matching_by_id.values())

    def scoped_requests(
        self,
        *,
        case_id: str | None,
        alert_id: str | None,
    ) -> tuple[ActionRequestRecord, ...]:
        return self.requests_by_scope.get((case_id, alert_id), ())


def build_action_review_record_index(
    service: AegisOpsControlPlaneService,
) -> _ActionReviewRecordIndex:
    def _freeze_grouped_records(
        grouped_records: defaultdict[object, list[object]],
    ) -> dict[object, tuple[object, ...]]:
        return {
            key: tuple(records)
            for key, records in grouped_records.items()
        }

    action_requests = service._store.list(ActionRequestRecord)
    if not action_requests:
        return _ActionReviewRecordIndex(
            requests_by_case_id={},
            requests_by_alert_id={},
            requests_by_scope={},
            approvals_by_id={},
            approvals_by_action_request_id={},
            executions_by_action_request_id={},
            reconciliations_by_action_request_id={},
            reconciliations_by_approval_decision_id={},
            reconciliations_by_action_execution_id={},
            reconciliations_by_delegation_id={},
        )
    approvals = service._store.list(ApprovalDecisionRecord)
    action_executions = service._store.list(ActionExecutionRecord)
    reconciliations = service._store.list(ReconciliationRecord)

    requests_by_case_id: defaultdict[str, list[ActionRequestRecord]] = defaultdict(list)
    requests_by_alert_id: defaultdict[str, list[ActionRequestRecord]] = defaultdict(list)
    requests_by_scope: defaultdict[
        tuple[str | None, str | None],
        list[ActionRequestRecord],
    ] = defaultdict(list)
    for action_request in action_requests:
        requests_by_scope[
            (action_request.case_id, action_request.alert_id)
        ].append(action_request)
        if action_request.case_id is not None:
            requests_by_case_id[action_request.case_id].append(action_request)
        if action_request.alert_id is not None:
            requests_by_alert_id[action_request.alert_id].append(action_request)

    approvals_by_action_request_id: defaultdict[
        str,
        list[ApprovalDecisionRecord],
    ] = defaultdict(list)
    approvals_by_id = {
        approval.approval_decision_id: approval for approval in approvals
    }
    for approval in approvals:
        approvals_by_action_request_id[approval.action_request_id].append(approval)

    executions_by_action_request_id: defaultdict[
        str,
        list[ActionExecutionRecord],
    ] = defaultdict(list)
    for action_execution in action_executions:
        executions_by_action_request_id[action_execution.action_request_id].append(
            action_execution
        )

    reconciliations_by_action_request_id: defaultdict[
        str,
        list[ReconciliationRecord],
    ] = defaultdict(list)
    reconciliations_by_approval_decision_id: defaultdict[
        str,
        list[ReconciliationRecord],
    ] = defaultdict(list)
    reconciliations_by_action_execution_id: defaultdict[
        str,
        list[ReconciliationRecord],
    ] = defaultdict(list)
    reconciliations_by_delegation_id: defaultdict[
        str,
        list[ReconciliationRecord],
    ] = defaultdict(list)
    for reconciliation in reconciliations:
        for action_request_id in service._assistant_ids_from_mapping(
            reconciliation.subject_linkage,
            "action_request_ids",
        ):
            reconciliations_by_action_request_id[action_request_id].append(
                reconciliation
            )
        for approval_decision_id in service._assistant_ids_from_mapping(
            reconciliation.subject_linkage,
            "approval_decision_ids",
        ):
            reconciliations_by_approval_decision_id[approval_decision_id].append(
                reconciliation
            )
        for action_execution_id in service._assistant_ids_from_mapping(
            reconciliation.subject_linkage,
            "action_execution_ids",
        ):
            reconciliations_by_action_execution_id[action_execution_id].append(
                reconciliation
            )
        for delegation_id in service._assistant_ids_from_mapping(
            reconciliation.subject_linkage,
            "delegation_ids",
        ):
            reconciliations_by_delegation_id[delegation_id].append(reconciliation)

    return _ActionReviewRecordIndex(
        requests_by_case_id=_freeze_grouped_records(requests_by_case_id),
        requests_by_alert_id=_freeze_grouped_records(requests_by_alert_id),
        requests_by_scope=_freeze_grouped_records(requests_by_scope),
        approvals_by_id=approvals_by_id,
        approvals_by_action_request_id=_freeze_grouped_records(
            approvals_by_action_request_id
        ),
        executions_by_action_request_id=_freeze_grouped_records(
            executions_by_action_request_id
        ),
        reconciliations_by_action_request_id=_freeze_grouped_records(
            reconciliations_by_action_request_id
        ),
        reconciliations_by_approval_decision_id=_freeze_grouped_records(
            reconciliations_by_approval_decision_id
        ),
        reconciliations_by_action_execution_id=_freeze_grouped_records(
            reconciliations_by_action_execution_id
        ),
        reconciliations_by_delegation_id=_freeze_grouped_records(
            reconciliations_by_delegation_id
        ),
    )


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
        if service._action_request_is_review_bound(record)
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
    approval_decision = service._action_review_approval_decision(
        action_request,
        record_index=record_index,
    )
    action_execution = service._action_review_execution(
        action_request,
        record_index=record_index,
    )
    reconciliation = service._latest_action_review_reconciliation(
        action_request=action_request,
        approval_decision=approval_decision,
        action_execution=action_execution,
        record_index=record_index,
    )
    approval_state = service._action_review_approval_state(
        action_request=action_request,
        approval_decision=approval_decision,
    )
    review_state = service._action_review_state(
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
    replacement_action_request = service._replacement_action_request(
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
        "next_expected_action": service._next_expected_action_for_review_state(
            review_state
        ),
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


def action_review_path_health(
    service: AegisOpsControlPlaneService,
    *,
    action_request: ActionRequestRecord,
    approval_decision: ApprovalDecisionRecord | None,
    action_execution: ActionExecutionRecord | None,
    reconciliation: ReconciliationRecord | None,
    review_state: str,
    as_of: datetime,
) -> dict[str, object]:
    if action_execution is None and reconciliation is None:
        if review_state in {"rejected", "expired", "superseded", "canceled"}:
            paths = service._action_review_terminal_non_delegated_path_health()
        elif (
            review_state == "unresolved"
            and approval_decision is not None
            and approval_decision.lifecycle_state == "approved"
        ):
            paths = service._action_review_unresolved_without_execution_path_health()
        else:
            paths = {
                "ingest": service._action_review_ingest_path_health(reconciliation),
                "delegation": service._action_review_delegation_path_health(
                    action_request=action_request,
                    approval_decision=approval_decision,
                    action_execution=action_execution,
                    review_state=review_state,
                ),
                "provider": service._action_review_provider_path_health(action_execution),
                "persistence": service._action_review_persistence_path_health(
                    reconciliation
                ),
            }
    elif action_execution is None:
        paths = service._action_review_reconciliation_without_execution_path_health(
            action_request=action_request,
            approval_decision=approval_decision,
            reconciliation=reconciliation,
            review_state=review_state,
        )
    else:
        paths = {
            "ingest": service._action_review_ingest_path_health(reconciliation),
            "delegation": service._action_review_delegation_path_health(
                action_request=action_request,
                approval_decision=approval_decision,
                action_execution=action_execution,
                review_state=review_state,
            ),
            "provider": service._action_review_provider_path_health(action_execution),
            "persistence": service._action_review_persistence_path_health(reconciliation),
        }
    deadline = service._action_review_visibility_deadline(
        action_request=action_request,
        approval_decision=approval_decision,
        action_execution=action_execution,
    )
    if deadline is not None and deadline <= as_of:
        paths = service._action_review_overdue_path_health(
            review_state=review_state,
            action_execution=action_execution,
            paths=paths,
        )
    overall_state = service._action_review_overall_path_state(paths.values())
    return {
        "overall_state": overall_state,
        "summary": service._action_review_path_health_summary(
            overall_state=overall_state,
            paths=paths,
        ),
        "paths": paths,
    }


def action_review_runtime_visibility(
    service: AegisOpsControlPlaneService,
    *,
    action_request: ActionRequestRecord,
    approval_decision: ApprovalDecisionRecord | None,
    review_state: str,
    record_index: _ActionReviewRecordIndex | None = None,
) -> dict[str, object] | None:
    reviewed_context = service._action_review_visibility_context(action_request)
    if reviewed_context is None:
        return None

    allow_unscoped_action_visibility = service._case_has_single_review_bound_action_request(
        action_request.case_id,
        record_index=record_index,
    )
    visibility: dict[str, object] = {}
    after_hours_handoff = service._action_review_after_hours_handoff_visibility(
        reviewed_context=reviewed_context,
        review_state=review_state,
    )
    if after_hours_handoff is not None:
        visibility["after_hours_handoff"] = after_hours_handoff

    manual_fallback = service._action_review_manual_fallback_visibility(
        reviewed_context=reviewed_context,
        action_request=action_request,
        approval_decision=approval_decision,
        review_state=review_state,
        allow_unscoped_context=allow_unscoped_action_visibility,
    )
    if manual_fallback is not None:
        visibility["manual_fallback"] = manual_fallback

    escalation_notes = service._action_review_escalation_visibility(
        reviewed_context=reviewed_context,
        action_request=action_request,
        approval_decision=approval_decision,
        review_state=review_state,
        allow_unscoped_context=allow_unscoped_action_visibility,
    )
    if escalation_notes is not None:
        visibility["escalation_notes"] = escalation_notes

    return visibility or None


def action_review_timeline(
    service: AegisOpsControlPlaneService,
    *,
    action_request: ActionRequestRecord,
    approval_state: str | None,
    approval_decision: ApprovalDecisionRecord | None,
    action_execution: ActionExecutionRecord | None,
    reconciliation: ReconciliationRecord | None,
) -> tuple[dict[str, object], ...]:
    delegation_details: dict[str, object] = {}
    action_execution_details: dict[str, object] = {}
    execution_actor_identities: tuple[str, ...] = ()
    if action_execution is not None:
        delegation_details["delegation_id"] = action_execution.delegation_id
        execution_actor_identities = service._assistant_merge_ids(
            action_execution.provenance.get("initiated_by"),
            action_execution.provenance.get("delegation_issuer"),
        )
        downstream_binding = action_execution.provenance.get("downstream_binding")
        if isinstance(downstream_binding, Mapping):
            delegation_details["downstream_binding"] = dict(downstream_binding)
        adapter = action_execution.provenance.get("adapter")
        if isinstance(adapter, str) and adapter.strip():
            action_execution_details["adapter"] = adapter
        adapter_base_url = action_execution.provenance.get("adapter_base_url")
        if isinstance(adapter_base_url, str) and adapter_base_url.strip():
            action_execution_details["adapter_base_url"] = adapter_base_url
    timeline = (
        service._action_review_stage_snapshot(
            stage="action_request",
            record_family="action_request",
            record_id=action_request.action_request_id,
            state=action_request.lifecycle_state,
            occurred_at=action_request.requested_at,
            actor_identities=(
                ()
                if action_request.requester_identity is None
                else (action_request.requester_identity,)
            ),
            details={
                "recipient_identity": action_request.requested_payload.get(
                    "recipient_identity"
                ),
                "execution_surface_type": action_request.policy_evaluation.get(
                    "execution_surface_type"
                ),
                "execution_surface_id": action_request.policy_evaluation.get(
                    "execution_surface_id"
                ),
            },
        ),
        service._action_review_stage_snapshot(
            stage="approval_decision",
            record_family="approval_decision",
            record_id=(
                None
                if approval_decision is None
                else approval_decision.approval_decision_id
            ),
            state=(
                approval_decision.lifecycle_state
                if approval_decision is not None
                else (approval_state or "pending")
            ),
            occurred_at=(
                None if approval_decision is None else approval_decision.decided_at
            ),
            actor_identities=(
                ()
                if approval_decision is None
                else approval_decision.approver_identities
            ),
            details=(
                {}
                if approval_decision is None
                or approval_decision.decision_rationale is None
                else {
                    "decision_rationale": approval_decision.decision_rationale,
                }
            ),
        ),
        service._action_review_stage_snapshot(
            stage="delegation",
            record_family="action_execution",
            record_id=(
                None
                if action_execution is None
                else action_execution.action_execution_id
            ),
            state=(
                "awaiting_delegation"
                if action_execution is None
                else "delegated"
            ),
            occurred_at=(
                None if action_execution is None else action_execution.delegated_at
            ),
            actor_identities=(
                ()
                if action_execution is None
                else service._assistant_ids_from_mapping(
                    action_execution.provenance,
                    "delegation_issuer",
                )
            ),
            details=delegation_details,
        ),
        service._action_review_stage_snapshot(
            stage="action_execution",
            record_family="action_execution",
            record_id=(
                None
                if action_execution is None
                else action_execution.action_execution_id
            ),
            state=(
                "awaiting_execution"
                if action_execution is None
                else action_execution.lifecycle_state
            ),
            occurred_at=None,
            actor_identities=execution_actor_identities,
            details=(
                {}
                if action_execution is None
                else {
                    "execution_run_id": action_execution.execution_run_id,
                    "execution_surface_type": action_execution.execution_surface_type,
                    "execution_surface_id": action_execution.execution_surface_id,
                    **action_execution_details,
                }
            ),
        ),
        service._action_review_stage_snapshot(
            stage="reconciliation",
            record_family="reconciliation",
            record_id=(
                None if reconciliation is None else reconciliation.reconciliation_id
            ),
            state=(
                "awaiting_reconciliation"
                if reconciliation is None
                else reconciliation.lifecycle_state
            ),
            occurred_at=(
                None if reconciliation is None else reconciliation.compared_at
            ),
            details=(
                {}
                if reconciliation is None
                else {
                    "ingest_disposition": reconciliation.ingest_disposition,
                    "execution_run_id": reconciliation.execution_run_id,
                }
            ),
        ),
    )
    return timeline


def action_review_mismatch_inspection(
    reconciliation: ReconciliationRecord | None,
) -> dict[str, object] | None:
    if reconciliation is None:
        return None
    if reconciliation.lifecycle_state not in {"pending", "mismatched", "stale"}:
        return None
    return {
        "reconciliation_id": reconciliation.reconciliation_id,
        "lifecycle_state": reconciliation.lifecycle_state,
        "ingest_disposition": reconciliation.ingest_disposition,
        "mismatch_summary": reconciliation.mismatch_summary,
        "correlation_key": reconciliation.correlation_key,
        "execution_run_id": reconciliation.execution_run_id,
        "linked_execution_run_ids": reconciliation.linked_execution_run_ids,
        "subject_linkage": dict(reconciliation.subject_linkage),
        "first_seen_at": reconciliation.first_seen_at,
        "last_seen_at": reconciliation.last_seen_at,
        "compared_at": reconciliation.compared_at,
    }


def action_review_reconciliation_detail(
    reconciliation: ReconciliationRecord | None,
) -> dict[str, object]:
    if reconciliation is None:
        return {
            "authority": "aegisops_reconciliation_record",
            "expected_aegisops_state": "matched",
            "authoritative_aegisops_state": "missing",
            "received_receipt": {
                "ingest_disposition": "missing",
                "execution_run_id": None,
                "linked_execution_run_ids": (),
                "correlation_key": None,
                "first_seen_at": None,
                "last_seen_at": None,
            },
            "closeout_evidence": {
                "reconciliation_id": None,
                "compared_at": None,
                "mismatch_summary": (
                    "No authoritative reconciliation record is visible for this "
                    "reviewed request yet."
                ),
            },
            "action_required": True,
            "next_step": "obtain_authoritative_receipt_before_closeout",
        }

    action_required = reconciliation.lifecycle_state != "matched"
    if reconciliation.lifecycle_state == "matched":
        next_step = "record_closeout_evidence"
    elif (
        reconciliation.lifecycle_state == "stale"
        or reconciliation.ingest_disposition == "stale"
    ):
        next_step = "refresh_downstream_receipt_before_closeout"
    elif (
        reconciliation.lifecycle_state == "mismatched"
        or reconciliation.ingest_disposition == "mismatch"
    ):
        next_step = "review_mismatch_before_closeout"
    else:
        next_step = "obtain_authoritative_receipt_before_closeout"

    return {
        "authority": "aegisops_reconciliation_record",
        "expected_aegisops_state": "matched",
        "authoritative_aegisops_state": reconciliation.lifecycle_state,
        "received_receipt": {
            "ingest_disposition": reconciliation.ingest_disposition,
            "execution_run_id": reconciliation.execution_run_id,
            "linked_execution_run_ids": reconciliation.linked_execution_run_ids,
            "correlation_key": reconciliation.correlation_key,
            "first_seen_at": reconciliation.first_seen_at,
            "last_seen_at": reconciliation.last_seen_at,
        },
        "closeout_evidence": {
            "reconciliation_id": reconciliation.reconciliation_id,
            "compared_at": reconciliation.compared_at,
            "mismatch_summary": reconciliation.mismatch_summary,
        },
        "action_required": action_required,
        "next_step": next_step,
    }


def action_review_coordination_ticket_outcome(
    service: AegisOpsControlPlaneService,
    *,
    action_request: ActionRequestRecord,
    approval_decision: ApprovalDecisionRecord | None,
    action_execution: ActionExecutionRecord | None,
    reconciliation: ReconciliationRecord | None,
    runtime_visibility: Mapping[str, object] | None,
    path_health: Mapping[str, object],
    review_state: str,
) -> dict[str, object] | None:
    requested_payload = action_request.requested_payload
    if requested_payload.get("action_type") != "create_tracking_ticket":
        return None
    if (
        action_execution is None
        and reconciliation is None
        and review_state in {"rejected", "expired", "superseded", "canceled"}
    ):
        return None

    downstream_binding = action_review_downstream_binding(action_execution)
    mismatch = action_review_coordination_ticket_mismatch(reconciliation)
    terminal_issue = action_review_coordination_ticket_terminal_issue(
        action_execution=action_execution,
        path_health=path_health,
    )
    manual_fallback = None
    if isinstance(runtime_visibility, Mapping):
        manual_fallback_entry = runtime_visibility.get("manual_fallback")
        if isinstance(manual_fallback_entry, Mapping):
            manual_fallback = dict(manual_fallback_entry)

    if (
        reconciliation is not None
        and reconciliation.lifecycle_state == "matched"
        and action_execution is not None
        and action_execution.lifecycle_state == "succeeded"
    ):
        status = "created"
        summary = (
            "reviewed create-ticket outcome recorded from authoritative "
            "execution and reconciliation"
        )
    elif manual_fallback is not None:
        status = "manual_fallback"
        summary = str(
            manual_fallback.get("action_taken")
            or manual_fallback.get("reason")
            or "reviewed create-ticket outcome recorded as manual fallback"
        )
    elif mismatch is not None:
        status = "mismatch"
        summary = str(mismatch["mismatch_summary"])
    elif terminal_issue is not None and terminal_issue["category"] == "timeout":
        status = "timeout"
        summary = str(terminal_issue["reason"]).replace("_", " ")
    elif terminal_issue is not None:
        status = "failed"
        summary = str(terminal_issue["reason"]).replace("_", " ")
    else:
        status = "pending"
        summary = "reviewed create-ticket outcome still awaiting authoritative result"

    outcome = {
        "authority": "authoritative_aegisops_review",
        "status": status,
        "summary": summary,
        "action_request_id": action_request.action_request_id,
        "approval_decision_id": (
            None if approval_decision is None else approval_decision.approval_decision_id
        ),
        "action_execution_id": (
            None if action_execution is None else action_execution.action_execution_id
        ),
        "execution_run_id": (
            None if action_execution is None else action_execution.execution_run_id
        ),
        "reconciliation_id": (
            None if reconciliation is None else reconciliation.reconciliation_id
        ),
        "coordination_reference_id": (
            action_request.target_scope.get("coordination_reference_id")
            if isinstance(action_request.target_scope.get("coordination_reference_id"), str)
            else requested_payload.get("coordination_reference_id")
        ),
        "coordination_target_type": (
            action_request.target_scope.get("coordination_target_type")
            if isinstance(action_request.target_scope.get("coordination_target_type"), str)
            else requested_payload.get("coordination_target_type")
        ),
        "coordination_target_id": (
            None
            if downstream_binding is None
            else downstream_binding.get("coordination_target_id")
        ),
        "external_receipt_id": (
            None
            if downstream_binding is None
            else downstream_binding.get("external_receipt_id")
        ),
        "ticket_reference_url": (
            None
            if downstream_binding is None
            else downstream_binding.get("ticket_reference_url")
        ),
    }
    if terminal_issue is not None:
        issue_payload = {
            key: value
            for key, value in terminal_issue.items()
            if key != "category"
        }
        if terminal_issue["category"] == "timeout":
            outcome["timeout"] = issue_payload
        else:
            outcome["terminal_issue"] = issue_payload
    if mismatch is not None:
        outcome["mismatch"] = mismatch
    if manual_fallback is not None:
        outcome["manual_fallback"] = manual_fallback
    return outcome


def action_review_downstream_binding(
    action_execution: ActionExecutionRecord | None,
) -> Mapping[str, object] | None:
    if action_execution is None or not isinstance(action_execution.provenance, Mapping):
        return None
    downstream_binding = action_execution.provenance.get("downstream_binding")
    if not isinstance(downstream_binding, Mapping):
        return None
    return downstream_binding


def action_review_coordination_ticket_mismatch(
    reconciliation: ReconciliationRecord | None,
) -> dict[str, object] | None:
    mismatch = action_review_mismatch_inspection(reconciliation)
    if mismatch is None:
        return None
    if (
        mismatch["lifecycle_state"] != "mismatched"
        and mismatch["ingest_disposition"] != "mismatch"
    ):
        return None
    return mismatch


def action_review_coordination_ticket_terminal_issue(
    *,
    action_execution: ActionExecutionRecord | None,
    path_health: Mapping[str, object],
) -> dict[str, object] | None:
    if (
        action_execution is not None
        and isinstance(action_execution.provenance, Mapping)
        and isinstance(action_execution.provenance.get("dispatch_failure"), Mapping)
    ):
        dispatch_failure = action_execution.provenance["dispatch_failure"]
        if dispatch_failure.get("error_type") == "TimeoutError":
            timeout = {
                "category": "timeout",
                "path": "provider",
                "reason": "dispatch_timeout",
            }
            error = dispatch_failure.get("error")
            if isinstance(error, str) and error:
                timeout["error"] = error
            return timeout

    paths = path_health.get("paths")
    if not isinstance(paths, Mapping):
        return None
    timeout_reasons = {
        "ingest_signal_timeout",
        "delegation_receipt_timeout",
        "provider_receipt_timeout",
        "authoritative_outcome_timeout",
        "reconciliation_timeout",
    }
    terminal_failure_reasons = {
        "execution_failed",
        "execution_canceled",
        "execution_expired",
        "execution_rejected",
    }
    provider_path = paths.get("provider")
    if isinstance(provider_path, Mapping):
        provider_reason = provider_path.get("reason")
        if (
            isinstance(provider_reason, str)
            and provider_reason in terminal_failure_reasons
        ):
            return {
                "category": "failed",
                "path": "provider",
                "reason": provider_reason,
            }
    for path_name in ("ingest", "delegation", "provider", "persistence"):
        path = paths.get(path_name)
        if not isinstance(path, Mapping):
            continue
        reason = path.get("reason")
        if not isinstance(reason, str):
            continue
        if reason in timeout_reasons:
            return {
                "category": "timeout",
                "path": path_name,
                "reason": reason,
            }
    return None
