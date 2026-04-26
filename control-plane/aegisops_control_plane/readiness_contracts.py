from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from typing import Mapping

from .models import (
    ActionExecutionRecord,
    ReconciliationRecord,
)

_READINESS_RUNTIME_STATUSES = frozenset(
    {"ready", "degraded", "stale", "failing_closed"}
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


@dataclass(frozen=True)
class ReadinessRuntimeStatus:
    status: str
    readiness_source: str
    http_status: HTTPStatus
    admits_runtime_traffic: bool

    def to_readyz_payload(
        self,
        *,
        service_name: str,
        persistence_mode: str,
    ) -> dict[str, object]:
        return {
            "service_name": service_name,
            "status": self.status,
            "readiness_source": self.readiness_source,
            "admits_runtime_traffic": self.admits_runtime_traffic,
            "persistence_mode": persistence_mode,
        }


def resolve_current_readiness_runtime_status(
    *,
    startup_ready: bool,
    reconciliation_lifecycle_counts: Mapping[str, int],
    review_path_health_overall_state: str | None = None,
) -> ReadinessRuntimeStatus:
    if not startup_ready:
        status = "failing_closed"
    elif reconciliation_lifecycle_counts.get("stale", 0):
        status = "stale"
    elif reconciliation_lifecycle_counts.get("mismatched", 0):
        status = "degraded"
    elif review_path_health_overall_state in {"degraded", "failed"}:
        status = "degraded"
    else:
        status = "ready"

    admits_runtime_traffic = status == "ready"
    return ReadinessRuntimeStatus(
        status=status,
        readiness_source="current_dependency_status",
        http_status=(
            HTTPStatus.OK
            if admits_runtime_traffic
            else HTTPStatus.SERVICE_UNAVAILABLE
        ),
        admits_runtime_traffic=admits_runtime_traffic,
    )


def resolve_readyz_runtime_status(
    readiness_payload: Mapping[str, object],
) -> ReadinessRuntimeStatus:
    raw_status = readiness_payload.get("status")
    status = (
        raw_status
        if isinstance(raw_status, str) and raw_status in _READINESS_RUNTIME_STATUSES
        else "failing_closed"
    )
    admits_runtime_traffic = status == "ready"
    return ReadinessRuntimeStatus(
        status=status,
        readiness_source="current_dependency_status",
        http_status=(
            HTTPStatus.OK
            if admits_runtime_traffic
            else HTTPStatus.SERVICE_UNAVAILABLE
        ),
        admits_runtime_traffic=admits_runtime_traffic,
    )


__all__ = [
    "ReadinessDiagnosticsAggregates",
    "ReadinessReviewPathRecords",
    "ReadinessRuntimeStatus",
    "resolve_current_readiness_runtime_status",
    "resolve_readyz_runtime_status",
]
