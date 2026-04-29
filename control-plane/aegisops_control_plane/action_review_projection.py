from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Iterable, Mapping

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


_AFTER_HOURS_HANDOFF_TRIAGE_DISPOSITIONS = frozenset(
    {
        "business_hours_handoff",
        "awaiting_business_hours_review",
    }
)


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


def _action_review_terminal_non_delegated_path_health() -> dict[str, dict[str, str]]:
    return {
        "ingest": {
            "state": "healthy",
            "reason": "review_closed_before_ingest",
        },
        "delegation": {
            "state": "healthy",
            "reason": "review_closed_without_delegation",
        },
        "provider": {
            "state": "healthy",
            "reason": "review_closed_before_provider",
        },
        "persistence": {
            "state": "healthy",
            "reason": "review_closed_before_reconciliation",
        },
    }


def _action_review_unresolved_without_execution_path_health() -> (
    dict[str, dict[str, str]]
):
    return {
        "ingest": {
            "state": "degraded",
            "reason": "ingest_signal_missing_after_approval",
        },
        "delegation": {
            "state": "degraded",
            "reason": "reviewed_delegation_missing_after_approval",
        },
        "provider": {
            "state": "degraded",
            "reason": "provider_signal_missing_after_approval",
        },
        "persistence": {
            "state": "degraded",
            "reason": "reconciliation_missing_after_approval",
        },
    }


def _action_review_reconciliation_without_execution_path_health(
    *,
    action_request: ActionRequestRecord,
    approval_decision: ApprovalDecisionRecord | None,
    reconciliation: ReconciliationRecord,
    review_state: str,
) -> dict[str, dict[str, str]]:
    delegation_path = _action_review_delegation_path_health(
        action_request=action_request,
        approval_decision=approval_decision,
        action_execution=None,
        review_state=review_state,
    )
    if delegation_path["state"] != "healthy":
        delegation_path = {
            "state": "degraded",
            "reason": "reviewed_delegation_record_missing",
        }
    return {
        "ingest": _action_review_ingest_path_health(reconciliation),
        "delegation": delegation_path,
        "provider": {
            "state": "degraded",
            "reason": "provider_execution_record_missing",
        },
        "persistence": {
            "state": "degraded",
            "reason": "reconciliation_execution_lineage_missing",
        },
    }


def _action_review_visibility_deadline(
    *,
    action_request: ActionRequestRecord,
    approval_decision: ApprovalDecisionRecord | None,
    action_execution: ActionExecutionRecord | None,
) -> datetime | None:
    return min(
        (
            candidate
            for candidate in (
                None if action_execution is None else action_execution.expires_at,
                (
                    None
                    if approval_decision is None
                    else approval_decision.approved_expires_at
                ),
                action_request.expires_at,
            )
            if candidate is not None
        ),
        default=None,
    )


def _action_review_overdue_path_health(
    *,
    review_state: str,
    action_execution: ActionExecutionRecord | None,
    paths: Mapping[str, Mapping[str, str]],
) -> dict[str, dict[str, str]]:
    if action_execution is None:
        if review_state in {"approved", "executing"}:
            return _action_review_unresolved_without_execution_path_health()
        return {path_name: dict(path) for path_name, path in paths.items()}

    overdue_paths = {path_name: dict(path) for path_name, path in paths.items()}
    if overdue_paths["ingest"].get("reason") == "awaiting_ingest_signal":
        overdue_paths["ingest"] = {
            "state": "degraded",
            "reason": "ingest_signal_timeout",
        }
    if overdue_paths["delegation"].get("reason") == "awaiting_receipt":
        overdue_paths["delegation"] = {
            "state": "degraded",
            "reason": "delegation_receipt_timeout",
        }
    if overdue_paths["provider"].get("reason") == "awaiting_provider_receipt":
        overdue_paths["provider"] = {
            "state": "degraded",
            "reason": "provider_receipt_timeout",
        }
    elif overdue_paths["provider"].get("reason") == "awaiting_authoritative_outcome":
        overdue_paths["provider"] = {
            "state": "degraded",
            "reason": "authoritative_outcome_timeout",
        }
    if overdue_paths["persistence"].get("reason") == "awaiting_reconciliation":
        overdue_paths["persistence"] = {
            "state": "degraded",
            "reason": "reconciliation_timeout",
        }
    return overdue_paths


