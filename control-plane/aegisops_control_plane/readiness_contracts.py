from __future__ import annotations

from dataclasses import dataclass

from .models import (
    ActionExecutionRecord,
    ReconciliationRecord,
)


@dataclass(frozen=True)
class ReadinessDiagnosticsAggregates:
    alert_total: int
    alert_lifecycle_counts: dict[str, int]
    case_total: int
    open_case_ids: tuple[str, ...]
    action_request_total: int
    action_request_lifecycle_counts: dict[str, int]
    active_action_request_ids: tuple[str, ...]
    terminal_review_outcome_action_request_ids: tuple[str, ...]
    action_execution_total: int
    action_execution_lifecycle_counts: dict[str, int]
    active_action_execution_ids: tuple[str, ...]
    terminal_action_execution_ids: tuple[str, ...]
    reconciliation_total: int
    reconciliation_lifecycle_counts: dict[str, int]
    reconciliation_ingest_disposition_counts: dict[str, int]
    unresolved_reconciliation_ids: tuple[str, ...]
    latest_reconciliation: ReconciliationRecord | None
    phase20_requested_action_requests: int
    phase20_approved_action_requests: int
    phase20_reconciled_executions: int


@dataclass(frozen=True)
class ReadinessReviewPathRecords:
    action_executions: tuple[ActionExecutionRecord, ...]
    reconciliations: tuple[ReconciliationRecord, ...]


__all__ = [
    "ReadinessDiagnosticsAggregates",
    "ReadinessReviewPathRecords",
]
