from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable, Mapping

from . import action_review_projection as _action_review_projection
from .action_review_projection import _ActionReviewRecordIndex
from .models import (
    ActionExecutionRecord,
    ActionRequestRecord,
    ApprovalDecisionRecord,
    ReconciliationRecord,
)


class ActionReviewInspectionBoundary:
    def __init__(self, service: Any) -> None:
        self._service = service

    def build_record_index(self) -> _ActionReviewRecordIndex:
        return _action_review_projection.build_action_review_record_index(
            self._service
        )

    def chains_for_scope(
        self,
        *,
        case_id: str | None,
        alert_id: str | None,
        record_index: _ActionReviewRecordIndex | None = None,
    ) -> tuple[dict[str, object], ...]:
        return _action_review_projection.action_review_chains_for_scope(
            self._service,
            case_id=case_id,
            alert_id=alert_id,
            record_index=record_index,
        )

    @staticmethod
    def priority(chain: Mapping[str, object]) -> int:
        return _action_review_projection.action_review_priority(chain)

    def build_chain_snapshot(
        self,
        action_request: ActionRequestRecord,
        *,
        record_index: _ActionReviewRecordIndex | None = None,
    ) -> dict[str, object]:
        return _action_review_projection.build_action_review_chain_snapshot(
            self._service,
            action_request,
            record_index=record_index,
        )

    def latest_reconciliation(
        self,
        *,
        action_request: ActionRequestRecord,
        approval_decision: ApprovalDecisionRecord | None,
        action_execution: ActionExecutionRecord | None,
        record_index: _ActionReviewRecordIndex | None = None,
    ) -> ReconciliationRecord | None:
        return _action_review_projection._latest_action_review_reconciliation(
            self._service,
            action_request=action_request,
            approval_decision=approval_decision,
            action_execution=action_execution,
            record_index=record_index,
        )

    def path_health(
        self,
        *,
        action_request: ActionRequestRecord,
        approval_decision: ApprovalDecisionRecord | None,
        action_execution: ActionExecutionRecord | None,
        reconciliation: ReconciliationRecord | None,
        review_state: str,
        as_of: datetime,
    ) -> dict[str, object]:
        return _action_review_projection.action_review_path_health(
            self._service,
            action_request=action_request,
            approval_decision=approval_decision,
            action_execution=action_execution,
            reconciliation=reconciliation,
            review_state=review_state,
            as_of=as_of,
        )

    @staticmethod
    def overall_path_state(paths: Iterable[Mapping[str, str]]) -> str:
        return _action_review_projection._action_review_overall_path_state(paths)

    @staticmethod
    def path_health_summary(
        *,
        overall_state: str,
        paths: Mapping[str, Mapping[str, str]],
    ) -> str:
        return _action_review_projection._action_review_path_health_summary(
            overall_state=overall_state,
            paths=paths,
        )

    def runtime_visibility(
        self,
        *,
        action_request: ActionRequestRecord,
        approval_decision: ApprovalDecisionRecord | None,
        review_state: str,
        record_index: _ActionReviewRecordIndex | None = None,
    ) -> dict[str, object] | None:
        return _action_review_projection.action_review_runtime_visibility(
            self._service,
            action_request=action_request,
            approval_decision=approval_decision,
            review_state=review_state,
            record_index=record_index,
        )

    def visibility_context(
        self,
        action_request: ActionRequestRecord,
    ) -> Mapping[str, object] | None:
        return _action_review_projection._action_review_visibility_context(
            self._service,
            action_request,
        )

    def timeline(
        self,
        *,
        action_request: ActionRequestRecord,
        approval_state: str | None,
        approval_decision: ApprovalDecisionRecord | None,
        action_execution: ActionExecutionRecord | None,
        reconciliation: ReconciliationRecord | None,
    ) -> tuple[dict[str, object], ...]:
        return _action_review_projection.action_review_timeline(
            self._service,
            action_request=action_request,
            approval_state=approval_state,
            approval_decision=approval_decision,
            action_execution=action_execution,
            reconciliation=reconciliation,
        )

    @staticmethod
    def mismatch_inspection(
        reconciliation: ReconciliationRecord | None,
    ) -> dict[str, object] | None:
        return _action_review_projection.action_review_mismatch_inspection(
            reconciliation
        )

    def coordination_ticket_outcome(
        self,
        *,
        action_request: ActionRequestRecord,
        approval_decision: ApprovalDecisionRecord | None,
        action_execution: ActionExecutionRecord | None,
        reconciliation: ReconciliationRecord | None,
        runtime_visibility: Mapping[str, object] | None,
        path_health: Mapping[str, object],
        review_state: str,
    ) -> dict[str, object] | None:
        return _action_review_projection.action_review_coordination_ticket_outcome(
            self._service,
            action_request=action_request,
            approval_decision=approval_decision,
            action_execution=action_execution,
            reconciliation=reconciliation,
            runtime_visibility=runtime_visibility,
            path_health=path_health,
            review_state=review_state,
        )

    @staticmethod
    def downstream_binding(
        action_execution: ActionExecutionRecord | None,
    ) -> Mapping[str, object] | None:
        return _action_review_projection.action_review_downstream_binding(
            action_execution
        )


__all__ = ["ActionReviewInspectionBoundary"]