def _action_review_ingest_path_health(
    reconciliation: ReconciliationRecord | None,
) -> dict[str, str]:
    if reconciliation is None:
        return {
            "state": "delayed",
            "reason": "awaiting_ingest_signal",
        }
    return {
        "matched": {
            "state": "healthy",
            "reason": "observations_current",
        },
        "missing": {
            "state": "delayed",
            "reason": "observation_missing",
        },
        "stale": {
            "state": "degraded",
            "reason": "stale_observation",
        },
        "duplicate": {
            "state": "degraded",
            "reason": "duplicate_observations",
        },
        "mismatch": {
            "state": "degraded",
            "reason": "mismatch_detected",
        },
    }.get(
        reconciliation.ingest_disposition,
        {
            "state": "degraded",
            "reason": "ingest_anomaly",
        },
    )


def _action_review_delegation_path_health(
    *,
    action_request: ActionRequestRecord,
    approval_decision: ApprovalDecisionRecord | None,
    action_execution: ActionExecutionRecord | None,
    review_state: str,
) -> dict[str, str]:
    if action_execution is not None:
        if action_execution.lifecycle_state == "dispatching":
            return {
                "state": "delayed",
                "reason": "awaiting_receipt",
            }
        return {
            "state": "healthy",
            "reason": "delegated",
        }
    if approval_decision is not None and approval_decision.lifecycle_state == "approved":
        return {
            "state": "delayed",
            "reason": "awaiting_reviewed_delegation",
        }
    if review_state == "approved" or action_request.lifecycle_state == "approved":
        return {
            "state": "delayed",
            "reason": "awaiting_reviewed_delegation",
        }
    return {
        "state": "delayed",
        "reason": "awaiting_approval",
    }


def _action_review_provider_path_health(
    action_execution: ActionExecutionRecord | None,
) -> dict[str, str]:
    if action_execution is None:
        return {
            "state": "delayed",
            "reason": "awaiting_delegation",
        }
    return {
        "dispatching": {
            "state": "delayed",
            "reason": "awaiting_provider_receipt",
        },
        "queued": {
            "state": "delayed",
            "reason": "awaiting_authoritative_outcome",
        },
        "running": {
            "state": "delayed",
            "reason": "awaiting_authoritative_outcome",
        },
        "succeeded": {
            "state": "healthy",
            "reason": "execution_succeeded",
        },
        "failed": {
            "state": "failed",
            "reason": "execution_failed",
        },
        "canceled": {
            "state": "failed",
            "reason": "execution_canceled",
        },
        "unresolved": {
            "state": "degraded",
            "reason": "execution_unresolved",
        },
        "expired": {
            "state": "failed",
            "reason": "execution_expired",
        },
        "rejected": {
            "state": "failed",
            "reason": "execution_rejected",
        },
        "superseded": {
            "state": "degraded",
            "reason": "execution_superseded",
        },
    }.get(
        action_execution.lifecycle_state,
        {
            "state": "degraded",
            "reason": "provider_anomaly",
        },
    )


def _action_review_persistence_path_health(
    reconciliation: ReconciliationRecord | None,
) -> dict[str, str]:
    if reconciliation is None:
        return {
            "state": "delayed",
            "reason": "awaiting_reconciliation",
        }
    return {
        "matched": {
            "state": "healthy",
            "reason": "reconciliation_matched",
        },
        "pending": {
            "state": "delayed",
            "reason": "reconciliation_pending",
        },
        "mismatched": {
            "state": "degraded",
            "reason": "reconciliation_mismatched",
        },
        "stale": {
            "state": "degraded",
            "reason": "reconciliation_stale",
        },
    }.get(
        reconciliation.lifecycle_state,
        {
            "state": "degraded",
            "reason": "persistence_anomaly",
        },
    )


def _action_review_overall_path_state(
    paths: Iterable[Mapping[str, str]],
) -> str:
    severity = {
        "healthy": 0,
        "delayed": 1,
        "degraded": 2,
        "failed": 3,
    }
    highest = max(
        (
            severity.get(path.get("state", "degraded"), severity["degraded"])
            for path in paths
        ),
        default=severity["healthy"],
    )
    for state, rank in severity.items():
        if rank == highest:
            return state
    return "degraded"


