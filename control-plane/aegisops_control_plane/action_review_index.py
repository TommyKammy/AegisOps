from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .models import (
    ActionExecutionRecord,
    ActionRequestRecord,
    ApprovalDecisionRecord,
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
        for action_request_id in service._ai_trace_lifecycle_service.ids_from_mapping(
            reconciliation.subject_linkage,
            "action_request_ids",
        ):
            reconciliations_by_action_request_id[action_request_id].append(
                reconciliation
            )
        for approval_decision_id in service._ai_trace_lifecycle_service.ids_from_mapping(
            reconciliation.subject_linkage,
            "approval_decision_ids",
        ):
            reconciliations_by_approval_decision_id[approval_decision_id].append(
                reconciliation
            )
        for action_execution_id in service._ai_trace_lifecycle_service.ids_from_mapping(
            reconciliation.subject_linkage,
            "action_execution_ids",
        ):
            reconciliations_by_action_execution_id[action_execution_id].append(
                reconciliation
            )
        for delegation_id in service._ai_trace_lifecycle_service.ids_from_mapping(
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


def _action_request_is_review_bound(action_request: ActionRequestRecord) -> bool:
    return not (
        action_request.policy_evaluation.get("approval_requirement")
        == "policy_authorized"
        and action_request.approval_decision_id is None
    )