def _action_review_path_health_summary(
    *,
    overall_state: str,
    paths: Mapping[str, Mapping[str, str]],
) -> str:
    active_paths = [
        f"{path_name} {path['reason'].replace('_', ' ')}"
        for path_name, path in paths.items()
        if path.get("state") != "healthy"
    ]
    if not active_paths:
        return "all reviewed execution visibility paths are healthy"
    primary = active_paths[:2]
    joined = "; ".join(primary)
    return f"{overall_state} path visibility: {joined}"


def _action_review_after_hours_handoff_visibility(
    *,
    reviewed_context: Mapping[str, object],
    review_state: str,
) -> dict[str, object] | None:
    if review_state in {"completed", "failed", "canceled"}:
        return None
    handoff = reviewed_context.get("handoff")
    triage = reviewed_context.get("triage")
    triage_disposition = triage.get("disposition") if isinstance(triage, Mapping) else None
    if (
        not isinstance(handoff, Mapping)
        and triage_disposition not in _AFTER_HOURS_HANDOFF_TRIAGE_DISPOSITIONS
    ):
        return None

    visibility: dict[str, object] = {}
    if isinstance(handoff, Mapping):
        for source_key, target_key in (
            ("handoff_at", "handoff_at"),
            ("handoff_owner", "handoff_owner"),
            ("note", "note"),
            ("follow_up_evidence_ids", "follow_up_evidence_ids"),
        ):
            value = handoff.get(source_key)
            if value is not None:
                visibility[target_key] = value
    if (
        isinstance(triage, Mapping)
        and triage_disposition in _AFTER_HOURS_HANDOFF_TRIAGE_DISPOSITIONS
    ):
        for source_key, target_key in (
            ("disposition", "disposition"),
            ("recorded_at", "recorded_at"),
        ):
            value = triage.get(source_key)
            if value is not None:
                visibility[target_key] = value
        rationale = triage.get("closure_rationale")
        if rationale is None:
            rationale = triage.get("rationale")
        if rationale is not None:
            visibility["rationale"] = rationale
    return visibility or None


def _action_review_visibility_context(
    service: AegisOpsControlPlaneService,
    action_request: ActionRequestRecord,
) -> Mapping[str, object] | None:
    case = (
        service._store.get(CaseRecord, action_request.case_id)
        if action_request.case_id is not None
        else None
    )
    alert = (
        service._store.get(AlertRecord, action_request.alert_id)
        if action_request.alert_id is not None
        else None
    )
    if case is not None and isinstance(case.reviewed_context, Mapping):
        return case.reviewed_context
    if alert is not None and isinstance(alert.reviewed_context, Mapping):
        return alert.reviewed_context
    return None


def _action_review_manual_fallback_visibility(
    *,
    reviewed_context: Mapping[str, object],
    action_request: ActionRequestRecord,
    approval_decision: ApprovalDecisionRecord | None,
    review_state: str,
    allow_unscoped_context: bool,
) -> dict[str, object] | None:
    manual_fallback = _action_review_visibility_entry(
        reviewed_context=reviewed_context,
        action_request_id=action_request.action_request_id,
        context_key="manual_fallback",
    )
    if not isinstance(manual_fallback, Mapping):
        return None

    approval_decision_id = (
        approval_decision.approval_decision_id
        if approval_decision is not None
        else action_request.approval_decision_id
    )
    if (
        approval_decision is None
        or approval_decision.lifecycle_state != "approved"
        or review_state in {"pending", "rejected", "expired", "superseded"}
    ):
        return None
    if not _action_review_context_matches_lineage(
        visibility_context=manual_fallback,
        action_request_id=action_request.action_request_id,
        approval_decision_id=approval_decision_id,
        allow_unscoped_context=allow_unscoped_context,
    ):
        return None

    visibility: dict[str, object] = {}
    for source_key in ("action_request_id", "approval_decision_id"):
        value = manual_fallback.get(source_key)
        if value is not None:
            visibility[source_key] = value
    for source_key, target_key in (
        ("fallback_at", "fallback_at"),
        ("performed_at", "fallback_at"),
        ("fallback_actor_identity", "fallback_actor_identity"),
        ("authority_boundary", "authority_boundary"),
        ("reason", "reason"),
        ("action_taken", "action_taken"),
        ("verification_evidence_ids", "verification_evidence_ids"),
        ("residual_uncertainty", "residual_uncertainty"),
    ):
        value = manual_fallback.get(source_key)
        if value is None:
            continue
        if source_key == "performed_at" and target_key in visibility:
            continue
        visibility[target_key] = value
    return visibility


def _action_review_escalation_visibility(
    *,
    reviewed_context: Mapping[str, object],
    action_request: ActionRequestRecord,
    approval_decision: ApprovalDecisionRecord | None,
    review_state: str,
    allow_unscoped_context: bool,
) -> dict[str, object] | None:
    requested_payload = action_request.requested_payload
    escalation_context = _action_review_visibility_entry(
        reviewed_context=reviewed_context,
        action_request_id=action_request.action_request_id,
        context_key="escalation",
    )
    if not isinstance(escalation_context, Mapping):
        return None

    approval_decision_id = (
        approval_decision.approval_decision_id
        if approval_decision is not None
        else action_request.approval_decision_id
    )
    if not _action_review_context_matches_lineage(
        visibility_context=escalation_context,
        action_request_id=action_request.action_request_id,
        approval_decision_id=approval_decision_id,
        allow_unscoped_context=allow_unscoped_context,
    ):
        return None

    recorded_review_state = escalation_context.get("review_state")
    visibility: dict[str, object] = {
        "action_request_id": action_request.action_request_id,
        "approval_decision_id": approval_decision_id,
        "requester_identity": action_request.requester_identity,
        "review_state": (
            recorded_review_state
            if isinstance(recorded_review_state, str) and recorded_review_state.strip()
            else review_state
        ),
    }
    escalation_reason = requested_payload.get("escalation_reason")
    if escalation_reason is not None:
        visibility["escalation_reason"] = escalation_reason
    for source_key, target_key in (
        ("escalated_at", "escalated_at"),
        ("escalated_to", "escalated_to"),
        ("escalated_by_identity", "escalated_by_identity"),
        ("note", "note"),
    ):
        value = escalation_context.get(source_key)
        if value is not None:
            visibility[target_key] = value
    return visibility


def _action_review_context_matches_lineage(
    *,
    visibility_context: Mapping[str, object],
    action_request_id: str,
    approval_decision_id: str | None,
    allow_unscoped_context: bool,
) -> bool:
    scoped_action_request_id = visibility_context.get("action_request_id")
    scoped_approval_decision_id = visibility_context.get("approval_decision_id")

    if scoped_action_request_id is None:
        if scoped_approval_decision_id is not None:
            return (
                approval_decision_id is not None
                and scoped_approval_decision_id == approval_decision_id
            )
        return allow_unscoped_context

    if scoped_action_request_id != action_request_id:
        return False
    if scoped_approval_decision_id is not None:
        return (
            approval_decision_id is not None
            and scoped_approval_decision_id == approval_decision_id
        )
    return True


def _action_review_visibility_entry(
    *,
    reviewed_context: Mapping[str, object],
    action_request_id: str,
    context_key: str,
) -> Mapping[str, object] | None:
    action_review_visibility = reviewed_context.get("action_review_visibility")
    if isinstance(action_review_visibility, Mapping):
        scoped_visibility = action_review_visibility.get(action_request_id)
        if isinstance(scoped_visibility, Mapping):
            scoped_entry = scoped_visibility.get(context_key)
            if isinstance(scoped_entry, Mapping):
                return scoped_entry
    legacy_entry = reviewed_context.get(context_key)
    if isinstance(legacy_entry, Mapping):
        return legacy_entry
    return None


def _action_review_visibility_update(
    *,
    action_request_id: str,
    context_key: str,
    context_value: Mapping[str, object],
) -> dict[str, object]:
    return {
        "action_review_visibility": {
            action_request_id: {
                context_key: dict(context_value),
            }
        }
    }


def _case_has_single_review_bound_action_request(
    service: AegisOpsControlPlaneService,
    case_id: str | None,
    *,
    record_index: _ActionReviewRecordIndex | None = None,
) -> bool:
    if case_id is None:
        return False
    if record_index is not None:
        matching_requests = record_index.requests_by_case_id.get(case_id, ())
    else:
        matching_requests = tuple(
            record
            for record in service._store.list(ActionRequestRecord)
            if record.case_id == case_id
        )
    review_bound_count = sum(
        1
        for record in matching_requests
        if _action_request_is_review_bound(record)
    )
    return review_bound_count == 1


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
        subject_action_execution_ids = service._assistant_ids_from_mapping(
            reconciliation.subject_linkage,
            "action_execution_ids",
        )
        if action_execution.action_execution_id in subject_action_execution_ids:
            return True
        subject_delegation_ids = service._assistant_ids_from_mapping(
            reconciliation.subject_linkage,
            "delegation_ids",
        )
        return action_execution.delegation_id in subject_delegation_ids

    def _matches_review_lineage(reconciliation: ReconciliationRecord) -> bool:
        if _matches_current_execution_lineage(reconciliation):
            return True
        if approval_decision is not None:
            subject_approval_decision_ids = service._assistant_ids_from_mapping(
                reconciliation.subject_linkage,
                "approval_decision_ids",
            )
            if approval_decision.approval_decision_id in subject_approval_decision_ids:
                return True
        subject_action_request_ids = service._assistant_ids_from_mapping(
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


def _action_request_is_review_bound(action_request: ActionRequestRecord) -> bool:
    return not (
        action_request.policy_evaluation.get("approval_requirement")
        == "policy_authorized"
        and action_request.approval_decision_id is None
    )


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


def _action_review_stage_snapshot(
    *,
    stage: str,
    record_family: str,
    record_id: str | None,
    state: str,
    occurred_at: datetime | None,
    actor_identities: tuple[str, ...] = (),
    details: Mapping[str, object] | None = None,
) -> dict[str, object]:
    snapshot = {
        "stage": stage,
        "record_family": record_family,
        "record_id": record_id,
        "state": state,
        "occurred_at": occurred_at,
        "actor_identities": actor_identities,
    }
    if details:
        snapshot["details"] = dict(details)
    return snapshot


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
            paths = _action_review_terminal_non_delegated_path_health()
        elif (
            review_state == "unresolved"
            and approval_decision is not None
            and approval_decision.lifecycle_state == "approved"
        ):
            paths = _action_review_unresolved_without_execution_path_health()
        else:
            paths = {
                "ingest": _action_review_ingest_path_health(reconciliation),
                "delegation": _action_review_delegation_path_health(
                    action_request=action_request,
                    approval_decision=approval_decision,
                    action_execution=action_execution,
                    review_state=review_state,
                ),
                "provider": _action_review_provider_path_health(action_execution),
                "persistence": _action_review_persistence_path_health(reconciliation),
            }
    elif action_execution is None:
        paths = _action_review_reconciliation_without_execution_path_health(
            action_request=action_request,
            approval_decision=approval_decision,
            reconciliation=reconciliation,
            review_state=review_state,
        )
    else:
        paths = {
            "ingest": _action_review_ingest_path_health(reconciliation),
            "delegation": _action_review_delegation_path_health(
                action_request=action_request,
                approval_decision=approval_decision,
                action_execution=action_execution,
                review_state=review_state,
            ),
            "provider": _action_review_provider_path_health(action_execution),
            "persistence": _action_review_persistence_path_health(reconciliation),
        }
    deadline = _action_review_visibility_deadline(
        action_request=action_request,
        approval_decision=approval_decision,
        action_execution=action_execution,
    )
    if deadline is not None and deadline <= as_of:
        paths = _action_review_overdue_path_health(
            review_state=review_state,
            action_execution=action_execution,
            paths=paths,
        )
    overall_state = _action_review_overall_path_state(paths.values())
    return {
        "overall_state": overall_state,
        "summary": _action_review_path_health_summary(
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
    reviewed_context = _action_review_visibility_context(service, action_request)
    if reviewed_context is None:
        return None

    allow_unscoped_action_visibility = _case_has_single_review_bound_action_request(
        service,
        action_request.case_id,
        record_index=record_index,
    )
    visibility: dict[str, object] = {}
    after_hours_handoff = _action_review_after_hours_handoff_visibility(
        reviewed_context=reviewed_context,
        review_state=review_state,
    )
    if after_hours_handoff is not None:
        visibility["after_hours_handoff"] = after_hours_handoff

    manual_fallback = _action_review_manual_fallback_visibility(
        reviewed_context=reviewed_context,
        action_request=action_request,
        approval_decision=approval_decision,
        review_state=review_state,
        allow_unscoped_context=allow_unscoped_action_visibility,
    )
    if manual_fallback is not None:
        visibility["manual_fallback"] = manual_fallback

    escalation_notes = _action_review_escalation_visibility(
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
        _action_review_stage_snapshot(
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
        _action_review_stage_snapshot(
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
        _action_review_stage_snapshot(
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
        _action_review_stage_snapshot(
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
        _action_review_stage_snapshot(
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
